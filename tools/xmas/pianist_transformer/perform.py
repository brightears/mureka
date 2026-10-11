#!/usr/bin/env python
"""Render a score MIDI into an expressive performance MIDI with Pianist Transformer.

Usage:
    .venv/bin/python perform.py input_score.mid output_performance.mid [options]

Model: yhj137/pianist-transformer-rendering (Apache-2.0), weights in ./models/sft
Code:  https://github.com/yhj137/PianistTransformer (cloned in ./repo)

INPUT
  * Any MIDI. All non-drum tracks are merged into one piano part (drum tracks are
    ignored). The tempo map is honoured: notes are converted to absolute
    milliseconds, so the score tempo matters (the model sees real-time IOIs).
  * The model was fine-tuned on ASAP score MIDIs: quantized, constant velocity 80,
    no pedal. By default this wrapper normalizes the input to that form
    (velocity -> 80, CC64 removed). Use --keep-input-dynamics to feed velocities
    and pedal through unchanged (out of training distribution).
  * Pitch is forced token-by-token, so every input note appears exactly once in
    the output (same pitch, same order). Overlapping repeats of the same pitch are
    trimmed; a repeat that starts on the same tick as another is dropped.
  * Limits of the token vocabulary: inter-onset gaps are capped at 4.99 s and note
    durations at 5.0 s (in real time at the score tempo). Longer rests get shortened.
  * Long pieces are processed in sliding windows of 512 notes (4096 tokens), 50%
    overlap. No hard length limit.

OUTPUT (primary file)
  * "raw" performance: one track, ticks_per_beat=500 at a fixed 120 BPM, so
    1 tick = 1 ms. Notes sit at absolute performed times. CC64 sustain values
    (0-127, four pedal samples per note) are included. No time signature.

  --fit-duration rescales the raw timing linearly so the last onset lands where the
    score's does. Takes vary a lot in overall tempo (seen: -11% to +43% length on
    Silent Night), so use this for a fair A/B against rule-based humanization.

  --editable PATH additionally writes the "Expressive Tempo Mapping" version
    (the repo's map_midi): notes stay on the score's beat grid (500 ticks/beat),
    timing is expressed as a dense tempo map (clipped to --max-tempo, min 10 BPM),
    with performed velocities, durations and CC64. Time signatures are kept.
"""

import argparse
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "repo")
MODEL_DIR = os.path.join(HERE, "models", "sft")
os.environ.setdefault("HF_HOME", os.path.join(HERE, "hf_home"))
sys.path.insert(0, REPO)

import torch  # noqa: E402
from miditoolkit import MidiFile  # noqa: E402

from src.model.generate import batch_performance_render, map_midi  # noqa: E402
from src.model.pianoformer import PianoT5Gemma  # noqa: E402


def prepare_score(midi, keep_dynamics, quantize_div, score_velocity):
    if quantize_div:
        grid = midi.ticks_per_beat / quantize_div
        for ins in midi.instruments:
            for n in ins.notes:
                s = round(round(n.start / grid) * grid)
                e = round(round(n.end / grid) * grid)
                n.start, n.end = s, max(e, s + round(grid))
    if not keep_dynamics:
        for ins in midi.instruments:
            for n in ins.notes:
                n.velocity = score_velocity
            ins.control_changes = [c for c in ins.control_changes if c.number != 64]
    return midi


def fit_duration(score, perf):
    """Scale perf (1 tick = 1 ms) so its last onset equals the score's last onset in ms."""
    t = score.get_tick_to_time_mapping()
    score_last = max(t[n.start] for ins in score.instruments if not ins.is_drum for n in ins.notes) * 1000
    pins = perf.instruments[0]
    perf_last = max(n.start for n in pins.notes)
    if perf_last <= 0:
        return
    k = score_last / perf_last
    for n in pins.notes:
        n.start, n.end = round(n.start * k), max(round(n.end * k), round(n.start * k) + 1)
    for c in pins.control_changes:
        c.time = round(c.time * k)
    perf.max_tick = max([n.end for n in pins.notes] + [c.time for c in pins.control_changes]) + 1
    print(f"[fit-duration] timing scaled by {k:.3f}")


def summarize(label, midi):
    if isinstance(midi, str):
        midi = MidiFile(midi)
    notes = [n for ins in midi.instruments if not ins.is_drum for n in ins.notes]
    t = midi.get_tick_to_time_mapping()
    end = max(n.end for n in notes)
    vel = [n.velocity for n in notes]
    cc64 = [c for ins in midi.instruments for c in ins.control_changes if c.number == 64]
    print(
        f"[{label}] notes={len(notes)} dur={t[min(end, len(t) - 1)]:.2f}s "
        f"vel={min(vel)}-{max(vel)} cc64={len(cc64)} tempos={len(midi.tempo_changes)} "
        f"tpb={midi.ticks_per_beat}"
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="score MIDI")
    ap.add_argument("output", help="performance MIDI (raw, absolute ms at 120 BPM)")
    ap.add_argument("--editable", metavar="PATH", help="also write DAW-friendly tempo-mapped MIDI here")
    ap.add_argument("--temperature", type=float, default=1.0, help="sampling temperature (default 1.0, GUI range 0-2; authors warn low values can give extreme/repetitive expression)")
    ap.add_argument("--top-p", type=float, default=0.95, help="nucleus sampling (default 0.95)")
    ap.add_argument("--seed", type=int, default=None, help="random seed for a reproducible take")
    ap.add_argument("--device", default="cpu", choices=["cpu", "mps", "auto"], help="cpu (default, tested) | mps | auto")
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float32"], help="model dtype (repo default bfloat16)")
    ap.add_argument("--max-tempo", type=int, default=300, help="tempo clip for --editable output (default 300)")
    ap.add_argument("--pedal-offset", type=float, default=0.0, help="-1..+1, shift pedal points 2-4 earlier/later (default 0)")
    ap.add_argument("--context", type=int, default=4096, help="window length in tokens, <=4096, 8 tokens/note (default 4096)")
    ap.add_argument("--keep-input-dynamics", action="store_true", help="do not reset velocity to 80 / strip CC64 before inference")
    ap.add_argument("--score-velocity", type=int, default=80, help="velocity used when normalizing the score (default 80, as in training)")
    ap.add_argument("--quantize-div", type=int, default=0, help="snap input note on/off to 1/N beat before inference (e.g. 24 = 32nds + 16th triplets). 0 = off")
    ap.add_argument("--fit-duration", action="store_true", help="linearly rescale performed timing so the last onset matches the score's (removes global tempo drift, keeps local rubato)")
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
        torch.manual_seed(args.seed)

    device = args.device
    if device == "auto":
        device = "mps" if torch.backends.mps.is_available() else "cpu"
    dtype = torch.bfloat16 if args.dtype == "bfloat16" else torch.float32

    t0 = time.time()
    model = PianoT5Gemma.from_pretrained(MODEL_DIR, torch_dtype=dtype).to(device).eval()
    t_load = time.time() - t0

    score = MidiFile(args.input)
    summarize("input", args.input)
    score = prepare_score(score, args.keep_input_dynamics, args.quantize_div, args.score_velocity)

    t1 = time.time()
    res, _ = batch_performance_render(
        model,
        [score],
        max_context_length=args.context,
        temperature=args.temperature,
        top_p=args.top_p,
        device=device,
        pedal_offset=args.pedal_offset,
    )
    t_inf = time.time() - t1

    perf = res[0]
    if args.fit_duration:
        fit_duration(score, perf)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    perf.dump(args.output)
    summarize("raw", args.output)

    if args.editable:
        # map_midi re-reads the score; pass a fresh copy of the prepared score
        fresh = prepare_score(MidiFile(args.input), args.keep_input_dynamics, args.quantize_div, args.score_velocity)
        ed = map_midi(fresh, perf, max_tempo=args.max_tempo)
        ed.dump(args.editable)
        summarize("editable", args.editable)

    print(f"device={device} dtype={args.dtype} load={t_load:.1f}s inference={t_inf:.1f}s")


if __name__ == "__main__":
    main()

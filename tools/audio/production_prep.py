"""STAGE 3 — production prep for streaming upload.
Replicates the manual Audacity + MP3Gain(91) process:
  * constant gain targeting MP3Gain "Target Volume 91.0 dB" using the actual
    ReplayGain algorithm (ffmpeg `replaygain` filter), NO dynamics processing
  * limiter ceiling -1.5 dB as clip protection (codec overshoot headroom)
  * downmix to mono, encode 96 kbps CBR MP3, metadata preserved
Calibration (2026-08-20, verified against the team's MP3Gain on 3 files, exact
3.0 dB mono-convention offset): MP3Gain_volume = 92 - ffmpeg_track_gain, so
hitting volume 91.0 means leaving a final track_gain of +1.0 in ffmpeg's frame:
    gain_to_apply = measured_track_gain - 1.0
(LUFS-based normalization was retired: RG's filtered 95th-percentile statistic
disagrees with integrated LUFS by up to +-1.5 dB on dynamic ambient material.)
Usage: production_prep.py <in_dir> <out_dir> [workers=5]
Skips files whose output already exists (safe to re-run)."""
import os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

IN_DIR, OUT_DIR = sys.argv[1], sys.argv[2]
WORKERS = int(sys.argv[3]) if len(sys.argv) > 3 else 5
TARGET_FINAL_TG = 1.0   # ffmpeg track_gain left in the file == MP3Gain volume 91.0
os.makedirs(OUT_DIR, exist_ok=True)

files = sorted(
    f for f in os.listdir(IN_DIR)
    if f.lower().endswith(('.mp3', '.flac', '.wav')) and not f.startswith('.')
)

def chain(gain):
    # The FULL production chain (same pan as encode; bare `-ac 1` = hotter pan
    # law, never use it). The limiter must be inside the measured chain: boosts
    # push ambient peaks into it, and its shave lowers the RG statistic.
    return (f'volume={gain:.2f}dB,pan=mono|c0=0.5*c0+0.5*c1,'
            'alimiter=limit=0.841:level=false')

def measure_track_gain(path, stereo_source=True):
    # The 0.5/0.5 pan is ONLY for stereo sources (mirrors the encode's fold).
    # On an already-mono file that pan references a missing c1 and halves the
    # signal (-6 dB false reading) - scan mono outputs with no pan at all.
    af = 'pan=mono|c0=0.5*c0+0.5*c1,replaygain' if stereo_source else 'replaygain'
    r = subprocess.run(
        ['ffmpeg', '-hide_banner', '-i', path, '-af', af, '-f', 'null', '-'],
        capture_output=True, text=True)
    m = re.search(r'track_gain\s*=\s*([+-]?[0-9.]+)\s*dB', r.stderr)
    return float(m.group(1)) if m else None

def encode(src, dst, gain):
    r = subprocess.run(
        ['ffmpeg', '-v', 'quiet', '-y', '-i', src, '-af', chain(gain),
         '-ar', '44100', '-acodec', 'libmp3lame', '-b:a', '96k',
         '-map_metadata', '0', '-id3v2_version', '3', dst],
        capture_output=True)
    return r.returncode == 0 and os.path.exists(dst)

def prep(name):
    src = os.path.join(IN_DIR, name)
    dst = os.path.join(OUT_DIR, os.path.splitext(name)[0] + '.mp3')
    if os.path.exists(dst):
        return f'{name}: exists, skipped'
    tg = measure_track_gain(src)
    if tg is None:
        return f'{name}: MEASURE FAILED'
    gain = tg - TARGET_FINAL_TG
    # Converge on the ENCODED file: both the limiter (boosted peaks get shaved)
    # and the 96k mono encode itself lower the RG statistic by a few tenths of
    # a dB, so encode -> scan -> correct until the deliverable measures right.
    final_tg = None
    for _ in range(3):
        if not encode(src, dst, gain):
            return f'{name}: ENCODE FAILED'
        final_tg = measure_track_gain(dst, stereo_source=False)
        if final_tg is None:
            return f'{name}: SCAN FAILED'
        err = final_tg - TARGET_FINAL_TG
        if abs(err) <= 0.15:
            break
        gain += err
    vol = 92.0 - final_tg
    return f'{name}: gain {gain:+.1f} dB -> MP3Gain volume {vol:.2f}'

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for i, res in enumerate(ex.map(prep, files), 1):
            print(f'[{i}/{len(files)}] {res}')
    print(f'STAGE3 DONE: {len(files)} inputs -> {OUT_DIR}')

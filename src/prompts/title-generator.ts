/**
 * Unique title generator for music tracks
 * Generates evocative, unique titles with global persistence
 * All titles use positive/neutral vocabulary only
 */

import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Path to persistent storage for used titles
const DATA_DIR = join(__dirname, '../../data');
const USED_TITLES_FILE = join(DATA_DIR, 'used-titles.json');

// Default prefix for all titles
const DEFAULT_PREFIX = 'MU';

// Configurable prefix (can be changed via setTitlePrefix)
let titlePrefix = DEFAULT_PREFIX;

/**
 * Massive vocabulary for title generation - POSITIVE/NEUTRAL WORDS ONLY
 * Target: 2000+ unique words for thousands of track combinations
 */
const VOCABULARY = {
  // Time-related (100+ words)
  times: [
    // Times of day
    'Dawn', 'Sunrise', 'Morning', 'Midday', 'Afternoon', 'Evening', 'Dusk', 'Twilight', 'Sunset', 'Night',
    'Midnight', 'Daybreak', 'Daylight', 'Nightfall', 'Starlight', 'Moonlight', 'Sunlight',
    // Seasons
    'Spring', 'Summer', 'Autumn', 'Winter', 'Springtime', 'Summertime', 'Wintertime',
    // Time concepts
    'Golden Hour', 'Blue Hour', 'Magic Hour', 'First Light', 'New Day', 'New Moon', 'Full Moon',
    'Eternal', 'Timeless', 'Everlasting', 'Infinite', 'Forever', 'Always', 'Ever',
    // Temporal adjectives
    'Early', 'Late', 'Ancient', 'Modern', 'Classic', 'Vintage', 'Contemporary',
    // Moments
    'Moment', 'Instant', 'Second', 'Hour', 'Day', 'Week', 'Month', 'Year', 'Century', 'Era',
    'Beginning', 'Start', 'Origin', 'Genesis', 'Opening', 'Awakening', 'Arrival',
    // Celestial time
    'Equinox', 'Solstice', 'Eclipse', 'Crescent', 'Waning', 'Waxing', 'Rising', 'Setting'
  ],

  // Places & Locations (200+ words)
  places: [
    // Nature locations
    'Garden', 'Meadow', 'Valley', 'Hill', 'Mountain', 'Peak', 'Summit', 'Ridge', 'Cliff',
    'Forest', 'Grove', 'Woods', 'Woodland', 'Glade', 'Clearing', 'Thicket', 'Orchard',
    'River', 'Stream', 'Creek', 'Brook', 'Lake', 'Pond', 'Lagoon', 'Bay', 'Cove', 'Inlet',
    'Ocean', 'Sea', 'Beach', 'Shore', 'Coast', 'Island', 'Peninsula', 'Cape', 'Reef',
    'Desert', 'Oasis', 'Dune', 'Canyon', 'Ravine', 'Gorge', 'Cavern', 'Grotto',
    'Prairie', 'Savanna', 'Steppe', 'Tundra', 'Glacier', 'Waterfall', 'Spring', 'Well',
    // Urban locations
    'City', 'Town', 'Village', 'Square', 'Plaza', 'Park', 'Avenue', 'Boulevard', 'Street',
    'Alley', 'Lane', 'Path', 'Trail', 'Road', 'Way', 'Passage', 'Corridor', 'Arcade',
    'Bridge', 'Pier', 'Dock', 'Harbor', 'Port', 'Marina', 'Wharf', 'Quay', 'Jetty',
    'Station', 'Terminal', 'Gateway', 'Entrance', 'Exit', 'Crossing', 'Junction',
    // Buildings & Structures
    'Tower', 'Castle', 'Palace', 'Temple', 'Shrine', 'Chapel', 'Cathedral', 'Monastery',
    'Villa', 'Manor', 'Estate', 'Cottage', 'Cabin', 'Lodge', 'Inn', 'Tavern',
    'Cafe', 'Bistro', 'Lounge', 'Club', 'Studio', 'Gallery', 'Museum', 'Library',
    'Theater', 'Cinema', 'Hall', 'Ballroom', 'Pavilion', 'Pergola', 'Gazebo', 'Kiosk',
    // Interior spaces
    'Room', 'Chamber', 'Suite', 'Loft', 'Attic', 'Basement', 'Cellar', 'Vault',
    'Terrace', 'Balcony', 'Veranda', 'Porch', 'Patio', 'Deck', 'Courtyard', 'Atrium',
    'Foyer', 'Lobby', 'Parlor', 'Salon', 'Study', 'Den', 'Nook', 'Alcove', 'Corner',
    // Abstract places
    'Haven', 'Sanctuary', 'Retreat', 'Refuge', 'Hideaway', 'Paradise', 'Eden', 'Utopia',
    'Threshold', 'Doorway', 'Window', 'Portal', 'Gate', 'Arch', 'Frame', 'Border',
    'Horizon', 'Skyline', 'Landscape', 'Vista', 'Panorama', 'View', 'Scene', 'Setting'
  ],

  // Nature & Weather (200+ words)
  nature: [
    // Weather
    'Rain', 'Drizzle', 'Shower', 'Mist', 'Fog', 'Haze', 'Dew', 'Frost', 'Snow', 'Snowfall',
    'Breeze', 'Wind', 'Gust', 'Zephyr', 'Gale', 'Whirl', 'Swirl', 'Draft', 'Current', 'Flow',
    'Cloud', 'Cumulus', 'Cirrus', 'Nimbus', 'Stratus', 'Vapor', 'Steam', 'Smoke', 'Plume',
    'Sun', 'Ray', 'Beam', 'Shaft', 'Glow', 'Gleam', 'Glint', 'Glimmer', 'Shimmer', 'Sparkle',
    'Moon', 'Star', 'Comet', 'Meteor', 'Planet', 'Constellation', 'Galaxy', 'Nebula', 'Cosmos',
    'Rainbow', 'Aurora', 'Halo', 'Corona', 'Prism', 'Spectrum', 'Arc', 'Bow', 'Circle',
    // Water
    'Wave', 'Tide', 'Current', 'Ripple', 'Splash', 'Spray', 'Foam', 'Bubble', 'Drop', 'Droplet',
    'Pool', 'Puddle', 'Pond', 'Spring', 'Fountain', 'Cascade', 'Torrent', 'Rapids', 'Eddy',
    // Plants
    'Flower', 'Blossom', 'Bloom', 'Petal', 'Leaf', 'Branch', 'Twig', 'Stem', 'Root', 'Seed',
    'Rose', 'Lily', 'Lotus', 'Orchid', 'Tulip', 'Daisy', 'Iris', 'Jasmine', 'Lavender', 'Violet',
    'Cherry', 'Plum', 'Peach', 'Apple', 'Maple', 'Oak', 'Pine', 'Cedar', 'Willow', 'Bamboo',
    'Fern', 'Moss', 'Ivy', 'Vine', 'Grass', 'Clover', 'Heather', 'Sage', 'Mint', 'Basil',
    // Animals (peaceful)
    'Bird', 'Swan', 'Crane', 'Heron', 'Dove', 'Sparrow', 'Lark', 'Nightingale', 'Finch', 'Robin',
    'Butterfly', 'Dragonfly', 'Firefly', 'Ladybug', 'Bee', 'Cricket', 'Cicada',
    'Deer', 'Fawn', 'Rabbit', 'Hare', 'Fox', 'Otter', 'Seal', 'Dolphin', 'Whale',
    'Fish', 'Koi', 'Goldfish', 'Salmon', 'Trout', 'Seahorse', 'Starfish', 'Jellyfish',
    // Earth elements
    'Stone', 'Rock', 'Pebble', 'Boulder', 'Crystal', 'Gem', 'Jewel', 'Diamond', 'Pearl',
    'Sand', 'Dust', 'Soil', 'Earth', 'Clay', 'Mineral', 'Ore', 'Metal', 'Gold', 'Silver',
    // Sky elements
    'Sky', 'Heaven', 'Air', 'Atmosphere', 'Ether', 'Space', 'Void', 'Infinity', 'Beyond'
  ],

  // Emotions & States - POSITIVE/NEUTRAL ONLY (150+ words)
  emotions: [
    // Joy & Happiness
    'Joy', 'Happiness', 'Bliss', 'Delight', 'Pleasure', 'Elation', 'Euphoria', 'Ecstasy',
    'Cheer', 'Glee', 'Mirth', 'Merriment', 'Jubilation', 'Celebration', 'Festivity',
    // Peace & Calm
    'Peace', 'Calm', 'Serenity', 'Tranquility', 'Stillness', 'Quietude', 'Repose', 'Rest',
    'Ease', 'Comfort', 'Relaxation', 'Contentment', 'Satisfaction', 'Fulfillment',
    // Love & Affection
    'Love', 'Affection', 'Fondness', 'Adoration', 'Devotion', 'Tenderness', 'Warmth', 'Care',
    'Kindness', 'Compassion', 'Empathy', 'Sympathy', 'Understanding', 'Acceptance',
    // Hope & Dreams
    'Hope', 'Dream', 'Wish', 'Aspiration', 'Ambition', 'Vision', 'Imagination', 'Fantasy',
    'Wonder', 'Awe', 'Marvel', 'Amazement', 'Fascination', 'Curiosity', 'Discovery',
    // Courage & Strength
    'Courage', 'Bravery', 'Valor', 'Spirit', 'Determination', 'Resolve', 'Will', 'Power',
    'Strength', 'Energy', 'Vitality', 'Vigor', 'Life', 'Liveliness', 'Animation',
    // Grace & Beauty
    'Grace', 'Elegance', 'Beauty', 'Charm', 'Allure', 'Radiance', 'Brilliance', 'Splendor',
    'Majesty', 'Glory', 'Grandeur', 'Magnificence', 'Wonder', 'Marvel',
    // Connection
    'Harmony', 'Unity', 'Connection', 'Bond', 'Link', 'Tie', 'Union', 'Fusion', 'Blend',
    'Belonging', 'Togetherness', 'Fellowship', 'Friendship', 'Companionship', 'Partnership',
    // Mindful states
    'Awareness', 'Presence', 'Mindfulness', 'Consciousness', 'Clarity', 'Insight', 'Wisdom',
    'Knowledge', 'Understanding', 'Perception', 'Intuition', 'Instinct', 'Sense',
    // Gentle emotions
    'Gentleness', 'Softness', 'Sweetness', 'Mildness', 'Smoothness', 'Lightness', 'Airiness',
    'Solace', 'Refuge', 'Shelter', 'Safety', 'Security', 'Protection', 'Sanctuary',
    // Memory & Nostalgia (positive)
    'Memory', 'Remembrance', 'Nostalgia', 'Reminiscence', 'Recollection', 'Reflection',
    'Heritage', 'Legacy', 'Tradition', 'History', 'Story', 'Tale', 'Legend', 'Myth'
  ],

  // Colors & Materials (100+ words)
  colors: [
    // Basic colors (warm)
    'Red', 'Orange', 'Yellow', 'Gold', 'Golden', 'Amber', 'Copper', 'Bronze', 'Brass',
    'Coral', 'Salmon', 'Peach', 'Apricot', 'Tangerine', 'Rust', 'Terracotta', 'Sienna',
    // Basic colors (cool)
    'Blue', 'Cyan', 'Teal', 'Turquoise', 'Aqua', 'Azure', 'Cerulean', 'Cobalt', 'Navy',
    'Indigo', 'Violet', 'Purple', 'Lavender', 'Lilac', 'Mauve', 'Plum', 'Magenta', 'Fuchsia',
    // Basic colors (neutral)
    'Green', 'Emerald', 'Jade', 'Sage', 'Olive', 'Forest', 'Mint', 'Lime', 'Chartreuse',
    'White', 'Cream', 'Ivory', 'Pearl', 'Snow', 'Frost', 'Cloud', 'Milk', 'Vanilla',
    'Silver', 'Platinum', 'Chrome', 'Steel', 'Iron', 'Pewter', 'Graphite', 'Charcoal',
    // Precious stones
    'Ruby', 'Sapphire', 'Emerald', 'Diamond', 'Topaz', 'Opal', 'Amethyst', 'Garnet', 'Onyx',
    'Jade', 'Jasper', 'Lapis', 'Moonstone', 'Sunstone', 'Turquoise', 'Quartz', 'Crystal',
    // Materials/Textures
    'Velvet', 'Silk', 'Satin', 'Lace', 'Linen', 'Cotton', 'Wool', 'Cashmere', 'Chiffon',
    'Glass', 'Crystal', 'Porcelain', 'Ceramic', 'Marble', 'Granite', 'Sandstone', 'Limestone',
    'Wood', 'Oak', 'Mahogany', 'Teak', 'Cedar', 'Pine', 'Birch', 'Maple', 'Bamboo',
    // Color qualities
    'Bright', 'Vivid', 'Rich', 'Deep', 'Pale', 'Light', 'Soft', 'Muted', 'Pastel', 'Dusty'
  ],

  // Abstract & Poetic (150+ words)
  abstract: [
    // Visual phenomena
    'Light', 'Shadow', 'Shade', 'Glow', 'Gleam', 'Glint', 'Glimmer', 'Shimmer', 'Sparkle', 'Shine',
    'Flicker', 'Flash', 'Blaze', 'Flame', 'Fire', 'Ember', 'Spark', 'Ignite', 'Radiance', 'Luminance',
    'Reflection', 'Refraction', 'Prism', 'Spectrum', 'Hue', 'Tint', 'Shade', 'Tone', 'Gradient',
    // Sound phenomena
    'Echo', 'Resonance', 'Vibration', 'Frequency', 'Wavelength', 'Harmony', 'Chord', 'Note', 'Tone',
    'Whisper', 'Murmur', 'Hum', 'Buzz', 'Ring', 'Chime', 'Bell', 'Toll', 'Peal', 'Knell',
    // Movement
    'Flow', 'Stream', 'Current', 'Drift', 'Float', 'Glide', 'Soar', 'Fly', 'Rise', 'Ascend',
    'Wave', 'Ripple', 'Swirl', 'Spiral', 'Curl', 'Twist', 'Turn', 'Spin', 'Rotate', 'Revolve',
    'Dance', 'Waltz', 'Sway', 'Swing', 'Rock', 'Roll', 'Bounce', 'Spring', 'Leap', 'Jump',
    // Abstract concepts
    'Essence', 'Spirit', 'Soul', 'Heart', 'Core', 'Center', 'Source', 'Origin', 'Root', 'Seed',
    'Truth', 'Beauty', 'Good', 'Right', 'Just', 'Fair', 'Pure', 'Clean', 'Clear', 'True',
    'Form', 'Shape', 'Figure', 'Outline', 'Silhouette', 'Profile', 'Contour', 'Line', 'Curve',
    'Pattern', 'Design', 'Motif', 'Theme', 'Style', 'Mode', 'Manner', 'Way', 'Path', 'Journey',
    // Space & Dimension
    'Space', 'Place', 'Point', 'Spot', 'Site', 'Location', 'Position', 'Area', 'Zone', 'Region',
    'Dimension', 'Realm', 'Domain', 'Sphere', 'Orbit', 'Circle', 'Ring', 'Arc', 'Curve', 'Bend',
    'Height', 'Depth', 'Width', 'Length', 'Distance', 'Range', 'Span', 'Reach', 'Scope', 'Scale',
    // Connection & Relation
    'Link', 'Bond', 'Tie', 'Chain', 'Thread', 'String', 'Wire', 'Cord', 'Rope', 'Net',
    'Bridge', 'Path', 'Way', 'Road', 'Route', 'Course', 'Track', 'Trail', 'Line', 'Connection',
    // Cycles & Patterns
    'Cycle', 'Circle', 'Loop', 'Spiral', 'Helix', 'Coil', 'Wave', 'Pulse', 'Beat', 'Rhythm'
  ],

  // Actions & Movements - POSITIVE ONLY (100+ words)
  actions: [
    // Upward/Forward movement
    'Rising', 'Ascending', 'Climbing', 'Soaring', 'Flying', 'Floating', 'Gliding', 'Hovering',
    'Growing', 'Blooming', 'Flourishing', 'Thriving', 'Prospering', 'Expanding', 'Spreading',
    // Gentle movement
    'Drifting', 'Flowing', 'Streaming', 'Trickling', 'Rippling', 'Swirling', 'Twirling',
    'Dancing', 'Swaying', 'Rocking', 'Swinging', 'Waving', 'Fluttering', 'Rustling',
    // Discovery & Creation
    'Finding', 'Discovering', 'Exploring', 'Seeking', 'Searching', 'Wandering', 'Roaming',
    'Creating', 'Making', 'Building', 'Crafting', 'Shaping', 'Forming', 'Designing',
    // Light & Energy
    'Shining', 'Glowing', 'Gleaming', 'Sparkling', 'Twinkling', 'Glittering', 'Radiating',
    'Burning', 'Blazing', 'Illuminating', 'Brightening', 'Lighting', 'Warming', 'Heating',
    // Connection & Gathering
    'Gathering', 'Collecting', 'Joining', 'Connecting', 'Linking', 'Bonding', 'Uniting',
    'Meeting', 'Greeting', 'Welcoming', 'Embracing', 'Holding', 'Keeping', 'Treasuring',
    // Sound & Voice
    'Singing', 'Humming', 'Whistling', 'Chiming', 'Ringing', 'Echoing', 'Resonating',
    'Calling', 'Speaking', 'Telling', 'Sharing', 'Giving', 'Offering', 'Presenting',
    // Rest & Peace
    'Resting', 'Sleeping', 'Dreaming', 'Wishing', 'Hoping', 'Believing', 'Trusting',
    'Breathing', 'Sighing', 'Relaxing', 'Calming', 'Soothing', 'Healing', 'Restoring',
    // Arrival & Beginning
    'Arriving', 'Coming', 'Approaching', 'Nearing', 'Reaching', 'Touching', 'Landing',
    'Beginning', 'Starting', 'Opening', 'Awakening', 'Waking', 'Emerging', 'Appearing'
  ],

  // Adjectives - POSITIVE/NEUTRAL ONLY (200+ words)
  adjectives: [
    // Soft/Gentle
    'Gentle', 'Soft', 'Smooth', 'Tender', 'Delicate', 'Fine', 'Light', 'Airy', 'Feathery',
    'Mild', 'Mellow', 'Calm', 'Quiet', 'Still', 'Peaceful', 'Serene', 'Tranquil', 'Placid',
    // Warm/Cozy
    'Warm', 'Cozy', 'Snug', 'Comfortable', 'Homey', 'Inviting', 'Welcoming', 'Friendly',
    'Pleasant', 'Agreeable', 'Nice', 'Lovely', 'Beautiful', 'Pretty', 'Handsome', 'Attractive',
    // Bright/Clear
    'Bright', 'Clear', 'Clean', 'Pure', 'Fresh', 'Crisp', 'Vivid', 'Vibrant', 'Radiant',
    'Luminous', 'Shining', 'Glowing', 'Gleaming', 'Sparkling', 'Twinkling', 'Brilliant',
    // Cool/Refreshing
    'Cool', 'Fresh', 'Refreshing', 'Invigorating', 'Brisk', 'Crisp', 'Sharp', 'Keen',
    // Rich/Full
    'Rich', 'Full', 'Complete', 'Whole', 'Total', 'Entire', 'Utter', 'Absolute', 'Perfect',
    'Deep', 'Profound', 'Intense', 'Strong', 'Powerful', 'Mighty', 'Grand', 'Great',
    // Simple/Natural
    'Simple', 'Plain', 'Natural', 'Organic', 'Real', 'True', 'Genuine', 'Authentic', 'Original',
    'Raw', 'Unrefined', 'Rustic', 'Rural', 'Country', 'Pastoral', 'Bucolic', 'Idyllic',
    // Elegant/Refined
    'Elegant', 'Graceful', 'Refined', 'Polished', 'Sophisticated', 'Cultured', 'Classy',
    'Chic', 'Stylish', 'Fashionable', 'Trendy', 'Modern', 'Contemporary', 'Current',
    // Old/Classic
    'Classic', 'Timeless', 'Eternal', 'Everlasting', 'Enduring', 'Lasting', 'Permanent',
    'Ancient', 'Old', 'Aged', 'Mature', 'Vintage', 'Antique', 'Historic', 'Traditional',
    // New/Fresh
    'New', 'Young', 'Fresh', 'Novel', 'Original', 'Innovative', 'Creative', 'Inventive',
    // Size
    'Big', 'Large', 'Great', 'Grand', 'Vast', 'Wide', 'Broad', 'Expansive', 'Spacious',
    'Small', 'Little', 'Tiny', 'Mini', 'Compact', 'Cozy', 'Intimate', 'Personal', 'Private',
    // Distance
    'Near', 'Close', 'Nearby', 'Adjacent', 'Neighboring', 'Surrounding', 'Encircling',
    'Far', 'Distant', 'Remote', 'Faraway', 'Beyond', 'Outer', 'Inner', 'Central', 'Core',
    // Height
    'High', 'Tall', 'Lofty', 'Elevated', 'Raised', 'Upper', 'Top', 'Peak', 'Summit',
    'Low', 'Short', 'Ground', 'Base', 'Bottom', 'Lower', 'Under', 'Beneath', 'Below',
    // Movement quality
    'Swift', 'Quick', 'Fast', 'Rapid', 'Speedy', 'Fleet', 'Nimble', 'Agile', 'Graceful',
    'Slow', 'Gradual', 'Steady', 'Even', 'Smooth', 'Fluid', 'Flowing', 'Continuous',
    // Visibility
    'Visible', 'Clear', 'Obvious', 'Apparent', 'Evident', 'Plain', 'Open', 'Exposed',
    'Hidden', 'Secret', 'Private', 'Secluded', 'Sheltered', 'Protected', 'Safe', 'Secure',
    // Special qualities
    'Special', 'Unique', 'Rare', 'Precious', 'Valuable', 'Priceless', 'Treasured', 'Cherished',
    'Magic', 'Magical', 'Mystical', 'Enchanted', 'Charmed', 'Blessed', 'Sacred', 'Holy',
    'Wild', 'Free', 'Untamed', 'Natural', 'Organic', 'Living', 'Alive', 'Vibrant', 'Dynamic'
  ],

  // Music-specific (80+ words)
  musical: [
    // Classical forms
    'Nocturne', 'Prelude', 'Interlude', 'Overture', 'Finale', 'Coda', 'Etude', 'Opus',
    'Waltz', 'Minuet', 'Polonaise', 'Mazurka', 'Bolero', 'Tango', 'Samba', 'Bossa',
    'Ballad', 'Serenade', 'Lullaby', 'Cradle', 'Hymn', 'Anthem', 'Carol', 'Chant',
    'Sonata', 'Sonatina', 'Concerto', 'Symphony', 'Suite', 'Fantasia', 'Rhapsody',
    'Aria', 'Cantata', 'Oratorio', 'Opera', 'Fugue', 'Canon', 'Round', 'Rondo',
    // Musical concepts
    'Melody', 'Harmony', 'Rhythm', 'Beat', 'Pulse', 'Tempo', 'Groove', 'Swing',
    'Theme', 'Variation', 'Motif', 'Phrase', 'Passage', 'Movement', 'Section', 'Part',
    'Chord', 'Note', 'Tone', 'Sound', 'Voice', 'Vocal', 'Instrumental', 'Acoustic',
    // Dynamics
    'Piano', 'Forte', 'Crescendo', 'Diminuendo', 'Staccato', 'Legato', 'Vibrato',
    // Performance
    'Solo', 'Duet', 'Trio', 'Quartet', 'Ensemble', 'Orchestra', 'Band', 'Choir',
    'Performance', 'Concert', 'Recital', 'Session', 'Jam', 'Improvisation', 'Encore'
  ],

  // Cultural/Regional (100+ words for genre-specific titles)
  cultural: {
    asian: [
      'Zen', 'Tao', 'Chi', 'Yin', 'Yang', 'Feng', 'Shui', 'Qi', 'Wu', 'Wei',
      'Lotus', 'Bamboo', 'Jade', 'Silk', 'Pearl', 'Dragon', 'Phoenix', 'Crane', 'Koi',
      'Temple', 'Pagoda', 'Garden', 'Bridge', 'Lantern', 'Fan', 'Scroll', 'Ink',
      'Mountain', 'River', 'Lake', 'Mist', 'Cloud', 'Moon', 'Blossom', 'Petal',
      'Tea', 'Incense', 'Bell', 'Gong', 'Chime', 'Flute', 'String', 'Zither',
      'Spring', 'Autumn', 'Rain', 'Snow', 'Wind', 'Leaf', 'Stone', 'Water',
      'Harmony', 'Balance', 'Peace', 'Wisdom', 'Journey', 'Path', 'Way', 'Light',
      'Ancient', 'Eternal', 'Sacred', 'Pure', 'Gentle', 'Flowing', 'Rising', 'Floating'
    ],
    jazz: [
      'Blue', 'Cool', 'Hot', 'Sweet', 'Smooth', 'Mellow', 'Groovy', 'Funky',
      'Swing', 'Bop', 'Bebop', 'Modal', 'Free', 'Fusion', 'Latin', 'Afro',
      'Club', 'Lounge', 'Bar', 'Cafe', 'Street', 'Corner', 'Avenue', 'Boulevard',
      'Night', 'Midnight', 'Evening', 'Twilight', 'Dawn', 'Morning', 'Afternoon',
      'City', 'Urban', 'Downtown', 'Uptown', 'Harlem', 'Village', 'Quarter',
      'Soul', 'Heart', 'Spirit', 'Vibe', 'Mood', 'Feel', 'Touch', 'Taste',
      'Bass', 'Keys', 'Horn', 'Sax', 'Trumpet', 'Piano', 'Guitar', 'Drums',
      'Session', 'Set', 'Gig', 'Jam', 'Solo', 'Duo', 'Trio', 'Quartet'
    ],
    ambient: [
      'Space', 'Void', 'Cosmos', 'Galaxy', 'Nebula', 'Star', 'Planet', 'Moon',
      'Drift', 'Float', 'Hover', 'Suspend', 'Levitate', 'Ascend', 'Transcend',
      'Deep', 'Vast', 'Infinite', 'Endless', 'Boundless', 'Limitless', 'Eternal',
      'Quiet', 'Still', 'Calm', 'Serene', 'Peaceful', 'Tranquil', 'Silent',
      'Ambient', 'Atmospheric', 'Ethereal', 'Celestial', 'Astral', 'Cosmic', 'Divine',
      'Texture', 'Layer', 'Wash', 'Pad', 'Drone', 'Hum', 'Tone', 'Frequency',
      'Inner', 'Outer', 'Beyond', 'Within', 'Between', 'Through', 'Across', 'Over'
    ],
    house: [
      'Groove', 'Soul', 'Vibe', 'Pulse', 'Deep', 'Soulful', 'Silky', 'Warm',
      'Hypnotic', 'Driving', 'Rolling', 'Diva', 'Gospel', 'Rhythm', 'Night',
      'Underground', 'Classic', 'Timeless', 'Velvet', 'Sultry', 'Smooth', 'Uplifting',
      'Floor', 'Club', 'Lounge', 'Late', 'Midnight', 'After', 'Hours', 'Dawn',
      'Keys', 'Rhodes', 'Organ', 'Sax', 'Strings', 'Horns', 'Bass', 'Kick',
      'Shuffle', 'Swing', 'Bounce', 'Glide', 'Float', 'Rise', 'Build', 'Release',
      'Bliss', 'Ecstasy', 'Freedom', 'Unity', 'Together', 'Love', 'Spirit', 'Feel'
    ],
    tropical: [
      'Sun', 'Summer', 'Beach', 'Ocean', 'Wave', 'Island', 'Paradise', 'Tropical',
      'Palm', 'Sunset', 'Sunrise', 'Golden', 'Breeze', 'Shore', 'Coast', 'Sand',
      'Sea', 'Tide', 'Horizon', 'Escape', 'Getaway', 'Vacation', 'Holiday', 'Dream',
      'Chill', 'Relax', 'Easy', 'Breezy', 'Carefree', 'Free', 'Warm', 'Sunny',
      'Glow', 'Shimmer', 'Sparkle', 'Blue', 'Aqua', 'Coral', 'Lagoon', 'Bay',
      'Marimba', 'Steel', 'Flute', 'Acoustic', 'Mellow', 'Laid', 'Back', 'Vibes'
    ],
    chillout: [
      // Balearic / Ibiza vibes
      'Ibiza', 'Balearic', 'Mediterranean', 'Sunset', 'Horizon', 'Coastline', 'Terrace',
      'Chill', 'Lounge', 'Bar', 'Lobby', 'Rooftop', 'Poolside', 'Veranda', 'Balcony',
      // Buddha Bar / Oriental influence
      'Zen', 'Buddha', 'Oriental', 'Eastern', 'Exotic', 'Ethnic', 'Tribal', 'Sacred',
      'Silk', 'Incense', 'Lantern', 'Temple', 'Sanctuary', 'Oasis', 'Haven', 'Retreat',
      // Downtempo / Atmospheric
      'Drift', 'Float', 'Hover', 'Glide', 'Flow', 'Stream', 'Current', 'Wave',
      'Deep', 'Ambient', 'Atmospheric', 'Ethereal', 'Hypnotic', 'Dreamy', 'Hazy', 'Misty',
      // Sophisticated / Luxury
      'Velvet', 'Silk', 'Satin', 'Cashmere', 'Marble', 'Crystal', 'Gold', 'Platinum',
      'Elegant', 'Refined', 'Sophisticated', 'Luxe', 'Opulent', 'Plush', 'Lush', 'Rich',
      // Time / Evening
      'Twilight', 'Dusk', 'Evening', 'Night', 'Midnight', 'Late', 'After', 'Hours',
      'Golden', 'Blue', 'Magic', 'Starlit', 'Moonlit', 'Candlelit', 'Dim', 'Soft',
      // Mood / Feeling
      'Sensual', 'Mysterious', 'Enchanting', 'Captivating', 'Alluring', 'Seductive', 'Intimate',
      'Serene', 'Tranquil', 'Peaceful', 'Calm', 'Relaxed', 'Mellow', 'Smooth', 'Warm'
    ],
    electroswing: [
      // Era / Vintage
      'Gatsby', 'Roaring', 'Twenties', 'Vintage', 'Retro', 'Classic', 'Speakeasy', 'Prohibition',
      'Antique', 'Golden', 'Era', 'Age', 'Deco', 'Glamour', 'Flapper', 'Charleston',
      // Energy / Movement
      'Swing', 'Bounce', 'Jump', 'Hop', 'Step', 'Stomp', 'Strut', 'Shuffle',
      'Dance', 'Groove', 'Beat', 'Rhythm', 'Pulse', 'Drive', 'Rush', 'Flash',
      // Brass / Jazz elements
      'Brass', 'Horn', 'Trumpet', 'Trombone', 'Big', 'Band', 'Club', 'Joint',
      'Hot', 'Cool', 'Slick', 'Sharp', 'Snappy', 'Peppy', 'Zippy', 'Fizzy',
      // Places / Venues
      'Ballroom', 'Stage', 'Floor', 'Hall', 'Theater', 'Cabaret', 'Revue', 'Show',
      'Street', 'Corner', 'Downtown', 'Uptown', 'City', 'Night', 'Lights', 'Neon',
      // Mood / Feel
      'Party', 'Fun', 'Wild', 'Crazy', 'Happy', 'Jolly', 'Merry', 'Lively',
      'Electric', 'Magnetic', 'Dynamic', 'Vibrant', 'Sparkling', 'Fizzing', 'Buzzing', 'Swinging',
      // Style
      'Dandy', 'Dapper', 'Fancy', 'Swanky', 'Ritzy', 'Snazzy', 'Classy', 'Sassy'
    ],
    nudisco: [
      // Disco / Dance vibes
      'Disco', 'Groove', 'Funk', 'Boogie', 'Dance', 'Floor', 'Mirror', 'Ball',
      'Glitter', 'Sparkle', 'Shine', 'Glow', 'Flash', 'Strobe', 'Neon', 'Laser',
      // Nightlife / Venues
      'Club', 'Night', 'Midnight', 'Late', 'After', 'Hours', 'Downtown', 'Studio',
      'Lounge', 'Party', 'Scene', 'Vibe', 'Fever', 'Heat', 'Fire', 'Burn',
      // Feelings / Energy
      'Hypnotized', 'Electric', 'Magnetic', 'Euphoric', 'High', 'Rush', 'Thrill', 'Pulse',
      'Free', 'Alive', 'Wild', 'Lost', 'Found', 'Touch', 'Feel', 'Move',
      // Romance / Connection
      'Love', 'Heart', 'Soul', 'Kiss', 'Desire', 'Dream', 'Fantasy', 'Paradise',
      'Together', 'Tonight', 'Forever', 'Always', 'Never', 'Again', 'More', 'You',
      // Retro / Style
      'Funky', 'Groovy', 'Smooth', 'Cool', 'Hot', 'Sexy', 'Sweet', 'Sugar',
      'Vinyl', 'Retro', 'Classic', 'Golden', 'Summer', 'Sunset', 'Sunrise', 'Dawn',
      // Sound / Music
      'Beat', 'Bass', 'Rhythm', 'Melody', 'Sound', 'Wave', 'Frequency', 'Vibration'
    ],
    latin: [
      // Beach / Coastal vibes
      'Playa', 'Costa', 'Marina', 'Bahia', 'Tropical', 'Island', 'Shore', 'Wave',
      'Sunset', 'Sunrise', 'Horizon', 'Ocean', 'Sea', 'Breeze', 'Palm', 'Paradise',
      // Warmth / Feelings
      'Caliente', 'Warm', 'Sol', 'Golden', 'Bronzed', 'Glow', 'Radiant', 'Sultry',
      'Sensual', 'Smooth', 'Silky', 'Velvet', 'Soft', 'Gentle', 'Tender', 'Sweet',
      // Romance / Passion
      'Amor', 'Corazon', 'Beso', 'Dulce', 'Suave', 'Cielo', 'Luna', 'Estrella',
      'Passion', 'Desire', 'Dream', 'Romance', 'Embrace', 'Touch', 'Kiss', 'Love',
      // Rhythm / Music
      'Ritmo', 'Sabor', 'Salsa', 'Bossa', 'Samba', 'Rumba', 'Conga', 'Groove',
      'Clave', 'Tumbao', 'Montuno', 'Guajira', 'Son', 'Mambo', 'Cha', 'Beat',
      // Places / Atmosphere
      'Havana', 'Rio', 'Cuba', 'Brazil', 'Caribbean', 'Ibiza', 'Marbella', 'Miami',
      'Lounge', 'Terrace', 'Cabana', 'Villa', 'Rooftop', 'Poolside', 'Beachside', 'Waterfront',
      // Time / Evening
      'Noche', 'Tarde', 'Atardecer', 'Twilight', 'Dusk', 'Evening', 'Night', 'Midnight',
      // Feelings
      'Tranquilo', 'Sereno', 'Chill', 'Relax', 'Easy', 'Lazy', 'Mellow', 'Cool',
      'Alegria', 'Feliz', 'Libre', 'Vivo', 'Fresco', 'Sueno', 'Encanto', 'Magia'
    ]
  }
};

// Genre-specific title patterns (which vocabulary categories to combine)
const GENRE_PATTERNS: Record<string, string[][]> = {
  jazz: [
    ['adjectives', 'places'],
    ['colors', 'musical'],
    ['times', 'emotions'],
    ['nature', 'abstract'],
    ['adjectives', 'emotions'],
    ['places', 'musical'],
    ['times', 'places'],
    ['colors', 'places'],
    ['adjectives', 'musical'],
    ['nature', 'emotions'],
    ['abstract', 'places'],
    ['adjectives', 'abstract'],
  ],
  chinese: [
    ['nature', 'places'],
    ['adjectives', 'nature'],
    ['times', 'nature'],
    ['abstract', 'emotions'],
    ['colors', 'nature'],
    ['nature', 'abstract'],
    ['adjectives', 'places'],
    ['times', 'places'],
    ['emotions', 'nature'],
    ['colors', 'places'],
  ],
  lounge: [
    ['times', 'places'],
    ['adjectives', 'musical'],
    ['colors', 'emotions'],
    ['nature', 'abstract'],
    ['places', 'emotions'],
    ['adjectives', 'places'],
    ['times', 'emotions'],
    ['colors', 'musical'],
    ['abstract', 'places'],
    ['adjectives', 'nature'],
  ],
  cafe: [
    ['times', 'places'],
    ['adjectives', 'nature'],
    ['colors', 'abstract'],
    ['emotions', 'musical'],
    ['nature', 'emotions'],
    ['adjectives', 'places'],
    ['times', 'nature'],
    ['places', 'abstract'],
    ['colors', 'emotions'],
    ['adjectives', 'emotions'],
  ],
  ambient: [
    ['abstract', 'nature'],
    ['adjectives', 'emotions'],
    ['colors', 'abstract'],
    ['times', 'nature'],
    ['actions', 'nature'],
    ['adjectives', 'abstract'],
    ['nature', 'emotions'],
    ['times', 'abstract'],
    ['colors', 'nature'],
    ['adjectives', 'places'],
  ],
  house: [
    ['adjectives', 'emotions'],
    ['colors', 'abstract'],
    ['times', 'musical'],
    ['actions', 'emotions'],
    ['adjectives', 'musical'],
    ['times', 'emotions'],
    ['colors', 'places'],
    ['abstract', 'emotions'],
    ['adjectives', 'abstract'],
    ['actions', 'abstract'],
  ],
  tropical: [
    ['adjectives', 'nature'],
    ['colors', 'places'],
    ['times', 'nature'],
    ['nature', 'emotions'],
    ['adjectives', 'emotions'],
    ['colors', 'nature'],
    ['times', 'places'],
    ['actions', 'nature'],
    ['adjectives', 'places'],
    ['nature', 'abstract'],
  ],
  chillout: [
    ['adjectives', 'places'],
    ['times', 'emotions'],
    ['colors', 'abstract'],
    ['abstract', 'places'],
    ['adjectives', 'emotions'],
    ['times', 'places'],
    ['nature', 'emotions'],
    ['colors', 'places'],
    ['actions', 'abstract'],
    ['adjectives', 'abstract'],
    ['times', 'abstract'],
    ['nature', 'places'],
  ],
  electroswing: [
    ['adjectives', 'musical'],
    ['times', 'places'],
    ['colors', 'abstract'],
    ['actions', 'emotions'],
    ['adjectives', 'places'],
    ['times', 'emotions'],
    ['colors', 'musical'],
    ['abstract', 'places'],
    ['adjectives', 'abstract'],
    ['actions', 'musical'],
    ['times', 'musical'],
    ['colors', 'emotions'],
  ],
  nudisco: [
    ['adjectives', 'emotions'],
    ['times', 'abstract'],
    ['colors', 'musical'],
    ['actions', 'emotions'],
    ['adjectives', 'places'],
    ['times', 'emotions'],
    ['colors', 'abstract'],
    ['abstract', 'emotions'],
    ['adjectives', 'musical'],
    ['actions', 'abstract'],
    ['times', 'places'],
    ['colors', 'emotions'],
  ],
  latin: [
    ['adjectives', 'places'],
    ['times', 'nature'],
    ['colors', 'emotions'],
    ['nature', 'abstract'],
    ['adjectives', 'emotions'],
    ['times', 'places'],
    ['colors', 'places'],
    ['abstract', 'nature'],
    ['adjectives', 'abstract'],
    ['actions', 'nature'],
    ['times', 'emotions'],
    ['nature', 'emotions'],
  ],
  default: [
    ['adjectives', 'emotions'],
    ['times', 'places'],
    ['colors', 'abstract'],
    ['nature', 'musical'],
    ['actions', 'nature'],
    ['adjectives', 'places'],
    ['times', 'emotions'],
    ['colors', 'places'],
    ['abstract', 'emotions'],
    ['nature', 'places'],
  ]
};

// In-memory cache of used titles (loaded from file on startup)
let usedTitles: Set<string> = new Set();
let titlesLoaded = false;

/**
 * Load used titles from persistent storage
 */
function loadUsedTitles(): void {
  if (titlesLoaded) return;

  try {
    if (existsSync(USED_TITLES_FILE)) {
      const data = JSON.parse(readFileSync(USED_TITLES_FILE, 'utf-8'));
      usedTitles = new Set(data.titles || []);
    }
  } catch (error) {
    console.warn('Warning: Could not load used titles, starting fresh');
    usedTitles = new Set();
  }

  titlesLoaded = true;
}

/**
 * Save used titles to persistent storage
 */
function saveUsedTitles(): void {
  try {
    if (!existsSync(DATA_DIR)) {
      mkdirSync(DATA_DIR, { recursive: true });
    }

    const data = {
      lastUpdated: new Date().toISOString(),
      count: usedTitles.size,
      titles: Array.from(usedTitles)
    };

    writeFileSync(USED_TITLES_FILE, JSON.stringify(data, null, 2));
  } catch (error) {
    console.warn('Warning: Could not save used titles:', (error as Error).message);
  }
}

/**
 * Get a random element from an array
 */
function randomChoice<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

/**
 * Get vocabulary for a category, including cultural words if applicable
 */
function getVocabulary(category: string, genre: string): string[] {
  const lowerGenre = genre.toLowerCase();
  const baseVocab = VOCABULARY[category as keyof typeof VOCABULARY];

  if (Array.isArray(baseVocab)) {
    // Add cultural vocabulary for specific genres
    if (category === 'abstract' || category === 'adjectives' || category === 'nature') {
      if (lowerGenre.includes('chinese') || lowerGenre.includes('asian') || lowerGenre.includes('oriental')) {
        return [...baseVocab, ...VOCABULARY.cultural.asian];
      }
      if (lowerGenre.includes('jazz') || lowerGenre.includes('lounge') || lowerGenre.includes('cafe')) {
        return [...baseVocab, ...VOCABULARY.cultural.jazz];
      }
      if (lowerGenre.includes('ambient')) {
        return [...baseVocab, ...VOCABULARY.cultural.ambient];
      }
      if (lowerGenre.includes('soulful') && lowerGenre.includes('house')) {
        return [...baseVocab, ...VOCABULARY.cultural.house];
      }
      if (lowerGenre.includes('tropical')) {
        return [...baseVocab, ...VOCABULARY.cultural.tropical];
      }
      if (lowerGenre.includes('chillout') || lowerGenre.includes('chill-out') || lowerGenre.includes('downtempo') || lowerGenre.includes('buddha') || lowerGenre.includes('balearic')) {
        return [...baseVocab, ...VOCABULARY.cultural.chillout];
      }
      if (lowerGenre.includes('electro') && lowerGenre.includes('swing') || lowerGenre.includes('electroswing') || lowerGenre.includes('swing house') || lowerGenre.includes('neo swing')) {
        return [...baseVocab, ...VOCABULARY.cultural.electroswing];
      }
      if (lowerGenre.includes('nu disco') || lowerGenre.includes('nudisco') || lowerGenre.includes('nu-disco') || lowerGenre.includes('indie dance') || lowerGenre.includes('disco house')) {
        return [...baseVocab, ...VOCABULARY.cultural.nudisco];
      }
      if (lowerGenre.includes('latin') || lowerGenre.includes('bossa') || lowerGenre.includes('salsa') || lowerGenre.includes('afro') || lowerGenre.includes('cuban') || lowerGenre.includes('brazilian')) {
        return [...baseVocab, ...VOCABULARY.cultural.latin];
      }
    }
    return baseVocab;
  }

  return [];
}

/**
 * Get the appropriate patterns for a genre
 */
function getPatterns(genre: string): string[][] {
  const lowerGenre = genre.toLowerCase();

  if (lowerGenre.includes('jazz')) return GENRE_PATTERNS.jazz;
  if (lowerGenre.includes('chinese') || lowerGenre.includes('asian') || lowerGenre.includes('oriental')) return GENRE_PATTERNS.chinese;
  if (lowerGenre.includes('lounge')) return GENRE_PATTERNS.lounge;
  if (lowerGenre.includes('cafe') || lowerGenre.includes('coffee')) return GENRE_PATTERNS.cafe;
  if (lowerGenre.includes('ambient')) return GENRE_PATTERNS.ambient;
  if (lowerGenre.includes('house') || lowerGenre.includes('soulful')) return GENRE_PATTERNS.house;
  if (lowerGenre.includes('chillout') || lowerGenre.includes('chill-out') || lowerGenre.includes('downtempo') || lowerGenre.includes('buddha') || lowerGenre.includes('balearic')) return GENRE_PATTERNS.chillout;
  if (lowerGenre.includes('tropical')) return GENRE_PATTERNS.tropical;
  if (lowerGenre.includes('electro') && lowerGenre.includes('swing') || lowerGenre.includes('electroswing') || lowerGenre.includes('swing house') || lowerGenre.includes('neo swing')) return GENRE_PATTERNS.electroswing;
  if (lowerGenre.includes('nu disco') || lowerGenre.includes('nudisco') || lowerGenre.includes('nu-disco') || lowerGenre.includes('indie dance') || lowerGenre.includes('disco house')) return GENRE_PATTERNS.nudisco;
  if (lowerGenre.includes('latin') || lowerGenre.includes('bossa') || lowerGenre.includes('salsa') || lowerGenre.includes('afro') || lowerGenre.includes('cuban') || lowerGenre.includes('brazilian')) return GENRE_PATTERNS.latin;

  return GENRE_PATTERNS.default;
}

/**
 * Generate a single title (without uniqueness check)
 */
function generateSingleTitle(genre: string): string {
  const patterns = getPatterns(genre);
  const pattern = randomChoice(patterns);

  const parts: string[] = [];
  const usedWords = new Set<string>();

  for (const category of pattern) {
    const vocab = getVocabulary(category, genre);
    if (vocab.length > 0) {
      // Try to pick a word not already used in this title
      let word: string;
      let attempts = 0;
      do {
        word = randomChoice(vocab);
        attempts++;
      } while (usedWords.has(word.toLowerCase()) && attempts < 10);

      usedWords.add(word.toLowerCase());
      parts.push(word);
    }
  }

  // Occasionally add a third word for variety (30% chance)
  if (Math.random() < 0.3 && parts.length === 2) {
    const extraCategories = ['adjectives', 'nature', 'abstract', 'emotions'];
    const extraCategory = randomChoice(extraCategories);
    const vocab = getVocabulary(extraCategory, genre);
    if (vocab.length > 0) {
      let word: string;
      let attempts = 0;
      do {
        word = randomChoice(vocab);
        attempts++;
      } while (usedWords.has(word.toLowerCase()) && attempts < 10);

      if (!usedWords.has(word.toLowerCase())) {
        // Insert at random position
        const pos = Math.floor(Math.random() * (parts.length + 1));
        parts.splice(pos, 0, word);
      }
    }
  }

  return parts.join(' ');
}

/**
 * Set the title prefix (default: "MU")
 */
export function setTitlePrefix(prefix: string): void {
  titlePrefix = prefix;
}

/**
 * Get the current title prefix
 */
export function getTitlePrefix(): string {
  return titlePrefix;
}

/**
 * Generate a unique title that hasn't been used before
 * Returns format: "MU - Title Words"
 */
export function generateUniqueTitle(genre: string, _mood?: string, _atmosphere?: string): string {
  loadUsedTitles();

  let attempts = 0;
  const maxAttempts = 1000; // More attempts since we have huge vocabulary

  while (attempts < maxAttempts) {
    const baseTitle = generateSingleTitle(genre);
    const fullTitle = `${titlePrefix} - ${baseTitle}`;
    const titleKey = fullTitle.toLowerCase();

    if (!usedTitles.has(titleKey)) {
      usedTitles.add(titleKey);
      saveUsedTitles();
      return fullTitle;
    }

    attempts++;
  }

  // This should be extremely rare with 2000+ vocabulary
  // If it happens, generate a unique combination using timestamp
  const timestamp = Date.now().toString(36);
  const baseTitle = generateSingleTitle(genre);
  const uniqueTitle = `${titlePrefix} - ${baseTitle} ${timestamp}`;
  usedTitles.add(uniqueTitle.toLowerCase());
  saveUsedTitles();

  console.warn(`Warning: Had to use timestamp suffix after ${maxAttempts} attempts. Consider expanding vocabulary.`);
  return uniqueTitle;
}

/**
 * Generate multiple unique titles at once
 */
export function generateUniqueTitles(count: number, genre: string): string[] {
  const titles: string[] = [];

  for (let i = 0; i < count; i++) {
    titles.push(generateUniqueTitle(genre));
  }

  return titles;
}

/**
 * Check if a title has been used
 */
export function isTitleUsed(title: string): boolean {
  loadUsedTitles();
  return usedTitles.has(title.toLowerCase());
}

/**
 * Get the count of used titles
 */
export function getUsedTitleCount(): number {
  loadUsedTitles();
  return usedTitles.size;
}

/**
 * Reset the used titles tracker (USE WITH CAUTION - will allow duplicate titles)
 */
export function resetTitleTracker(): void {
  usedTitles.clear();
  saveUsedTitles();
}

/**
 * Get vocabulary statistics
 */
export function getVocabularyStats(): { category: string; count: number }[] {
  const stats: { category: string; count: number }[] = [];

  for (const [key, value] of Object.entries(VOCABULARY)) {
    if (Array.isArray(value)) {
      stats.push({ category: key, count: value.length });
    } else if (typeof value === 'object') {
      // Cultural subcategories
      for (const [subKey, subValue] of Object.entries(value)) {
        if (Array.isArray(subValue)) {
          stats.push({ category: `cultural.${subKey}`, count: subValue.length });
        }
      }
    }
  }

  return stats;
}

/**
 * Get total vocabulary size
 */
export function getTotalVocabularySize(): number {
  let total = 0;

  for (const value of Object.values(VOCABULARY)) {
    if (Array.isArray(value)) {
      total += value.length;
    } else if (typeof value === 'object') {
      for (const subValue of Object.values(value)) {
        if (Array.isArray(subValue)) {
          total += subValue.length;
        }
      }
    }
  }

  return total;
}

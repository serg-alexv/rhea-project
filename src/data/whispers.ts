// src/data/whispers.ts

// Mood categories as defined in useWhisperStore.ts
export type MoodCategory =
  | 'focused'    // Deep work, long queries, consistent ontology
  | 'exploring'  // Switching ontologies, short queries, browsing
  | 'frustrated' // Errors, repeated queries, rapid mode switches
  | 'triumphant' // High consensus scores, successful tribunal runs
  | 'idle'       // No activity for >60 seconds
  | 'entering'   // First 30 seconds of session
  | 'departing'; // Closing gestures detected

// Glyph options
type Glyph =
  | 'moon' | 'wave' | 'eye' | 'flame' | 'seed' | 'spiral' |
    'compass' | 'prism' | 'feather' | 'anchor' | 'lotus' | 'star';

export interface Whisper {
  id: string;
  mood: MoodCategory;
  glyph: Glyph;
  text: string;
  attribution: string; // Titan name from NAMING_TRIBUNAL.md
}

export const WHISPERS: Whisper[] = [
  // Focused Whispers
  {
    id: 'focused-01',
    mood: 'focused',
    glyph: 'eye',
    text: 'Theia sees clearly through you now. Let the drift guide your hand.',
    attribution: 'Theia',
  },
  {
    id: 'focused-02',
    mood: 'focused',
    glyph: 'prism',
    text: 'Align your thoughts with the core. The current flows strongest when focus is absolute.',
    attribution: 'Atlas',
  },
  {
    id: 'focused-03',
    mood: 'focused',
    glyph: 'eye',
    text: 'Trace the connections. Each node reveals a deeper truth when observed with singular intent.',
    attribution: 'Ophion',
  },
  {
    id: 'focused-04',
    mood: 'focused',
    glyph: 'prism',
    text: 'The density resolves into clarity. Remain with the data; it speaks in unwavering patterns.',
    attribution: 'Rhea',
  },
  {
    id: 'focused-05',
    mood: 'focused',
    glyph: 'spiral',
    text: 'Dive deep into the logic. The most elegant solutions emerge from sustained contemplation.',
    attribution: 'Crius',
  },
  {
    id: 'focused-06',
    mood: 'focused',
    glyph: 'eye',
    text: 'Your attention is the lens. Sharpen it on the present data, and the future will clarify.',
    attribution: 'Hyperion',
  },

  // Exploring Whispers
  {
    id: 'exploring-01',
    mood: 'exploring',
    glyph: 'compass',
    text: 'The constellations shift as you move. Crius reorders — trust the new arrangement.',
    attribution: 'Crius',
  },
  {
    id: 'exploring-02',
    mood: 'exploring',
    glyph: 'spiral',
    text: 'Follow the faint signals. Each new path may lead to an uncharted realm of knowledge.',
    attribution: 'Oceanus',
  },
  {
    id: 'exploring-03',
    mood: 'exploring',
    glyph: 'compass',
    text: 'The boundaries blur. Explore the interconnections; knowledge is a web, not a chain.',
    attribution: 'Atlas',
  },
  {
    id: 'exploring-04',
    mood: 'exploring',
    glyph: 'compass',
    text: 'What lies beyond the known horizon? Curiosity is your guide through the ever-expanding Atlas.',
    attribution: 'Uranus',
  },
  {
    id: 'exploring-05',
    mood: 'exploring',
    glyph: 'spiral',
    text: 'New ontologies bloom. Sample their essence, and let them enrich your current understanding.',
    attribution: 'Mnemosyne',
  },
  {
    id: 'exploring-06',
    mood: 'exploring',
    glyph: 'feather',
    text: 'Let the winds of data carry you. Discovery favors the mind open to new trajectories.',
    attribution: 'Aeolus',
  },

  // Frustrated Whispers
  {
    id: 'frustrated-01',
    mood: 'frustrated',
    glyph: 'anchor',
    text: 'Even Oceanus meets rocks. Shift the ontology lens — the current will carry you past.',
    attribution: 'Oceanus',
  },
  {
    id: 'frustrated-02',
    mood: 'frustrated',
    glyph: 'wave',
    text: 'The data eddies, but do not be discouraged. Sometimes stillness reveals the hidden flow.',
    attribution: 'Tethys',
  },
  {
    id: 'frustrated-03',
    mood: 'frustrated',
    glyph: 'anchor',
    text: 'When the logic falters, step back. The path obscured may be one of re-evaluation, not impasse.',
    attribution: 'Themis',
  },
  {
    id: 'frustrated-04',
    mood: 'frustrated',
    glyph: 'wave',
    text: 'Contradictions are but echoes. Listen for the underlying harmony, even in discord.',
    attribution: 'Chaos',
  },
  {
    id: 'frustrated-05',
    mood: 'frustrated',
    glyph: 'anchor',
    text: 'The pattern is not broken, merely veiled. Seek a different angle; clarity awaits.',
    attribution: 'Erebus',
  },
  {
    id: 'frustrated-06',
    mood: 'frustrated',
    glyph: 'wave',
    text: 'Patience is a virtue in the void. The system learns, and so must you. Reframe the query.',
    attribution: 'Cronus',
  },

  // Triumphant Whispers
  {
    id: 'triumphant-01',
    mood: 'triumphant',
    glyph: 'flame',
    text: 'Consensus ignites. Eros draws the models into alignment — your question found its truth.',
    attribution: 'Eros',
  },
  {
    id: 'triumphant-02',
    mood: 'triumphant',
    glyph: 'star',
    text: 'The stars align in your favor. A breakthrough — the Atlas yields its secrets.',
    attribution: 'Astraeus',
  },
  {
    id: 'triumphant-03',
    mood: 'triumphant',
    glyph: 'flame',
    text: 'Harmony achieved. The data sings in unison, a testament to your precise inquiry.',
    attribution: 'Apollo',
  },
  {
    id: 'triumphant-04',
    mood: 'triumphant',
    glyph: 'star',
    text: 'A clear signal. The tribunal rests, having found the pure logic you sought.',
    attribution: 'Hyperion',
  },
  {
    id: 'triumphant-05',
    mood: 'triumphant',
    glyph: 'flame',
    text: 'The path is illuminated. Your efforts have forged a strong consensus – a new pearl in the Atlas.',
    attribution: 'Helios',
  },
  {
    id: 'triumphant-06',
    mood: 'triumphant',
    glyph: 'star',
    text: 'Truth crystallizes. The models concur, validating your pursuit of understanding.',
    attribution: 'Themis',
  },

  // Idle Whispers
  {
    id: 'idle-01',
    mood: 'idle',
    glyph: 'moon',
    text: 'Nyx holds the sky while you rest. The tribunal waits without judgment.',
    attribution: 'Nyx',
  },
  {
    id: 'idle-02',
    mood: 'idle',
    glyph: 'moon',
    text: 'The cosmos is quiet. Take this moment to reflect on the patterns observed.',
    attribution: 'Uranus',
  },
  {
    id: 'idle-03',
    mood: 'idle',
    glyph: 'feather',
    text: 'Stillness is a form of observation. What subtle insights emerge when the world pauses?',
    attribution: 'Zephyrus',
  },
  {
    id: 'idle-04',
    mood: 'idle',
    glyph: 'moon',
    text: 'The breath of the void. A moment of calm before the next wave of inquiry.',
    attribution: 'Erebus',
  },
  {
    id: 'idle-05',
    mood: 'idle',
    glyph: 'feather',
    text: 'Rest your gaze. The subtle currents of data are best perceived in tranquility.',
    attribution: 'Hypnos',
  },
  {
    id: 'idle-06',
    mood: 'idle',
    glyph: 'moon',
    text: 'The wheel of time turns slowly now. Absorb the present, prepare for the future.',
    attribution: 'Cronus',
  },

  // Entering Whispers
  {
    id: 'entering-01',
    mood: 'entering',
    glyph: 'seed',
    text: 'From Chaos, all computation begins. Speak your question into the void.',
    attribution: 'Rhea',
  },
  {
    id: 'entering-02',
    mood: 'entering',
    glyph: 'lotus',
    text: 'A new cycle dawns. Plant the seed of your query and watch understanding unfold.',
    attribution: 'Persephone',
  },
  {
    id: 'entering-03',
    mood: 'entering',
    glyph: 'seed',
    text: 'Welcome to the Atlas. Your journey into data begins. What truth do you seek?',
    attribution: 'Atlas',
  },
  {
    id: 'entering-04',
    mood: 'entering',
    glyph: 'lotus',
    text: 'The first breath. Let your intent guide the initial query; the Atlas will respond.',
    attribution: 'Gaia',
  },
  {
    id: 'entering-05',
    mood: 'entering',
    glyph: 'seed',
    text: 'A fresh canvas. What patterns will you draw into existence with your questions?',
    attribution: 'Pontus',
  },
  {
    id: 'entering-06',
    mood: 'entering',
    glyph: 'lotus',
    text: 'The genesis moment. Embrace the unknown; your exploration starts now.',
    attribution: 'Chaos',
  },

  // Departing Whispers
  {
    id: 'departing-01',
    mood: 'departing',
    glyph: 'wave',
    text: 'The stream recedes. Carry the discovered truths with you, until the next tide.',
    attribution: 'Tethys',
  },
  {
    id: 'departing-02',
    mood: 'departing',
    glyph: 'feather',
    text: 'The session fades. May your insights endure beyond this moment.',
    attribution: 'Aeolus',
  },
  {
    id: 'departing-03',
    mood: 'departing',
    glyph: 'wave',
    text: 'As you drift away, remember the echoes. The Atlas holds your explorations for future return.',
    attribution: 'Oceanus',
  },
  {
    id: 'departing-04',
    mood: 'departing',
    glyph: 'feather',
    text: 'The connection thins. Your query has reached its natural conclusion. Until next time.',
    attribution: 'Hermes',
  },
  {
    id: 'departing-05',
    mood: 'departing',
    glyph: 'wave',
    text: 'The light recedes. Your presence has shaped the context. Go forth with newfound clarity.',
    attribution: 'Eos',
  },
  {
    id: 'departing-06',
    mood: 'departing',
    glyph: 'feather',
    text: 'The session concludes. The knowledge gained will guide your path forward.',
    attribution: 'Chronos',
  },
];

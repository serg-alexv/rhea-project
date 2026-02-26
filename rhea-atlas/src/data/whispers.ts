export type MoodCategory =
  | 'focused'
  | 'exploring'
  | 'frustrated'
  | 'triumphant'
  | 'idle'
  | 'entering'
  | 'departing';

export type WhisperGlyph =
  | 'moon'
  | 'wave'
  | 'eye'
  | 'flame'
  | 'seed'
  | 'spiral'
  | 'compass'
  | 'prism'
  | 'feather'
  | 'anchor'
  | 'lotus'
  | 'star';

export interface Whisper {
  id: string;
  mood: MoodCategory;
  glyph: WhisperGlyph;
  text: string;
  attribution: string;
}

type WhisperSeed = Omit<Whisper, 'id' | 'mood'>;

const WHISPER_SEEDS: Record<MoodCategory, WhisperSeed[]> = {
  focused: [
    { glyph: 'eye', text: 'You have narrowed the field. Keep one ontology steady and let the evidence thicken.', attribution: 'Theia' },
    { glyph: 'prism', text: 'You are splitting noise from structure. Stay with the strongest beam for one more pass.', attribution: 'Phoebe' },
    { glyph: 'eye', text: 'The drift is no longer wandering. You can refine the question now without losing the thread.', attribution: 'Mnemosyne' },
    { glyph: 'prism', text: 'You are already inside the useful layer. Trim the query, not the ambition.', attribution: 'Rhea' },
    { glyph: 'star', text: 'Your target star is visible. Test one contradiction before you move to the next cluster.', attribution: 'Themis' },
    { glyph: 'lotus', text: 'You do not need more motion yet. Let this result settle and annotate the important edge.', attribution: 'Tethys' },
    { glyph: 'eye', text: 'The panel field is aligned. Use the same lens again and compare only one variable.', attribution: 'Crius' },
    { glyph: 'prism', text: 'You are in deep work now. Preserve the current rhythm and harvest evidence while it is coherent.', attribution: 'Hyperion' },
  ],
  exploring: [
    { glyph: 'compass', text: 'You are charting, not concluding. Rotate the ontology lens and watch which cluster brightens.', attribution: 'Crius' },
    { glyph: 'spiral', text: 'The map is widening around you. Follow the new branch, but leave a marker in the old one.', attribution: 'Mnemosyne' },
    { glyph: 'wave', text: 'You are moving through currents of possibility. Let two models disagree before you pick a shore.', attribution: 'Oceanus' },
    { glyph: 'compass', text: 'This is a scouting pass. Short queries and fast comparisons will teach you the terrain.', attribution: 'Rhea' },
    { glyph: 'spiral', text: 'You are reordering constellations. Keep the question loose, but record what repeats.', attribution: 'Phoebe' },
    { glyph: 'feather', text: 'Exploration works best when the touch is light. Sample the edge case and return with one fact.', attribution: 'Iapetus' },
    { glyph: 'compass', text: 'You are not lost. You are still measuring the shape of the problem space.', attribution: 'Themis' },
    { glyph: 'prism', text: 'Try a neighboring mode and compare outputs side by side. The pattern will reveal itself.', attribution: 'Hyperion' },
  ],
  frustrated: [
    { glyph: 'anchor', text: 'You hit resistance, not failure. Drop anchor, shorten the query, and test one clean path.', attribution: 'Oceanus' },
    { glyph: 'wave', text: 'The current is choppy because too many switches happened at once. Hold one mode for two turns.', attribution: 'Tethys' },
    { glyph: 'anchor', text: 'You are pushing against the wrong layer. Change the ontology lens before repeating the same prompt.', attribution: 'Phoebe' },
    { glyph: 'wave', text: 'The system can feel noisy when the evidence is thin. Ask for a narrower claim and rebuild upward.', attribution: 'Rhea' },
    { glyph: 'anchor', text: 'A failed step still teaches direction. Keep the useful fragments and discard only the phrasing.', attribution: 'Themis' },
    { glyph: 'flame', text: 'Do not fight the panel field. Minimize what you are not using and restore your line of sight.', attribution: 'Hyperion' },
    { glyph: 'wave', text: 'Rapid mode switching can mimic chaos. Pick one tribunal path, then compare the next run deliberately.', attribution: 'Mnemosyne' },
    { glyph: 'anchor', text: 'You have enough signal to recover. Start from the last strong result and move one hypothesis at a time.', attribution: 'Crius' },
  ],
  triumphant: [
    { glyph: 'flame', text: 'You found alignment. Capture the claim now before you widen the search again.', attribution: 'Eros' },
    { glyph: 'star', text: 'The models converged around your question. This is the moment to extract evidence, not celebrate only.', attribution: 'Themis' },
    { glyph: 'flame', text: 'Consensus is bright and rare. Save a memory map snapshot while the structure is clean.', attribution: 'Mnemosyne' },
    { glyph: 'star', text: 'You pulled a true signal from the drift. Compare one rival framing to confirm the edge.', attribution: 'Hyperion' },
    { glyph: 'flame', text: 'The tribunal is agreeing with you now. Turn this into a reusable query pattern.', attribution: 'Rhea' },
    { glyph: 'star', text: 'This cluster just tightened. Mark the star, then map its planets as concrete examples.', attribution: 'Crius' },
    { glyph: 'flame', text: 'Your question landed well. Preserve the ontology and iterate with a sharper scope.', attribution: 'Phoebe' },
    { glyph: 'star', text: 'The path is open. Convert momentum into notes, evidence, and a next-step test.', attribution: 'Chronos' },
  ],
  idle: [
    { glyph: 'moon', text: 'You are allowed to pause. The tribunal keeps its place while you return to breath.', attribution: 'Nyx' },
    { glyph: 'feather', text: 'Stillness is part of the method. When you return, begin with the last active star.', attribution: 'Mnemosyne' },
    { glyph: 'moon', text: 'The panels have gone quiet, but the map remains. Tap any slot and the field will wake with you.', attribution: 'Rhea' },
    { glyph: 'feather', text: 'No urgency is lost here. Resume with one query and let the drift reassemble.', attribution: 'Tethys' },
    { glyph: 'moon', text: 'The night mode is gentle on purpose. Your context is resting, not disappearing.', attribution: 'Nyx' },
    { glyph: 'lotus', text: 'When you return, start from memory before speed. The strongest path is usually already visible.', attribution: 'Phoebe' },
    { glyph: 'feather', text: 'Quiet intervals sharpen interpretation. Re-enter by comparing only two results first.', attribution: 'Themis' },
    { glyph: 'moon', text: 'The system waits without judgment. Continue when the question becomes precise again.', attribution: 'Hyperion' },
  ],
  entering: [
    { glyph: 'seed', text: 'You are entering a fresh field. Begin with one honest question and one clear target.', attribution: 'Rhea' },
    { glyph: 'lotus', text: 'Start small and let the map grow around evidence. You do not need the final form yet.', attribution: 'Mnemosyne' },
    { glyph: 'seed', text: 'The first query sets the rhythm. Choose the ontology lens before you chase speed.', attribution: 'Phoebe' },
    { glyph: 'compass', text: 'You are at the threshold. Pick a direction, then let the tribunal test your footing.', attribution: 'Crius' },
    { glyph: 'lotus', text: 'Welcome back to the field. Stabilize the panels first, then open the research line.', attribution: 'Hyperion' },
    { glyph: 'seed', text: 'A good beginning is narrow and curious. Name the domain, then ask for one contradiction.', attribution: 'Themis' },
    { glyph: 'prism', text: 'You are about to shape the drift. Keep your first prompt simple enough to compare.', attribution: 'Theia' },
    { glyph: 'seed', text: 'From a single seed, the graph can grow. Plant one useful query and observe the response.', attribution: 'Oceanus' },
  ],
  departing: [
    { glyph: 'star', text: 'Before you go, mark the brightest result. Tomorrow you will thank the note you leave now.', attribution: 'Mnemosyne' },
    { glyph: 'anchor', text: 'You can stop here cleanly. Save the star, preserve the planets, and let the rest drift.', attribution: 'Themis' },
    { glyph: 'feather', text: 'Close lightly. One final summary line is often better than another full query.', attribution: 'Nyx' },
    { glyph: 'moon', text: 'The field will hold your place. Leave one breadcrumb for the path you want to resume.', attribution: 'Rhea' },
    { glyph: 'anchor', text: 'A deliberate exit is part of the experiment. Capture what changed and what remains uncertain.', attribution: 'Chronos' },
    { glyph: 'star', text: 'You have enough for this session. Convert momentum into a next task while the shape is clear.', attribution: 'Hyperion' },
    { glyph: 'lotus', text: 'Let the interface quiet down with you. Keep only the panels you need for re-entry.', attribution: 'Tethys' },
    { glyph: 'feather', text: 'You are not abandoning the question. You are storing it in a form your future self can trust.', attribution: 'Phoebe' },
  ],
};

for (const mood of Object.keys(WHISPER_SEEDS) as MoodCategory[]) {
  if (WHISPER_SEEDS[mood].length !== 8) {
    throw new Error(`Mnemosyne whisper library invalid for ${mood}: expected 8 items, got ${WHISPER_SEEDS[mood].length}`);
  }
}

export const WHISPERS: Whisper[] = (Object.keys(WHISPER_SEEDS) as MoodCategory[]).flatMap((mood) =>
  WHISPER_SEEDS[mood].map((seed, index) => ({
    ...seed,
    id: `${mood}-${String(index + 1).padStart(2, '0')}`,
    mood,
  })),
);

export const WHISPERS_BY_MOOD: Record<MoodCategory, Whisper[]> = {
  focused: [],
  exploring: [],
  frustrated: [],
  triumphant: [],
  idle: [],
  entering: [],
  departing: [],
};

for (const whisper of WHISPERS) {
  WHISPERS_BY_MOOD[whisper.mood].push(whisper);
}

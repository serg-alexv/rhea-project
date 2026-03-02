import { create } from 'zustand';
import { useAtlasStore, AtlasState, SessionEntry } from '@/store/useAtlasStore';
import { WHISPERS_BY_MOOD, MoodCategory, Whisper } from '@/data/whispers';

interface WhisperAction {
  type: 'query' | 'error' | 'mode-switch' | 'dismiss' | 'milestone';
  timestamp: number;
}

interface WhisperState {
  current: Whisper | null;
  queue: Whisper[];
  currentMood: MoodCategory;
  lastMoodChangeAt: number;
  lastShownAt: number;
  recentActions: WhisperAction[];
  visible: boolean;
  sessionStartedAt: number;
  highConsensusSeen: number;
  shownIds: string[];
  recordQuery: (entry?: SessionEntry | null) => void;
  recordError: () => void;
  recordModeSwitch: () => void;
  evaluateFromAtlas: (atlas: AtlasState) => void;
  showWhisperForMood: (mood: MoodCategory, reason?: WhisperAction['type']) => void;
  dismissCurrent: () => void;
  dequeueNext: () => void;
}

const MOOD_DEBOUNCE_MS = 10_000;
const AUTO_DISMISS_MS = 8_000;
const IDLE_TRIGGER_MS = 90_000;
const RECENT_WINDOW_MS = 180_000;
const MAX_QUEUE = 2;

let autoDismissTimer: ReturnType<typeof setTimeout> | null = null;
let idlePollTimer: ReturnType<typeof setInterval> | null = null;
let initialized = false;

function clearAutoTimer() {
  if (autoDismissTimer) {
    clearTimeout(autoDismissTimer);
    autoDismissTimer = null;
  }
}

function trimActions(actions: WhisperAction[], now: number): WhisperAction[] {
  return actions.filter((a) => now - a.timestamp <= RECENT_WINDOW_MS).slice(-30);
}

function maybeExtractConsensus(entry?: SessionEntry | null): number | null {
  if (!entry?.result) return null;
  const text = entry.result;
  const direct = text.match(/agreement:\s*(\d{1,3})%/i);
  if (direct) return Number(direct[1]);
  const consensus = text.match(/consensus[^\d]*(\d{1,3})/i);
  if (consensus) return Number(consensus[1]);
  return null;
}

export function detectMood(state: AtlasState, recentActions: WhisperAction[], sessionStartedAt: number): MoodCategory {
  const now = Date.now();
  const actions = trimActions(recentActions, now);
  const errorCount = actions.filter((a) => a.type === 'error').length;
  const queryCount = actions.filter((a) => a.type === 'query').length;
  const modeSwitchCount = actions.filter((a) => a.type === 'mode-switch').length;
  const lastQueryTs = [...actions].reverse().find((a) => a.type === 'query')?.timestamp ?? 0;
  const lastActionTs = actions[actions.length - 1]?.timestamp ?? sessionStartedAt;
  const lastQueryAge = lastQueryTs ? now - lastQueryTs : now - sessionStartedAt;
  const idleAge = now - lastActionTs;
  const sessionAge = now - sessionStartedAt;

  if (idleAge > IDLE_TRIGGER_MS) return 'idle';
  if (sessionAge < 30_000 && queryCount <= 2) return 'entering';
  if (errorCount > 2 && queryCount < 4) return 'frustrated';
  if (state.consensusScore > 90 && queryCount > 0) return 'triumphant';
  if (queryCount > 5 && modeSwitchCount < Math.max(2, queryCount / 2)) return 'focused';
  if (modeSwitchCount >= 3 || queryCount <= 2) return 'exploring';
  if (lastQueryAge > 60_000) return 'idle';
  return 'exploring';
}

function pickWhisper(mood: MoodCategory, shownIds: string[]): Whisper {
  const pool = WHISPERS_BY_MOOD[mood];
  const unseen = pool.filter((w) => !shownIds.includes(w.id));
  const source = unseen.length ? unseen : pool;
  const idx = Math.floor(Math.random() * source.length);
  return source[idx];
}

function scheduleAutoDismiss() {
  clearAutoTimer();
  autoDismissTimer = setTimeout(() => {
    useWhisperStore.getState().dismissCurrent();
  }, AUTO_DISMISS_MS);
}

export const useWhisperStore = create<WhisperState>((set, get) => ({
  current: null,
  queue: [],
  currentMood: 'entering',
  lastMoodChangeAt: 0,
  lastShownAt: 0,
  recentActions: [],
  visible: false,
  sessionStartedAt: Date.now(),
  highConsensusSeen: 0,
  shownIds: [],

  recordQuery: (entry) => {
    const now = Date.now();
    set((state) => {
      const actions = trimActions([...state.recentActions, { type: 'query', timestamp: now }], now);
      const parsed = maybeExtractConsensus(entry);
      const highConsensusSeen = parsed && parsed > state.highConsensusSeen ? parsed : state.highConsensusSeen;
      return { recentActions: actions, highConsensusSeen };
    });
    const atlas = useAtlasStore.getState();
    get().evaluateFromAtlas(atlas);
    if (entry && maybeExtractConsensus(entry) && (maybeExtractConsensus(entry) ?? 0) >= 90) {
      get().showWhisperForMood('triumphant', 'milestone');
    }
  },

  recordError: () => {
    const now = Date.now();
    set((state) => ({
      recentActions: trimActions([...state.recentActions, { type: 'error', timestamp: now }], now),
    }));
    get().evaluateFromAtlas(useAtlasStore.getState());
  },

  recordModeSwitch: () => {
    const now = Date.now();
    set((state) => ({
      recentActions: trimActions([...state.recentActions, { type: 'mode-switch', timestamp: now }], now),
    }));
    get().evaluateFromAtlas(useAtlasStore.getState());
  },

  evaluateFromAtlas: (atlas) => {
    const now = Date.now();
    const state = get();
    const mood = detectMood(atlas, state.recentActions, state.sessionStartedAt);
    if (mood !== state.currentMood) {
      const tooSoon = now - state.lastMoodChangeAt < MOOD_DEBOUNCE_MS;
      set({ currentMood: mood, lastMoodChangeAt: now });
      if (!tooSoon) get().showWhisperForMood(mood, 'milestone');
      return;
    }
    if (!state.visible && mood === 'idle' && now - state.lastShownAt > MOOD_DEBOUNCE_MS) {
      get().showWhisperForMood('idle', 'milestone');
    }
  },

  showWhisperForMood: (mood) => {
    const now = Date.now();
    const state = get();
    if (state.visible && state.queue.length >= MAX_QUEUE) return;
    const whisper = pickWhisper(mood, state.shownIds);

    if (state.visible && state.current) {
      set((prev) => ({
        queue: [...prev.queue, whisper].slice(0, MAX_QUEUE),
        shownIds: [...prev.shownIds, whisper.id].slice(-200),
      }));
      return;
    }

    set((prev) => ({
      current: whisper,
      visible: true,
      lastShownAt: now,
      shownIds: [...prev.shownIds, whisper.id].slice(-200),
    }));
    scheduleAutoDismiss();
  },

  dismissCurrent: () => {
    clearAutoTimer();
    set((state) => ({
      current: null,
      visible: false,
      recentActions: trimActions([...state.recentActions, { type: 'dismiss', timestamp: Date.now() }], Date.now()),
    }));
    const queued = get().queue;
    if (queued.length) {
      setTimeout(() => get().dequeueNext(), 120);
    }
  },

  dequeueNext: () => {
    const state = get();
    if (state.visible || state.queue.length === 0) return;
    const [next, ...rest] = state.queue;
    set({ current: next, queue: rest, visible: true, lastShownAt: Date.now() });
    scheduleAutoDismiss();
  },
}));

function initWhisperBridge() {
  if (initialized) return;
  initialized = true;

  let prevSessionLen = useAtlasStore.getState().sessionHistory.length;
  let prevConsensus = useAtlasStore.getState().consensusScore;

  useAtlasStore.subscribe((atlas) => {
    const state = useWhisperStore.getState();
    if (atlas.sessionHistory.length > prevSessionLen) {
      state.recordQuery(atlas.sessionHistory[0]);
      prevSessionLen = atlas.sessionHistory.length;
    }
    if (atlas.consensusScore > prevConsensus && atlas.consensusScore >= 90) {
      state.showWhisperForMood('triumphant', 'milestone');
      prevConsensus = atlas.consensusScore;
    } else {
      prevConsensus = atlas.consensusScore;
    }
    state.evaluateFromAtlas(atlas);
  });

  idlePollTimer = setInterval(() => {
    useWhisperStore.getState().evaluateFromAtlas(useAtlasStore.getState());
  }, 15_000);
}

initWhisperBridge();

export function __stopWhisperTimersForTests() {
  clearAutoTimer();
  if (idlePollTimer) {
    clearInterval(idlePollTimer);
    idlePollTimer = null;
  }
  initialized = false;
}

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

// Import necessary types from other modules
import { MoodCategory, Whisper, WHISPERS } from '../data/whispers';
import useAtlasStore, { AtlasState } from './useAtlasStore'; // Import actual AtlasState

// --- Action type for mood detection ---
interface Action {
  type: string; // e.g., 'query', 'error', 'milestone', 'session_start', 'view_change'
  timestamp: number;
}

// --- Mood Detection Logic ---
// This function determines the user's mood based on recent activity and system state.

const MAX_ACTIONS_HISTORY = 50; // Limit history to keep it manageable
let recentActionsHistory: Action[] = []; // Store actions to track user activity

function addActionToHistory(action: Action) {
  recentActionsHistory.unshift(action); // Add to the beginning
  if (recentActionsHistory.length > MAX_ACTIONS_HISTORY) {
    recentActionsHistory.pop(); // Remove the oldest action
  }
}

function detectMood(currentAtlasState: AtlasState): MoodCategory {
  const errorCount = recentActionsHistory.filter(a => a.type === 'error').length;
  const queryCount = recentActionsHistory.filter(a => a.type === 'query').length;
  const lastQueryTimestamp = recentActionsHistory.find(a => a.type === 'query')?.timestamp ?? 0;
  const lastQueryAge = Date.now() - lastQueryTimestamp;

  // --- Mood Heuristics (as per IMPLEMENTATION_SPEC.md) ---

  // Frustrated: Multiple errors without significant query progress
  if (errorCount > 2 && queryCount < 4 && lastQueryAge < 60_000) return 'frustrated';

  // Triumphant: High consensus score achieved with some activity
  if (currentAtlasState.consensusScore > 90 && queryCount > 0) return 'triumphant';

  // Idle: No activity for a while
  if (lastQueryAge > 60_000) return 'idle'; // 60 seconds

  // Focused: Many queries indicating deep work
  if (queryCount > 5) return 'focused';

  // Entering: Very few queries, early in session
  if (queryCount <= 2 && lastQueryAge < 30_000) return 'entering'; // Within first 30s

  // Default/Exploring: Anything else, suggesting general browsing or moderate activity
  return 'exploring';
}


// --- Whisper Store ---

interface WhisperStoreState {
  currentWhisper: Whisper | null;
  whisperQueue: Whisper[];
  mood: MoodCategory;
  lastMoodChangeTime: number;
  lastActionTime: number;
  isShowingWhisper: boolean;

  // Actions
  addWhisperToQueue: (whisper: Whisper) => void;
  showNextWhisper: () => void;
  dismissWhisper: () => void;
  updateMood: (currentAtlasState: AtlasState) => void; // Accept actual AtlasState
  recordAction: (actionType: Action['type']) => void;
  autoDismissTimer: NodeJS.Timeout | null;
  clearAutoDismissTimer: () => void;
}

const useWhisperStore = create<WhisperStoreState>()(
  devtools(
    persist(
      immer((set, get) => ({
        currentWhisper: null,
        whisperQueue: [],
        mood: 'entering', // Initial mood
        lastMoodChangeTime: Date.now(),
        lastActionTime: Date.now(),
        isShowingWhisper: false,
        autoDismissTimer: null,

        // --- Actions ---
        addWhisperToQueue: (whisper: Whisper) => {
          set(state => {
            state.whisperQueue.push(whisper);
            // If no whisper is currently showing, try to show the next one
            if (!state.isShowingWhisper) {
              get().showNextWhisper();
            }
          });
        },

        showNextWhisper: () => {
          const { whisperQueue, currentWhisper, isShowingWhisper, autoDismissTimer } = get();

          if (isShowingWhisper || whisperQueue.length === 0) {
            return;
          }

          if (autoDismissTimer) {
            clearTimeout(autoDismissTimer);
            set({ autoDismissTimer: null });
          }

          set(state => {
            const nextWhisper = state.whisperQueue.shift();
            if (nextWhisper) {
              state.currentWhisper = nextWhisper;
              state.isShowingWhisper = true;
              // Set auto-dismiss timer (8 seconds as per spec)
              const timer = setTimeout(() => {
                get().dismissWhisper();
              }, 8000);
              state.autoDismissTimer = timer;
            }
          });
        },

        dismissWhisper: () => {
          set(state => {
            state.currentWhisper = null;
            state.isShowingWhisper = false;
            state.autoDismissTimer = null;
            get().showNextWhisper(); // Try to show next in queue
          });
        },

        updateMood: (currentAtlasState: AtlasState) => {
          const newMood = detectMood(currentAtlasState);
          const { mood: currentMood, lastMoodChangeTime, isShowingWhisper, whisperQueue } = get();
          const currentTime = Date.now();
          const MOOD_CHANGE_DEBOUNCE_MS = 10000; // 10 seconds

          if (newMood !== currentMood && (currentTime - lastMoodChangeTime > MOOD_CHANGE_DEBOUNCE_MS)) {
            set(state => {
              state.mood = newMood;
              state.lastMoodChangeTime = currentTime;
              // If mood changes and no whisper is showing, try to show one for the new mood
              if (!state.isShowingWhisper && whisperQueue.length === 0) {
                const relevantWhispers = WHISPERS.filter(w => w.mood === newMood);
                if (relevantWhispers.length > 0) {
                  const randomWhisper = relevantWhispers[Math.floor(Math.random() * relevantWhispers.length)];
                  state.whisperQueue.push(randomWhisper);
                  get().showNextWhisper();
                }
              }
            });
          }
        },

        recordAction: (actionType: Action['type']) => {
          const currentTime = Date.now();
          addActionToHistory({ type: actionType, timestamp: currentTime });
          set({ lastActionTime: currentTime });
          // Re-evaluate mood after action
          // Get the actual AtlasState to pass to updateMood
          const atlasState = useAtlasStore.getState(); // Accessing zustand store state directly
          get().updateMood(atlasState);
        },

        clearAutoDismissTimer: () => {
          const { autoDismissTimer } = get();
          if (autoDismissTimer) {
            clearTimeout(autoDismissTimer);
            set({ autoDismissTimer: null });
          }
        },
      })),
      {
        name: 'whisper-storage',
      }
    ),
    { name: 'WhisperStore' }
  )
);

// Export helper to get the current mood and actions
export const useWhisperState = (selector: (state: WhisperStoreState) => any) => {
  const state = useWhisperStore(selector);
  return state;
};

export default useWhisperStore;

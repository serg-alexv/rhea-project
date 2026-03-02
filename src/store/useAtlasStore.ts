import { create } from 'zustand';

// Placeholder for Vector3 if not globally available or imported elsewhere
// In a real project, you'd likely import this from a 3D library like three.js
// For example: import { Vector3 } from 'three';
type Vector3 = any;

// Define ViewId as per spec
type ViewId = 'atlas-prime' | 'atlas-mesh' | 'theia-drift' | 'system-pw';

// Define ContextDensity interface as per spec
interface ContextDensity {
  id: string;
  label: string;                    // e.g. "cancer medicine", "weed shops"
  density: number;                  // 0.0 (vapor) → 1.0 (solid)
  consistency: number;              // 0.0 (contradictory) → 1.0 (aligned)
  vectorField: Vector3[];           // Directional flow arrows
  color: string;                    // Derived from ontology/mood
  position: [number, number, number]; // 3D placement
}

// Define AtlasState including existing and new properties
interface AtlasState {
  // Existing state from PHASE 1a
  activeView: ViewId;
  setActiveView: (v: ViewId) => void;

  // New state from PHASE 1b
  contextDensities: ContextDensity[];
  setContextDensities: (d: ContextDensity[]) => void;
  showOceanusFlow: boolean;
  toggleOceanusFlow: () => void;

  // ... other states will be added in subsequent phases
}

const useAtlasStore = create<AtlasState>((set) => ({
  // Initial state for PHASE 1a
  activeView: 'atlas-prime', // Default view
  setActiveView: (v: ViewId) => set({ activeView: v }),

  // Initial state for PHASE 1b
  contextDensities: [],
  setContextDensities: (d: ContextDensity[]) => set({ contextDensities: d }),
  showOceanusFlow: false, // Default to false, toggled later
  toggleOceanusFlow: () => set((state) => ({ showOceanusFlow: !state.showOceanusFlow })),

  // ... other state initializations
}));

export default useAtlasStore;


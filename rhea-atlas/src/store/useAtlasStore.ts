import { create } from 'zustand';

interface Island {
  id: string;
  name: string;
  position: [number, number, number];
  complexity: number; // D-Metric
  color: string;
}

interface AtlasState {
  islands: Island[];
  consensusScore: number;
  dMetric: number;
  activeIslandId: string | null;
  setIslands: (islands: Island[]) => void;
  updateIsland: (id: string, delta: Partial<Island>) => void;
  setDMetric: (d: number) => void;
  setActiveIsland: (id: string | null) => void;
}

export const useAtlasStore = create<AtlasState>((set) => ({
  islands: [
    { id: '1', name: 'Biology', position: [-3, 0, 0], complexity: 1.2, color: '#00ff00' },
    { id: '2', name: 'Mathematics', position: [3, 0, 0], complexity: 0.8, color: '#00ffff' },
  ],
  consensusScore: 94,
  dMetric: 243.8,
  activeIslandId: null,
  setIslands: (islands) => set({ islands }),
  updateIsland: (id, delta) => set((state) => ({
    islands: state.islands.map((is) => is.id === id ? { ...is, ...delta } : is)
  })),
  setDMetric: (d) => set({ dMetric: d }),
  setActiveIsland: (id) => set({ activeIslandId: id }),
}));

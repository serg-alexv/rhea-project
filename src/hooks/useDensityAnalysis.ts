import { create } from 'zustand';
import { Vector3 } from 'three'; // Assuming three.js for Vector3

// --- Mock/Helper Types and Functions ---
// These would typically be imported from other modules.
// Mocking them here for self-containment as per the spec's intent.

interface SessionEntry {
  id: string;
  ontology: string;
  result: {
    consensus_score: number;
    // ... other properties from tribunal results
  };
  timestamp: number;
  label?: string; // Optional label for context
}

interface ContextDensity {
  id: string;
  label: string;                    // e.g. "cancer medicine", "weed shops"
  density: number;                  // 0.0 (vapor) → 1.0 (solid)
  consistency: number;              // 0.0 (contradictory) → 1.0 (aligned)
  vectorField: Vector3[];           // Directional flow arrows
  color: string;                    // Derived from ontology/mood
  position: [number, number, number]; // 3D placement
}

function mean(arr: number[]): number {
  if (arr.length === 0) return 0;
  return arr.reduce((sum, val) => sum + val, 0) / arr.length;
}

function standardDeviation(arr: number[]): number {
  if (arr.length < 2) return 0;
  const m = mean(arr);
  // Using sample standard deviation (n-1)
  const variance = arr.reduce((sum, val) => sum + Math.pow(val - m, 2), 0) / (arr.length - 1);
  return Math.sqrt(variance);
}

function groupBy<T>(list: T[], getKey: (item: T) => string): Record<string, T[]> {
  return list.reduce((acc, item) => {
    const key = getKey(item);
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(item);
    return acc;
  }, {} as Record<string, T[]>);
}

function extractConsensusScore(result: any): number {
  // Placeholder: In a real app, this would extract the score from the result object
  return result?.consensus_score ?? 0;
}

const ONTOLOGY_COLOR_MAP: Record<string, string> = {
  'pharmacology': '#10b981', // emerald
  'biochemistry': '#f59e0b', // amber
  'logic': '#8b5cf6', // violet
  'topology': '#f43f5e', // rose
  'systems biology': '#6366f1', // indigo
  'general': '#06b6d4', // cyan
};

// Mock function to map a label (like 'cancer medicine') to an ontology key
function getOntologyKeyForLabel(label: string): string {
  const lowerLabel = label.toLowerCase();
  if (lowerLabel.includes('cancer') || lowerLabel.includes('medicine')) return 'pharmacology';
  if (lowerLabel.includes('shop') || lowerLabel.includes('retail')) return 'general';
  // Add more mappings as needed for other ontologies
  return 'general'; // Default ontology
}

// --- Density Analysis Store ---

interface DensityAnalysisState {
  sessions: SessionEntry[];
  contextDensities: ContextDensity[];
  updateSessions: (newSessions: SessionEntry[]) => void;
  computeDensity: () => void;
}

const useDensityAnalysis = create<DensityAnalysisState>((set, get) => ({
  sessions: [],
  contextDensities: [],

  updateSessions: (newSessions: SessionEntry[]) => {
    set({ sessions: newSessions });
    // Recompute density immediately after sessions update
    get().computeDensity();
  },

  computeDensity: () => {
    const { sessions } = get();
    if (sessions.length === 0) {
      set({ contextDensities: [] });
      return;
    }

    // Cluster sessions by ontology derived from session label/ontology
    const clusters = groupBy(sessions, s => getOntologyKeyForLabel(s.label ?? s.ontology ?? 'general'));

    const computedDensities: ContextDensity[] = [];

    Object.entries(clusters).forEach(([ontologyKey, entries], index) => {
      if (entries.length === 0) return;

      const scores = entries.map(e => extractConsensusScore(e.result));
      const avgScore = mean(scores);
      const variance = standardDeviation(scores);

      // Density calculation: based on number of sessions and average consensus
      // Scale factor 10 and 100 are empirical, adjust as needed
      const density = Math.min(1.0, (entries.length / 10) * (avgScore / 100));
      // Consistency calculation: inversely related to variance
      const consistency = Math.max(0.0, 1.0 - variance / 50); // Max variance of 50 maps to consistency 0

      // Vector field: temporal gradient of scores (simplified)
      const vectors: Vector3[] = scores.map((s, i) => {
        const nextScore = scores[i + 1] ?? s;
        const scoreChange = nextScore - s;
        const magnitude = Math.abs(scoreChange);
        // Simplified vector direction and magnitude calculation
        // This can be made more sophisticated based on temporal or semantic relationships
        const direction = new Vector3(
          Math.cos(i * 0.5) * scoreChange * 0.1,
          Math.sin(i * 0.5) * scoreChange * 0.1,
          scoreChange * 0.05 // Z component for temporal progression?
        );
        return direction.normalize().multiplyScalar(magnitude);
      });

      const baseColor = ONTOLOGY_COLOR_MAP[ontologyKey] || ONTOLOGY_COLOR_MAP['general'];
      // Modulate color saturation based on consistency (e.g., higher consistency = more vivid)
      // This is a simplified approach; a real implementation might use HSL color manipulation
      const saturationFactor = consistency; // 0 = desaturated, 1 = vivid
      const finalColor = colorWithSaturation(baseColor, saturationFactor); // Function to adjust saturation

      computedDensities.push({
        id: `density-${index}-${ontologyKey}`,
        label: entries[0].label || ontologyKey, // Use provided label or ontology key
        density: density,
        consistency: consistency,
        vectorField: vectors,
        color: finalColor,
        position: [
          Math.sin(index * 0.5) * 5, // Distribute horizontally
          -2, // Fixed Y position below islands as per spec
          Math.cos(index * 0.5) * 5
        ],
      });
    });

    // Sort by density (highest first) for rendering priority
    computedDensities.sort((a, b) => b.density - a.density);

    set({ contextDensities: computedDensities });
  },
}));

// Helper function for color saturation (example implementation)
function colorWithSaturation(hex: string, factor: number): string {
  // Basic method: adjust brightness/saturation. More advanced would use HSL.
  // For simplicity, let's just make it slightly dimmer if consistency is low.
  if (factor >= 0.8) return hex;
  if (factor < 0.5) return hex.replace(/([0-9A-F]{2})/g, (match) => {
      const val = parseInt(match, 16);
      return Math.floor(val * (0.5 + factor * 0.5)).toString(16).padStart(2, '0');
  });
  return hex;
}


export default useDensityAnalysis;

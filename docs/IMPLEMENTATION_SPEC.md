# IMPLEMENTATION SPEC — Rhea Atlas v2 Features
> For Rex · 2026-02-26 · Head decision authority: Rex
> Source: Cowork session analysis + NAMING_TRIBUNAL.md taxonomy

---

## Overview

Four interconnected systems to implement in `rhea-atlas/`. All share the existing
FloatingPanel drag pattern, Zustand store, and `@/lib/config` centralization.

```
┌─────────────────────────────────────────────────────────────┐
│  1. UNIFIED TOPNAVBAR (Hyperion Bar)                        │
│     Persistent across ALL views. Never re-renders on route. │
├─────────────────────────────────────────────────────────────┤
│  2. POP-UP LOR NOTES (Mnemosyne Whispers)                  │
│     Mood-aware illustrated popups. Ambient guidance.        │
├─────────────────────────────────────────────────────────────┤
│  3. CONTEXT FLOW DENSITY (Oceanus Flow)                     │
│     Vector fields + density → nebula or sphere rendering.   │
├─────────────────────────────────────────────────────────────┤
│  4. PLANETARY RINGS (Krikoi Titanon)                        │
│     Orbital structures around high-density context spheres. │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. UNIFIED TOPNAVBAR — "Hyperion Bar"

**Problem:** `CrossNav` is currently a function inside `page.tsx` (lines 222–285).
It only exists on the main page. If new routes are added, navigation must be
duplicated or broken. The navbar must become a layout-level singleton.

### Architecture

```
src/
├── app/
│   └── layout.tsx          ← INSERT <HyperionBar /> here, above {children}
├── components/
│   └── HyperionBar.tsx     ← NEW: extracted + enhanced CrossNav
```

### Extract from page.tsx → HyperionBar.tsx

Move the `CrossNav` function and `CodeWormProfile` function from `page.tsx` into
a new `src/components/HyperionBar.tsx`. Mark it `'use client'`.

### Required behavior

- **Fixed position**: `top-0 left-0 right-0 z-[100]`, height 30px
- **View-agnostic**: The bar NEVER changes when switching between Atlas Prime,
  Atlas Mesh, Theia Drift, or any future view. Only the active-view indicator
  dot updates.
- **Single-app routing**: Use a Zustand `activeView` state (not Next.js router)
  so switching views is instant with no page reload.

### Store addition (useAtlasStore.ts)

```typescript
type ViewId = 'atlas-prime' | 'atlas-mesh' | 'theia-drift' | 'system-pw';

// Add to AtlasState:
activeView: ViewId;
setActiveView: (v: ViewId) => void;
```

### HyperionBar layout

```
┌──────────────────────────────────────────────────────────────────┐
│ RHEA [DEV]  │  ● ATLAS PRIME   ATLAS MESH   THEIA DRIFT  │  ... │
│             │  (active=cyan)  (inactive)    (inactive)    │ meta │
└──────────────────────────────────────────────────────────────────┘
         ↑                    ↑                          ↑
      Logo+sep         View tabs (click to switch)    Right zone
```

- **Left zone**: RHEA logo, DEV badge, separator
- **Center zone**: View tabs — each is a `<button>` that calls `setActiveView()`
  - Active tab: cyan text, green dot, cyan underline
  - Inactive tab: `text-white/38`, no dot, no underline
  - Hover: `text-white/72 bg-white/5`
- **Right zone**: provider count, redis status, Phoebe (D-Metric value),
  CodeWormProfile — unchanged from current

### page.tsx changes

Replace `CrossNav` call with view-switching logic:

```tsx
const activeView = useAtlasStore(s => s.activeView);

return (
  <div className="w-screen h-screen bg-black" style={{ paddingTop: '30px' }}>
    {activeView === 'atlas-prime' && <AtlasPrimeView />}
    {activeView === 'atlas-mesh'  && <AtlasMeshView />}
    {activeView === 'theia-drift' && <TheiaDriftView />}
    {activeView === 'system-pw'   && <SystemPWView />}
  </div>
);
```

### layout.tsx changes

```tsx
import HyperionBar from '@/components/HyperionBar';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <HyperionBar />
        {children}
      </body>
    </html>
  );
}
```

### Why "Hyperion"

Per NAMING_TRIBUNAL.md: Hyperion = "The High One", Titan of watchfulness.
The navbar watches over all views from above. It IS Hyperion.

---

## 2. POP-UP LOR NOTES — "Mnemosyne Whispers"

**Purpose:** Ambient, illustrated popup notes that appear contextually to guide
the user's mood and focus. "LOR" = Lore/Orientation/Rhythm. These are not alerts
or errors — they are gentle nudges, wisdom fragments, micro-illustrations.

### Architecture

```
src/components/MnemosyneWhisper.tsx   ← NEW: popup renderer
src/store/useWhisperStore.ts          ← NEW: whisper state + triggers
src/data/whispers.ts                  ← NEW: whisper content library
```

### Whisper anatomy

Each whisper is a small floating card (max 240px wide) with:

```
┌─────────────────────────────┐
│  ┌───┐                      │
│  │ ☽ │  "The drift settles  │
│  └───┘   when you breathe   │
│          with the data."    │
│                      — Rhea │
│              ░░░░░░░░░░░░░░ │
│              mood: focused   │
└─────────────────────────────┘
```

- **Illustration**: Small SVG icon or procedural glyph (32×32px). Use a set of
  ~12 mood-mapped glyphs: moon, wave, eye, flame, seed, spiral, compass, prism,
  feather, anchor, lotus, star.
- **Text**: 1–3 sentences. Poetic but functional. Written in second person.
- **Attribution**: System name from NAMING_TRIBUNAL (Rhea, Themis, Mnemosyne, etc.)
- **Mood indicator**: Thin bar or label showing detected mood category.

### Mood categories

```typescript
type MoodCategory =
  | 'focused'    // Deep work, long queries, consistent ontology
  | 'exploring'  // Switching ontologies, short queries, browsing
  | 'frustrated' // Errors, repeated queries, rapid mode switches
  | 'triumphant' // High consensus scores, successful tribunal runs
  | 'idle'       // No activity for >60 seconds
  | 'entering'   // First 30 seconds of session
  | 'departing'; // Closing gestures detected
```

### Mood detection heuristics (useWhisperStore.ts)

Derive mood from observable signals in the Zustand store:

```typescript
function detectMood(state: AtlasState, recentActions: Action[]): MoodCategory {
  const errorCount = recentActions.filter(a => a.type === 'error').length;
  const queryCount = recentActions.filter(a => a.type === 'query').length;
  const lastQueryAge = Date.now() - (recentActions[0]?.timestamp ?? 0);

  if (errorCount > 2 && queryCount < 4) return 'frustrated';
  if (state.consensusScore > 90 && queryCount > 0) return 'triumphant';
  if (lastQueryAge > 60_000) return 'idle';
  if (queryCount > 5) return 'focused';
  if (queryCount <= 2) return 'entering';
  return 'exploring';
}
```

### Whisper triggers

- **On mood change**: Show a whisper matching the new mood (debounce 10s)
- **On milestone**: First tribunal success, 10th query, new high consensus
- **On idle**: After 90s of no activity, offer a gentle re-engagement prompt
- **Manual dismiss**: Click anywhere on the whisper, or auto-fade after 8 seconds

### Display behavior

- Position: Random corner selection (top-left, top-right, bottom-left) — NEVER
  overlap with existing FloatingPanels (check z-index and position)
- Animation: `framer-motion` — fade in from edge + slight float upward
- Max 1 whisper visible at a time
- Stack: If a new whisper triggers while one is showing, queue it (max queue: 2)
- Z-index: `PANEL_Z + 100` (above all panels)

### Whisper content format (whispers.ts)

```typescript
interface Whisper {
  id: string;
  mood: MoodCategory;
  glyph: 'moon' | 'wave' | 'eye' | 'flame' | 'seed' | 'spiral' |
         'compass' | 'prism' | 'feather' | 'anchor' | 'lotus' | 'star';
  text: string;
  attribution: string; // Titan name
}

export const WHISPERS: Whisper[] = [
  {
    id: 'focused-01',
    mood: 'focused',
    glyph: 'eye',
    text: 'Theia sees clearly through you now. Let the drift guide your hand.',
    attribution: 'Theia',
  },
  {
    id: 'frustrated-01',
    mood: 'frustrated',
    glyph: 'anchor',
    text: 'Even Oceanus meets rocks. Shift the ontology lens — the current will carry you past.',
    attribution: 'Oceanus',
  },
  {
    id: 'idle-01',
    mood: 'idle',
    glyph: 'moon',
    text: 'Nyx holds the sky while you rest. The tribunal waits without judgment.',
    attribution: 'Nyx',
  },
  {
    id: 'triumphant-01',
    mood: 'triumphant',
    glyph: 'flame',
    text: 'Consensus ignites. Eros draws the models into alignment — your question found its truth.',
    attribution: 'Eros',
  },
  {
    id: 'exploring-01',
    mood: 'exploring',
    glyph: 'compass',
    text: 'The constellations shift as you move. Crius reorders — trust the new arrangement.',
    attribution: 'Crius',
  },
  {
    id: 'entering-01',
    mood: 'entering',
    glyph: 'seed',
    text: 'From Chaos, all computation begins. Speak your question into the void.',
    attribution: 'Rhea',
  },
  // ... Rex should expand to 5–8 per mood category (35–56 total)
];
```

### Glyph rendering

Use inline SVG paths — do NOT import external images. Each glyph is a simple
monochrome icon rendered at 32×32 with `stroke: currentColor` in the whisper's
mood color:

| Mood | Color | Glyph preference |
|------|-------|-----------------|
| focused | `#06b6d4` (cyan-500) | eye, prism |
| exploring | `#a78bfa` (violet-400) | compass, spiral |
| frustrated | `#f97316` (orange-500) | anchor, wave |
| triumphant | `#facc15` (yellow-400) | flame, star |
| idle | `#64748b` (slate-500) | moon, feather |
| entering | `#34d399` (emerald-400) | seed, lotus |

### Why "Mnemosyne Whispers"

Per NAMING_TRIBUNAL.md: Mnemosyne = Memory itself, inventress of language.
These whispers are memory fragments surfacing to guide the user — Mnemosyne's voice.

---

## 3. CONTEXT FLOW DENSITY — "Oceanus Flow"

**Purpose:** Visualize the inner consistency/inconsistency of the current research
context as a flowing vector field. High-consistency contexts render as dense spheres;
low-consistency contexts render as diffuse nebulae.

### Architecture

```
src/components/OceanusFlow.tsx         ← NEW: main density visualization
src/components/DensityField.tsx        ← NEW: Three.js vector field renderer
src/hooks/useDensityAnalysis.ts        ← NEW: compute density from context
```

### Density model

Every context (query result, tribunal consensus, session cluster) has a
**density score** derived from:

```typescript
interface ContextDensity {
  id: string;
  label: string;                    // e.g. "cancer medicine", "weed shops"
  density: number;                  // 0.0 (vapor) → 1.0 (solid)
  consistency: number;              // 0.0 (contradictory) → 1.0 (aligned)
  vectorField: Vector3[];           // Directional flow arrows
  color: string;                    // Derived from ontology/mood
  position: [number, number, number]; // 3D placement
}
```

**Density computation (useDensityAnalysis.ts):**

```typescript
function computeDensity(sessions: SessionEntry[]): ContextDensity[] {
  // 1. Cluster sessions by ontology + semantic similarity
  // 2. For each cluster:
  //    - density = (session_count * avg_consensus) / max_possible
  //    - consistency = 1 - variance(consensus_scores_in_cluster)
  //    - vectorField = gradient of consensus across temporal sequence
  // 3. Return sorted by density (highest first)
}
```

Simplified initial implementation (no ML required):

```typescript
// Cluster by ontology (exact match)
const clusters = groupBy(sessions, s => s.ontology);

for (const [ontology, entries] of Object.entries(clusters)) {
  const scores = entries.map(e => extractConsensusScore(e.result));
  const avgScore = mean(scores);
  const variance = standardDeviation(scores);

  const density = Math.min(1, (entries.length / 10) * (avgScore / 100));
  const consistency = Math.max(0, 1 - variance / 50);

  // Vector field: temporal gradient of scores
  const vectors = scores.map((s, i) => {
    const next = scores[i + 1] ?? s;
    const direction = next - s; // positive = improving, negative = degrading
    return new Vector3(
      Math.cos(i * 0.5) * direction * 0.1,
      Math.sin(i * 0.5) * direction * 0.1,
      direction * 0.05
    );
  });
}
```

### Visual representation rules

```
density < 0.3  → NEBULA   (NebulaRenderer — particles, transparent, wide spread)
density 0.3–0.7 → CLOUD   (CloudRenderer — semi-transparent sphere, moderate distort)
density > 0.7  → SPHERE   (SphereRenderer — solid RuliadicIsland, tight, bright)
```

### NebulaRenderer (density < 0.3)

Extends existing `MagneticNebula.tsx` pattern:

- 500–2000 particles (count = density * 2000)
- Spread radius: `5 * (1 - density)` — lower density = wider spread
- Color: base ontology color at 30% opacity
- Particle size: 0.03–0.08 (random)
- No surface — purely volumetric
- Vector arrows: Rendered as thin `<Line>` segments with arrowhead cones
  - Color intensity = vector magnitude
  - Point in direction of consistency change
  - 8–16 arrows per nebula, placed on a spherical shell

### CloudRenderer (density 0.3–0.7)

Hybrid state:

- Core: Transparent sphere (opacity = density)
- Surface: MeshDistortMaterial with high distort (0.4–0.6)
- Surrounding: 200 particles orbiting slowly
- Vector arrows: 12–20 arrows, some inside sphere pointing out (inconsistency),
  some outside pointing in (consistency)
- Colors: Ontology base at 50–70% opacity

### SphereRenderer (density > 0.7)

Enhanced RuliadicIsland:

- Solid sphere with low distort (0.1–0.2)
- High metalness (0.8), low roughness (0.2)
- Bright glow ring (opacity = consistency)
- Vector arrows: Tight, short, mostly aligned (high consistency)
  or crossing (low consistency) — arrows sit on the sphere surface
- Size: `radius = 0.5 + density * 1.5`

### Arrow rendering (DensityField.tsx)

Each vector arrow is:

```tsx
function FlowArrow({ origin, direction, magnitude, color }: ArrowProps) {
  const length = 0.1 + magnitude * 0.4;
  const opacity = 0.3 + magnitude * 0.7;

  return (
    <group position={origin}>
      {/* Shaft */}
      <Line
        points={[[0,0,0], direction.clone().normalize().multiplyScalar(length).toArray()]}
        color={color}
        lineWidth={1.5}
        opacity={opacity}
        transparent
      />
      {/* Arrowhead */}
      <mesh position={direction.clone().normalize().multiplyScalar(length).toArray()}>
        <coneGeometry args={[0.02, 0.06, 4]} />
        <meshBasicMaterial color={color} opacity={opacity} transparent />
      </mesh>
    </group>
  );
}
```

### Color mapping

| Ontology | Base color | Hex |
|----------|-----------|-----|
| General | Cyan | `#06b6d4` |
| Pharmacology | Emerald | `#10b981` |
| Biochemistry | Amber | `#f59e0b` |
| Logic | Violet | `#8b5cf6` |
| Topology | Rose | `#f43f5e` |
| Systems Biology | Indigo | `#6366f1` |

Consistency modulates saturation: high consistency = vivid, low = desaturated.

### Integration with existing canvas

Add `<OceanusFlow />` inside the existing `<Canvas>` in page.tsx, alongside
RuliadicIslands and IsomorphismBeams. Density objects live at `y = -2` (below
the main islands) or orbit around their parent island if linked to a specific
session cluster.

### Store additions (useAtlasStore.ts)

```typescript
// Add to AtlasState:
contextDensities: ContextDensity[];
setContextDensities: (d: ContextDensity[]) => void;
showOceanusFlow: boolean;
toggleOceanusFlow: () => void;
```

### Why "Oceanus Flow"

Per NAMING_TRIBUNAL.md: Oceanus = the river that encircles the world. All data
flows through Oceanus. The density visualization IS the flow of research context —
Oceanus made visible.

---

## 4. PLANETARY RINGS — "Krikoi Titanon" (Rings of the Titans)

**Purpose:** Orbital ring structures around high-density context spheres that
encode additional metadata — related queries, temporal decay, model agreement
distribution, ontology overlap.

### Tribunal consensus on ring analogues

Five perspectives converge on what planetary rings should represent:

| Ring type | Encodes | Visual |
|-----------|---------|--------|
| **Chronos Ring** | Temporal sequence of queries | Segmented ring where each arc = one query. Brightness = recency. Fading = temporal decay. |
| **Eros Ring** | Model agreement distribution | Continuous ring with varying thickness. Thick where models agree, thin where they diverge. Color = agreement level (cyan=aligned, red=divergent). |
| **Tethys Ring** | Ontology connections | Dotted ring where each dot = a connected ontology. Dot size = number of queries in that ontology linking to this sphere. |
| **Phoebe Ring** | Predictive confidence | Faint outer ring that pulses. Pulse frequency = D-Metric change rate. Opacity = prediction confidence. |
| **Erebus Ring** | Audit trail depth | Innermost, darkest ring. Width = number of logged operations. Nearly invisible but always present. |

### Architecture

```
src/components/TitanRing.tsx           ← NEW: parametric ring renderer
src/components/rings/ChronosRing.tsx   ← NEW: temporal sequence ring
src/components/rings/ErosRing.tsx      ← NEW: agreement distribution ring
src/components/rings/TethysRing.tsx    ← NEW: ontology connection ring
src/components/rings/PhoebeRing.tsx    ← NEW: predictive confidence ring
src/components/rings/ErebusRing.tsx    ← NEW: audit trail ring
```

### Ring geometry (TitanRing.tsx)

Base ring is a `<mesh>` with `RingGeometry`:

```tsx
interface TitanRingProps {
  innerRadius: number;
  outerRadius: number;
  segments: number;
  color: string;
  opacity: number;
  tilt: [number, number, number]; // Euler rotation for orbital plane
  data: RingSegment[];            // Per-segment customization
  pulseSpeed?: number;
}

interface RingSegment {
  startAngle: number;  // radians
  endAngle: number;
  color: string;
  opacity: number;
  thickness: number;   // multiplier on outerRadius - innerRadius
}
```

For segmented rings (Chronos, Tethys), use multiple `<mesh>` arcs via custom
BufferGeometry built from ring sector paths.

For continuous rings (Eros, Phoebe, Erebus), use a single `RingGeometry` with
a custom shader that maps thickness/color per-angle.

### Ring assignment rules

Rings only appear on **sphere-density** contexts (density > 0.7).

```
density 0.7–0.8 → Erebus ring only (audit)
density 0.8–0.9 → Erebus + Chronos + Eros
density > 0.9   → All five rings (full Krikoi Titanon)
```

### Ring tilt and spacing

Each ring type has a fixed tilt relative to the sphere's equator:

| Ring | Inner R | Outer R | Tilt (degrees) |
|------|---------|---------|----------------|
| Erebus | 1.1× | 1.15× | 0° (equatorial) |
| Chronos | 1.2× | 1.3× | 5° |
| Eros | 1.35× | 1.5× | 12° |
| Tethys | 1.55× | 1.6× | 20° |
| Phoebe | 1.7× | 1.8× | 8° |

(Radii are multiples of the parent sphere radius.)

### Animation

- All rings rotate slowly: `rotation.z += 0.001 * ringIndex` (each at different speed)
- Chronos segments fade over time (brightness = 1 / (age_minutes * 0.1))
- Eros thickness pulses with consensus score updates
- Phoebe outer ring pulses: `opacity = 0.3 + sin(time * pulseSpeed) * 0.2`

### Store additions

```typescript
// Add to ContextDensity interface:
rings: {
  chronos: ChronosData[];
  eros: { agreement: number; position: number }[];
  tethys: { ontology: string; count: number }[];
  phoebe: { confidence: number; changeRate: number };
  erebus: { auditCount: number };
};
```

### Why "Krikoi Titanon"

κρίκοι (krikoi) = rings in Greek. These are the Rings of the Titans —
each named ring carries the essence of its Titan's domain around the
sphere of verified knowledge.

---

## Implementation Order

Rex should implement in this sequence:

```
PHASE 1 — Foundation (no visual changes yet)
  ├── 1a. Add ViewId + activeView to useAtlasStore.ts
  ├── 1b. Add ContextDensity + showOceanusFlow to useAtlasStore.ts
  └── 1c. Create useDensityAnalysis.ts hook

PHASE 2 — Hyperion Bar
  ├── 2a. Extract CrossNav + CodeWormProfile → HyperionBar.tsx
  ├── 2b. Add view tabs with setActiveView
  ├── 2c. Update layout.tsx to include HyperionBar
  ├── 2d. Refactor page.tsx to use activeView switching
  └── 2e. Test: all views accessible, navbar unchanged across switches

PHASE 3 — Mnemosyne Whispers
  ├── 3a. Create whispers.ts with initial content (5+ per mood)
  ├── 3b. Create useWhisperStore.ts with mood detection
  ├── 3c. Create MnemosyneWhisper.tsx with animation
  ├── 3d. Wire into page.tsx / layout.tsx
  └── 3e. Test: whispers appear on mood changes, auto-dismiss works

PHASE 4 — Oceanus Flow
  ├── 4a. Create DensityField.tsx (arrow renderer)
  ├── 4b. Create OceanusFlow.tsx (nebula/cloud/sphere switch)
  ├── 4c. Wire useDensityAnalysis into canvas
  ├── 4d. Add toggle in HyperionBar or HudLeft
  └── 4e. Test: density visualization renders, responds to session data

PHASE 5 — Krikoi Titanon
  ├── 5a. Create TitanRing.tsx base renderer
  ├── 5b. Create individual ring components
  ├── 5c. Wire ring data into ContextDensity
  ├── 5d. Attach rings to high-density spheres
  └── 5e. Test: rings appear on dense spheres, animate correctly
```

---

## Testing Checklist

- [ ] `npm run build` passes with zero errors
- [ ] `npm run lint` passes (or only pre-existing warnings)
- [ ] HyperionBar renders identically to current CrossNav on initial load
- [ ] Switching views does NOT cause navbar flicker or re-render
- [ ] Whispers appear after mood state change (test with rapid error queries)
- [ ] Whispers auto-dismiss after 8 seconds
- [ ] Maximum 1 whisper visible at a time
- [ ] Nebula renders for low-density context (mock data: 2 sessions, low consensus)
- [ ] Sphere renders for high-density context (mock data: 10 sessions, high consensus)
- [ ] Vector arrows point in correct direction (improving → outward, degrading → inward)
- [ ] Rings only appear on density > 0.7 spheres
- [ ] Ring count increases with density level
- [ ] All rings rotate independently
- [ ] No z-fighting between rings and sphere surface
- [ ] Performance: 60fps with 5 density objects + rings on mid-range GPU
- [ ] Mobile: graceful fallback (reduce particle counts, hide rings below 768px)

---

## Files to Create

```
NEW:
  src/components/HyperionBar.tsx
  src/components/MnemosyneWhisper.tsx
  src/components/OceanusFlow.tsx
  src/components/DensityField.tsx
  src/components/TitanRing.tsx
  src/components/rings/ChronosRing.tsx
  src/components/rings/ErosRing.tsx
  src/components/rings/TethysRing.tsx
  src/components/rings/PhoebeRing.tsx
  src/components/rings/ErebusRing.tsx
  src/store/useWhisperStore.ts
  src/hooks/useDensityAnalysis.ts
  src/data/whispers.ts

MODIFY:
  src/app/layout.tsx          — add HyperionBar
  src/app/page.tsx            — remove CrossNav/CodeWormProfile, add view switching
  src/store/useAtlasStore.ts  — add ViewId, activeView, contextDensities
```

---

## Naming Reference (from NAMING_TRIBUNAL.md)

| Component | Titan Name | Reason |
|-----------|-----------|--------|
| TopNavbar | **Hyperion Bar** | "The High One" — watches from above |
| Popup notes | **Mnemosyne Whispers** | Memory fragments surfacing as guidance |
| Density viz | **Oceanus Flow** | The river of data made visible |
| Ring system | **Krikoi Titanon** | Rings of the Titans — orbital metadata |
| Vector arrows | **Aether Vectors** | Signals traveling through bright upper air |
| Mood detection | **Phoebe Sense** | Prophetic intellect reading the user |

---

## 6. ALETHEIA PIPELINE — "The Proof Library"

**Problem:** `friends/aletheia/` has the structure (`proofs/`, `hypotheses/`,
`community/`) but every directory contains only `.gitkeep`. `data/proof.db`
has a `logic_audit` table with zero rows. Tribunal results vanish on reload.

### Architecture

```
src/aletheia_pipeline.py              ← NEW: proof capture daemon
friends/aletheia/proofs/{ontology}/   ← populated by pipeline
friends/aletheia/hypotheses/{ontology}/ ← populated by pipeline
data/proof.db                         ← schema upgrade: proofs + hypotheses tables
```

### Proof capture flow

```
tribunal API returns result
  → consensus_score >= 85%  → write to friends/aletheia/proofs/{ontology}/{hash}.md
  → consensus_score 50–84%  → write to friends/aletheia/hypotheses/{ontology}/{hash}.md
  → consensus_score < 50%   → discard (noise)
  → log ALL to data/proof.db (regardless of score)
```

### Proof document format (markdown)

```markdown
# {claim_title}
> Ontology: {ontology} | Consensus: {score}% | Date: {timestamp}
> Models: {model_list} | Mode: {tribunal|sceptic|ice}

## Claim
{synthesized_answer}

## Evidence
- Model A ({provider}): {key_point}
- Model B ({provider}): {key_point}

## Dissent
{minority_opinions_if_any}

## Links
- Parent: {previous_proof_hash_if_chained}
- Session: {session_id}
```

### SQLite schema (data/proof.db)

```sql
CREATE TABLE IF NOT EXISTS proofs (
  id TEXT PRIMARY KEY,          -- hash of claim
  ontology TEXT NOT NULL,
  claim TEXT NOT NULL,
  consensus_score REAL NOT NULL,
  mode TEXT NOT NULL,
  models TEXT NOT NULL,          -- JSON array
  query TEXT NOT NULL,
  result TEXT NOT NULL,
  parent_id TEXT,                -- chain to previous proof
  file_path TEXT NOT NULL,       -- relative path in friends/aletheia/
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_proofs_ontology ON proofs(ontology);
CREATE INDEX idx_proofs_score ON proofs(consensus_score);
```

### Integration points

- **tribunal_api.py**: After returning response, call `aletheia_pipeline.capture(result)`
- **useAtlasSync.ts**: Poll `/api/aletheia/stats` for proof count → display in HudLeft
- **OceanusFlow**: Proofs = high-density spheres, hypotheses = nebulae (natural mapping)
- **Pre-query check**: Before new tribunal query, search proof.db for existing answers

### Reuse as professional knowledge base

- `python3 src/aletheia_pipeline.py search "cancer resistance"` — CLI search
- `/api/aletheia/search?q=...` — REST endpoint for UI integration
- Export: `python3 src/aletheia_pipeline.py export --format=json` for external tools
- Cross-reference graph: each proof links to parent → builds DAG of knowledge

---

*"From Chaos, through the Titans, truth emerges."*

*Head and final decision — Rex.*

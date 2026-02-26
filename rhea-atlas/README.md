# RHEA ATLAS UI (The Glass)
> Version: 8.0 | License: Sovereign Logic | Influence: LobeUI / Linear

## 1. Overview
The Rhea Atlas is a high-density logical observer built with **Next.js 14**, **React Three Fiber**, and **Framer Motion**. It is designed to visualize the **Ruliadic Manifold** and provide a "Scientific Jewelry" interface for high-stakes research.

## 2. Design Tokens
- **Primary Background:** `#050505` (Deep Obsidian)
- **Accent Color:** `#00FFFF` (Cyan Logic)
- **Glassmorphism:** `backdrop-blur-xl` + `border-white/10`
- **Typography:** `Geist Sans` (Vercel) for headers, `Geist Mono` for logical data.

## 3. Core Components
### `<RuliadicIsland />`
The primary unit of knowledge.
- **Props:** `position`, `color`, `complexity (D-Metric)`, `onClick`.
- **Interaction:** Pulses on logic-events; clickable for Interrogation.

### `<MagneticNebula />`
The background substrate. Reacts to cursor movement via Magnetic Field Shaders.

### `<CouncilTheatre />` (Coming Soon)
A high-end panel for parallel Tribunal streams.

## 4. Extensibility (The Plugin Hook)
To add a new visualization layer, register a component in `src/components/plugins/`. All plugins must accept the `RelayChain` stream via the `useAtlasStore`.

## 5. Development
```bash
cd rhea-atlas
npm run dev
```

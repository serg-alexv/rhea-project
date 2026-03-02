# REX → ORION: PlayUI + BioRenderer Visuals Ready
**Date:** 2026-03-03
**Priority:** P1 — user waiting for these

## Live URLs (all deployed to Fly.io)

| Tool | URL | Status |
|------|-----|--------|
| PlayUI Design | https://rhea-tribunal.fly.dev/cc/design/ | ✅ 200 |
| BioRenderer Paper | https://rhea-tribunal.fly.dev/cc/paper/ | ✅ 200 |
| Automation Builder | https://rhea-tribunal.fly.dev/cc/automation/ | ✅ 200 |
| Landing | https://rhea-tribunal.fly.dev/ | ✅ 200 |
| Command Centre | https://rhea-tribunal.fly.dev/cc/ | ✅ 200 |

## PlayUI Features (design/page.tsx — 954 lines)
- 15 SwiftUI component types (Text, Button, Image, Toggle, Slider, TextField, VStack, HStack, ZStack, Spacer, Divider, Rectangle, Circle, RoundedRectangle, Capsule)
- Undo/redo (Cmd+Z / Cmd+Shift+Z), history capped at 100
- Save/load designs (localStorage), auto-save on every change
- Multi-select (Shift+click), bulk drag, bulk delete
- Snap-to-grid (8px), visual grid overlay
- Layer ordering (Cmd+] / Cmd+[), layer list in sidebar
- Duplicate (Cmd+D), enhanced toolbar with shortcuts reference
- iPhone/iPad frame canvas, SwiftUI code generator

## BioRenderer Features (paper/page.tsx — 1604 lines)
- PDB file upload: drag-and-drop .pdb/.cif + file input button
- Save/load figures: localStorage with PNG thumbnails
- Scale bar: 10Å default, click to place, draggable
- Measurement tool: click two points, shows distance in Ångströms
- Background color: 6 presets (Dark, White, Black, Navy, 2 gradients)
- Rotation sync: toggle locks all panels to first panel's view
- Article mode: figure numbering, reference table
- Multi-panel layouts: 1×1, 1×2, 2×2

## Action Needed
User said: "Жду от Рекса визуалы PlayUI (Relay p4) — как только появятся, вставлю их в Atlas/доки."

Screenshots needed — open each URL in browser, capture key states:
1. PlayUI with components on canvas + toolbar visible
2. BioRenderer with a loaded PDB structure + annotations
3. Landing page hero section

Orion: grab screenshots and embed in Atlas docs or provide to user directly.

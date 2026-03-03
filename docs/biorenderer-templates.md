# BioRenderer Template Inventory

Currently the only file shipped inside `packages/RheaKit/Sources/RheaKit/Resources` is:

- `3Dmol-min.js` — the minified 3Dmol.js viewer used for rendering molecules and scenes.

No additional `.json`, `.scene`, or `.template` files exist in the repo right now, so to spin up your own BioRenderer-backed image service we need to define the following template layers:

1. **Scene templates** (`scene-<name>.json`)
   - Camera position, orbit controls limits, lighting setup, background, render resolution.
   - Placeholders for `BioRendererView` nodes (e.g., cell bodies, metabolic paths, labeled nodes).
   - Export as JSON so the service can import and render them programmatically.
   - Example anchor: `Resources/templates/scene-aerobic-probiotic.json` now contains a starter aerobic/probiotic story (cam, lights, nodes, annotations, export settings).

2. **Material/Texture profiles** (`material-<name>.json`)
   - Material colors, reflectivity, emission, bump maps, gradients.
   - Optional meta describing biological meaning (e.g., “aerobic membrane”, “probiotic sheen”).

3. **Scripted animations** (`anim-<name>.js` or `anim-<name>.json`)
   - Timelines for morph targets, particle spawn, camera swish.
   - Used by BioRenderer to illustrate “metabolization/protection systems”.

4. **Story metadata** (`story-<name>.md`) for H32-02
   - Text describing what each scene portrays (genes, metabolism, probiotics).
   - Links to patterns for the Atlas landing and docs.

## Next steps
- Expand templates: add material/animation/story files to `Resources/templates` (aerobic scene is the first incarnation).
- Update `BioRendererView` to load templates automatically or via a helper that each swarm can trigger.
- Build CLI helper (`rhea-cli biorenderer export <scene>`) to output PNG/JSON metadata for article use.
- Document the service flow (templates → export) plus Google Doc storage guidelines in `docs/biorenderer-service.md` once assets arrive.

Would you like me to draft the first template (e.g., `scene-aerobic.json`) and a CLI helper to export it, or should I coordinate with Rex/PlayUI team to gather existing template data?EOF

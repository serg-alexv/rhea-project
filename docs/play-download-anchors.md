# Play App Bundle Anchors (Downloads/play)

The unpacked Play macOS bundle at `/Users/sa/Downloads/play` contains the following anchor points useful for the BioRenderer-based services:

1. **Resources directory** (`Resources/...`) – holds assets, config, media, and helper bundles:
   - `GoogleService-Info*.plist` - Firebase configs (DEV/PROD) ➜ use for analytics/messaging signalling.
   - `EnvConfig-*.xcconfig` - environment flag toggles (DEV vs PROD) for enabling services.
   - `PlayAIWebImporter`, `PlayAgentPackage`, `PlayImages`, `PlayMacEditor`, `PlayNodes`, `PlayPlayMode` bundles – these are the Swift bundles that power the PlayUI modules (extract metadata to understand how BioRenderer scenes are structured).
   - `projectTest.json` - sample project metadata (likely includes scene definitions / node graphs) – this is a prime candidate for extracting template settings (camera, nodes, assets).
   - `Playground-1/3.png`, `welcome*.mp4` – hero visuals for onboarding; can be repurposed for Atlas or docs cards.
   - `codeExport.html`, `editor_onboarding_lottie.json`, `confetti.json` – export/animation templates.
   - `Onboarding-iOS.mp4`, `Onboarding-macOS.mp4` – quick examples of runtime experience.

2. **Framework bundles** (`Frameworks/` + `PlugIns/`) – contain compiled Release frameworks; identifying entry points (BioRenderer, editors) helps document what API surfaces exist.

3. **Archive.zip** – zipped data (likely containing scene assets). Unzip and inspect before copying into `packages/RheaKit/Resources/templates`.

4. **MacOS executable** – the Play app binary itself (use to inspect instrumentation or symbol tables if necessary).

## Next steps
- Unzip `Archive.zip` and search for `.json/.scene` files (these can become our BioRenderer templates).
- Extract metadata from `projectTest.json` and map to the template layers (scene, material, animation).
- Use the helper bundles to understand how PlayUI loads nodes and exports assets; we can mimic their structure in new templates.
- Save the relevant assets to `docs/biorenderer-templates.md` references and import them into the planned `Resources/templates` folder.

Need me to unzip `Archive.zip` now and look for actual template files/metadata?"EOF
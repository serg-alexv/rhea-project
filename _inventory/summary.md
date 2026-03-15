# rh.1 Structural Summary

- Total files indexed: **264988**
- Total bytes indexed: **25532037558**
- Corpus distribution by size:
  - `unknown`: 17391139544 bytes, 141353 files (68.11% by size)
  - `ui_assets`: 4329656030 bytes, 52127 files (16.96% by size)
  - `app_bundles`: 2480170040 bytes, 28755 files (9.71% by size)
  - `reverse`: 857514591 bytes, 466 files (3.36% by size)
  - `configs`: 184223894 bytes, 6021 files (0.72% by size)
  - `firebase_data`: 178345103 bytes, 932 files (0.70% by size)
  - `play_docs`: 109501323 bytes, 27278 files (0.43% by size)
  - `sessions`: 1487033 bytes, 8056 files (0.01% by size)

## Size concentrations
- `.git`: 8864254564 bytes (35255 files)
- `.git/objects`: 8839612577 bytes (35096 files)
- `.git/objects/pack`: 6014466316 bytes (20 files)
- `packages`: 2674836332 bytes (27746 files)
- `packages/RheaKit`: 2674541280 bytes (27690 files)
- `packages/RheaKit/.build`: 2673451975 bytes (27644 files)
- `docs`: 1962467070 bytes (68399 files)
- `ios`: 1686148031 bytes (12463 files)
- `packages/RheaKit/.build/index-build`: 1650971690 bytes (14254 files)
- `docs/restore`: 1597877321 bytes (4153 files)
- `rhea-cli`: 1583241323 bytes (5959 files)
- `rhea-cli/target`: 1583123631 bytes (5950 files)
- `rhea-session-server`: 1229507494 bytes (5024 files)
- `rhea-session-server/target`: 1229410968 bytes (5017 files)
- `rhea-dash`: 1222916191 bytes (3470 files)
- `rhea-dash/target`: 1222748766 bytes (3466 files)
- `rhea-dash/target/debug`: 1222740768 bytes (3463 files)
- `docs/restore/1`: 1194611582 bytes (3024 files)
- `docs/restore/1/docscreatewithplaycomenarticlesgetting-started-14470916151957`: 1194578798 bytes (3020 files)
- `docs/restore/1/docscreatewithplaycomenarticlesgetting-started-14470916151957/en`: 1194572650 bytes (3019 files)

## File-type concentrations
- `.js`: 55475 files
- `[none]`: 47820 files
- `.py`: 20788 files
- `.pyc`: 20576 files
- `.ts`: 14751 files
- `.md`: 13379 files
- `.map`: 9701 files
- `.json`: 9128 files
- `.o`: 7417 files
- `.txt`: 4683 files
- `.html`: 4383 files
- `.test`: 4326 files
- `.swift`: 4236 files
- `.d`: 3878 files
- `.pcm`: 2746 files
- `.timestamp`: 2556 files
- `.rmeta`: 1790 files
- `.dia`: 1692 files
- `.rlib`: 1643 files
- `.swiftdeps`: 1582 files

## Obvious clusters
- Firebase mirror cluster: `mirror/firebase_storage/...` (high-volume image assets + IDs).
- Play extraction cluster: `ios/play-extraction/...` (reports + JSON metadata).
- UI/runtime cluster: `rhea-atlas/`, `frontend/`, `assets/`, `rheknel_files/`.
- Build/bundle cluster: `.next/`, `rhea-atlas-out/`, `dist/build` style folders.
- Session/memory cluster: `.entire/`, `docs/state*.md`, `opera/ops/virtual-office/`.

## Source-of-truth vs cache/debris (evidence-based)
- Likely source-of-truth: protocol docs, state docs, config roots, extraction reports, code in `src/`, `packages/`, `ios/`.
- Likely derived/cache: `.next/`, bundled chunks, mirrored thumbnails, temporary caches.
- Mixed zones: `mirror/`, `ios/play-extraction/` (high-value metadata + generated artifacts mixed).

## Salvage zones
- `ios/play-extraction/*.json` and reports: high potential for metadata ingest.
- `mirror/firebase_storage/...`: asset linkage candidates (project/page IDs).
- `protocols/`, `prompts/`, `docs/`: policy and continuity indexing candidates.

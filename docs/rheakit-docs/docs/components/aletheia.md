---
sidebar_position: 8
title: AletheiaView
---

# AletheiaView

A proof store and ontology browser. Displays immutable tribunal proofs and hypothesis verification chains from the Aletheia subsystem.

## Usage

```swift
import RheaKit

struct AletheiaTab: View {
    var body: some View {
        AletheiaView()
    }
}
```

## Features

- **Proof listing** — Browse all proofs from `/aletheia/proofs`
- **Summary badges** — Proof count and ontology count at a glance
- **Proof detail** — Tap a proof to expand its full data (claim, tier, agreement score, confidence)
- **Ontology section** — Lists all registered ontologies from `/ontology`
- **Pull to refresh** — Standard refresh gesture
- **Loading state** — ProgressView while data is being fetched

## Layout

```
┌─ Summary Badges ──────────────────┐
│  PROOFS: 42    ONTOLOGIES: 3      │
├───────────────────────────────────┤
│  [Proof Detail — if selected]     │
├───────────────────────────────────┤
│  Proof List                       │
│  ├─ claim: "X is true"           │
│  │  tier: cheap | score: 0.87    │
│  ├─ claim: "Y holds"            │
│  │  tier: mid  | score: 0.92    │
│  └─ ...                          │
├───────────────────────────────────┤
│  Ontology Section                 │
│  ├─ biochemistry                  │
│  ├─ chronobiology                 │
│  └─ ...                          │
└───────────────────────────────────┘
```

## Data Source

- **Proofs** — Fetched via `RheaAPI.shared.proofs()` → `GET /aletheia/proofs`. SQL-backed (`proof.db`), immutable once written, survives backend restarts.
- **Ontologies** — Fetched via `RheaAPI.shared.ontologies()` → `GET /ontology`. Returns list of registered hypothesis spaces.

## Notes

- Proofs are the permanent truth record — once written to `proof.db`, they never change
- The view is iOS-compatible (no `HSplitView` — uses `NavigationStack` with scroll)
- Proof data includes: id, claim, tier, agreement_score, confidence, created_at

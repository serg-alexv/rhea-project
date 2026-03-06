---
sidebar_position: 1
title: BioRendererView
---

# BioRendererView

A 3D molecular visualization component powered by [3Dmol.js](https://3dmol.csb.pitt.edu/) running inside a `WKWebView`. Supports PDB lookup, SMILES input, multiple render styles, and tribunal-powered molecule analysis.

## Usage

```swift
import RheaKit

struct MoleculeTab: View {
    var body: some View {
        BioRendererView()
    }
}
```

`BioRendererView` is a self-contained `NavigationStack` — drop it into a `TabView` or present it modally.

## Features

- **PDB lookup** — Enter a PDB ID (e.g. `1CRN`) to fetch and render structures from RCSB
- **SMILES input** — Toggle to SMILES mode for small molecule visualization (drug candidates)
- **Render styles** — Cartoon, stick, sphere, line, cross
- **Color schemes** — Spectrum, chain, secondary structure, element, residue
- **Touch/mouse interaction** — Rotate, zoom, pan the 3D model
- **Molecule presets** — Quick-access buttons for common structures
- **Analysis panel** — "Ask about this molecule" triggers a tribunal-powered AI analysis
- **Metadata display** — Shows title, method, resolution, organism for loaded structures

## Presets

The following molecules are available as one-tap presets:

| PDB ID | Name |
|---|---|
| `1CRN` | Crambin |
| `1BNA` | DNA B-form |
| `4HHB` | Hemoglobin |
| `1ATP` | ATP synthase |
| `6LU7` | SARS-CoV-2 Mpro |
| `1GZM` | GFP |

## Render Styles

| Style | Description |
|---|---|
| `cartoon` | Secondary structure ribbons (default) |
| `stick` | Ball-and-stick bonds |
| `sphere` | Space-filling CPK spheres |
| `line` | Wireframe bonds |
| `cross` | Cross markers at atom positions |

## Color Schemes

| Scheme | Description |
|---|---|
| `spectrum` | Rainbow gradient along chain (default) |
| `chain` | Distinct color per chain |
| `ss` | Color by secondary structure |
| `element` | CPK element colors |
| `residue` | Color by residue type |

## Analysis Panel

Tapping "Ask about this molecule" sends the current PDB ID or SMILES string to the Rhea backend for tribunal-powered multi-model analysis. The response appears in a collapsible panel below the 3D viewer.

## Notes

- 3Dmol.js is bundled locally as `3Dmol-min.js` — no CDN dependency
- PDB files are fetched from RCSB (public domain)
- The renderer runs entirely client-side; no server computation needed for visualization
- Requires network access for PDB fetches and AI analysis

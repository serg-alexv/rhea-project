# BioRenderer Integration Map

## Status: Ready to Integrate ✅

**Frontend:** BioRendererView.swift (32KB, fully implemented in RheaKit)  
**Backend:** rhea-biorenderer Rust service (MIT licensed)  
**Graphics:** Gigabytes of assets (PDB database, SMILES renderers, molecular templates)  

---

## Architecture

```
┌─────────────────────────┐
│   iOS/SwiftUI Client    │
│  (BioRendererView.swift)│
│   - 3Dmol.js WebView    │
│   - PDB lookup          │
│   - SMILES input        │
│   - Rotation/zoom       │
│   - Analysis panel      │
└────────────┬────────────┘
             │ HTTP/JSON
             ▼
┌─────────────────────────┐
│   rhea-biorenderer      │
│   Rust service (:3003)  │
│   - /generate/molecule  │
│   - /generate/pathway   │
│   - /generate/crdt      │
│   - /generate/paper     │
└────────────┬────────────┘
             │ SVG/PDF
             ▼
┌─────────────────────────┐
│  Graphics Library       │
│  (Asset store)          │
│  - Protein structures   │
│  - Metabolic networks   │
│  - Molecular templates  │
│  - Publication figures  │
└─────────────────────────┘
```

---

## Current State

### Frontend (BioRendererView.swift) ✅ DONE
- **Features:**
  - PDB database lookup (6 preset proteins)
  - SMILES string input for small molecules
  - 3D rendering via 3Dmol.js (bundled locally)
  - Multiple render styles (cartoon, stick, sphere, line, cross)
  - Color schemes (spectrum, chain, secondary structure, element, residue)
  - Touch gestures (rotate, zoom, pan)
  - "Ask about this molecule" — tribunal-powered analysis
  - Cross-device sync of 3D snapshots
  - Metadata panel (PDB method, resolution, organism)

### Backend (rhea-biorenderer) ✅ DONE
- **Endpoints:**
  - `POST /generate/molecule` — render molecular structure
  - `POST /generate/pathway` — render metabolic pathway
  - `POST /generate/crdt` — render CRDT convergence diagrams
  - `POST /generate/paper` — batch generate publication figures

### Graphics/Assets ❓ EXTERNAL
- PDB database (RCSB, public domain)
- SMILES → 3D conversion (via RDKit or similar)
- Publication templates for scientific papers
- Metabolic network databases (KEGG, Reactome)

---

## Integration Steps

### 1. Wire BioRendererView to Backend

In `BioRendererView.swift`, add endpoint calls:

```swift
// Fetch molecule figure from backend
func fetchMoleculeImage(name: String, smiles: String) {
    let req = MoleculeRequest(name: name, smiles: smiles, description: nil)
    Task {
        let result = try await APIClient.post(
            "/biorenderer/generate/molecule",
            body: req
        )
        // Use result.svg_data in WebView
    }
}
```

### 2. Add Batch Paper Generation

```swift
// Generate full figure set for scientific paper
func generatePaperFigures() {
    Task {
        let figures = try await APIClient.post(
            "/biorenderer/generate/paper",
            body: [:]
        ) as [PaperFigure]
        // Display figures in gallery
    }
}
```

### 3. Export to LaTeX/PDF

Add PDF export for paper writing:

```swift
// Export as PDF for inclusion in paper
func exportAsPDF(figure: PaperFigure) -> URL {
    // Convert SVG → PDF via Cairo/librsvg
    let pdf = SVGToPDFConverter.convert(figure.svg_data)
    return pdf
}
```

---

## Use Cases

### 1. Scientific Paper Writing
- Generate CRDT/DTS diagrams automatically
- Molecule/pathway visualizations with captions
- Cross-reference figures in appendix

### 2. Interactive Education
- Students rotate proteins, explore structure
- "Ask about this molecule" for AI explanations
- Multi-device collaborative exploration

### 3. Research Collaboration
- Cross-device sync of 3D analysis
- Annotation overlay on structures
- Export snapshots for presentations

---

## Next Steps (Priority Order)

1. **Wire APIClient calls** (BioRendererView → rhea-biorenderer)
   - Replace mock data with real backend calls
   - Handle network errors gracefully

2. **Asset pipeline** (Graphics library)
   - Set up PDB caching
   - SMILES → 3D rendering pipeline
   - Template library for papers

3. **PDF export** (Publication workflow)
   - SVG → PDF conversion
   - Batch figure export for papers
   - Integration with Overleaf/LaTeX

4. **Advanced rendering**
   - Protein structure animations
   - Electron density maps
   - Multi-scale visualization (atoms → pathways → systems)

---

## Files to Modify

```
ios/RheaPreview.swiftpm/Sources/
  ├─ RheaPreviewApp.swift       (added .bio case)
  └─ CommandCentreLayout.swift  (added BioRendererView())

packages/RheaKit/Sources/RheaKit/
  ├─ BioRendererView.swift      (32KB, DONE)
  ├─ RheaAPI.swift              (add biorenderer endpoints)
  └─ APIClient.swift            (wire HTTP calls)

rhea-biorenderer/
  ├─ src/main.rs                (DONE)
  ├─ Cargo.toml                 (DONE)
  └─ README.md                  (DONE, MIT licensed)
```

---

## Architecture Decision (ADR-018)

**Proposal:** Separate rendering backend (Rust) from presentation (SwiftUI).

**Rationale:**
- **Portability**: rhea-biorenderer runs on Linux, Docker, Cloud Run
- **Scalability**: Batch figure generation for papers
- **Licensing**: MIT licensed, deployable anywhere
- **Graphics**: Graphics library (GB of assets) decoupled from code

**Status:** Ready for implementation.

---

## Deployment

### Development
```bash
# Terminal 1: Backend
cd rhea-biorenderer && cargo run --release
# Running on http://127.0.0.1:3003

# Terminal 2: iOS
open ios/RheaApp/RheaApp.xcodeproj
```

### Production
```bash
# Deploy via Cloud Run
gcloud run deploy rhea-biorenderer \
  --source rhea-biorenderer \
  --platform managed \
  --region us-central1
```

---

## References

- **Frontend:** `packages/RheaKit/Sources/RheaKit/BioRendererView.swift`
- **Backend:** `rhea-biorenderer/src/main.rs`
- **3Dmol.js:** `packages/RheaKit/Resources/3Dmol-min.js`
- **PDB Database:** https://www.rcsb.org/
- **SMILES:** https://en.wikipedia.org/wiki/Simplified_molecular_input_line_entry_system

---

**Status:** Framework complete. Graphics library integration pending.  
**Last Updated:** 2026-03-06 03:45Z

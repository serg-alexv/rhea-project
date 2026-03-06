# 🧬 BioRenderer

**Auto-generate publication-quality figures for scientific papers from structured biological data.**

MIT-licensed, self-hostable, or use the hosted service.

## Features

- 🎨 **SVG figure generation** — molecules, pathways, CRDT diagrams, protein structures
- 📊 **Publication-ready output** — high-DPI, vector-based, editable
- 🔄 **CRDT visualization** — illustrate multi-device convergence, Lamport Clocks
- 📝 **Paper integration** — generate entire figure sets for a single document
- 🚀 **REST API** — POST structured data, get SVG/PDF figures
- 🏠 **Self-hostable** — deploy on your own infrastructure

## Quick Start

### Install (Self-Hosted)

```bash
git clone https://github.com/timelabs/rhea-biorenderer.git
cd rhea-biorenderer
cargo build --release
./target/release/rhea-biorenderer
# Running on http://127.0.0.1:3003
```

### Generate a Molecule Figure

```bash
curl -X POST http://127.0.0.1:3003/generate/molecule \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dopamine",
    "smiles": "C1=CC(=C(C=C1)O)CCNC",
    "description": "Neurotransmitter structure"
  }'
```

Response:
```json
{
  "figure_id": "fig_abc123",
  "figure_type": "molecule",
  "title": "Structure of Dopamine",
  "caption": "Neurotransmitter structure",
  "svg_data": "<svg>...</svg>",
  "timestamp": "2026-03-06T03:44:00Z"
}
```

### Generate a Metabolic Pathway

```bash
curl -X POST http://127.0.0.1:3003/generate/pathway \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Glycolysis",
    "steps": ["Glucose", "Glucose-6-P", "Fructose-6-P", "Pyruvate"],
    "organism": "E. coli"
  }'
```

### Generate Full Paper Figure Set

```bash
curl -X POST http://127.0.0.1:3003/generate/paper \
  -H "Content-Type: application/json" \
  -d '{}'
```

Returns array of publication-ready figures (CRDT convergence, message ordering, etc).

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Service health check |
| `/generate/molecule` | POST | Render molecular structure |
| `/generate/pathway` | POST | Render metabolic/biological pathway |
| `/generate/crdt` | POST | Render CRDT convergence diagram |
| `/generate/paper` | POST | Generate complete paper figure set |

## Deployment

### Hosted Service

Use the free tier (5 figures/month) or upgrade:

```bash
# Point to hosted service
export BIORENDERER_API="https://biorenderer.rhea.dev"
curl -X POST $BIORENDERER_API/generate/paper \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Pricing:**
- **Free**: 5 figures/month, community figures (MIT licensed)
- **Pro**: $9/mo, unlimited figures, 1-hour priority rendering
- **Enterprise**: Custom SLA, private deployments, dedicated support

### Self-Host (Docker)

```dockerfile
FROM rust:latest
WORKDIR /app
COPY . .
RUN cargo build --release
EXPOSE 3003
CMD ["./target/release/rhea-biorenderer"]
```

```bash
docker run -p 3003:3003 biorenderer
```

## Format: Structured Data → SVG → PDF

Input: JSON description of biological object  
↓  
BioRenderer: Generates SVG  
↓  
Output: SVG (edit in Inkscape) or PDF (print-ready)

Example: Molecule → LaTeX figure → Paper

```latex
\begin{figure}
  \includegraphics[width=0.4\textwidth]{dopamine.pdf}
  \caption{Neurotransmitter structure}
\end{figure}
```

## Examples

### CRDT Convergence Diagram
```
Input:
{
  "type": "crdt",
  "devices": ["Device A", "Device B"],
  "messages": [{"lc": 1, "content": "msg1"}, {"lc": 2, "content": "msg2"}]
}

Output:
[Box: Device A]  ←→  [Box: Device B]
  LC: 1,2,3           LC: 1,2,3
                    ✓ Converged
```

### Protein Pathway
```
Input:
{
  "name": "SARS-CoV-2 RdRp",
  "steps": ["Binding", "Proofreading", "Elongation", "Release"]
}

Output: [Step 1] → [Step 2] → [Step 3] → [Step 4]
```

## License

MIT — Use, modify, deploy freely. See [LICENSE](LICENSE).

## Contributing

PRs welcome. Ideas:

- [ ] 3D protein structure rendering (via Mol*)
- [ ] Publication export (PDF, EPS)
- [ ] Batch figure generation
- [ ] Figure templates library
- [ ] Integration with Overleaf/Google Docs

## Roadmap

- **v0.2**: PDF export, batch processing
- **v0.3**: Protein structure visualization
- **v0.4**: ML model visualizations
- **v1.0**: Production API, SLA guarantees

## Support

- **Docs**: https://docs.rhea.dev/biorenderer
- **Issues**: https://github.com/timelabs/rhea-biorenderer/issues
- **Chat**: Rhea Discord #biorenderer

---

**Hosted service**: https://biorenderer.rhea.dev  
**Self-host**: `cargo run --release`

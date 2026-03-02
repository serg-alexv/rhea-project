# Aletheia — Proof Library Guide
> ἀλήθεια — "un-concealment": truth as the act of revealing what was hidden.

## What Is Aletheia?

Aletheia is Rhea's knowledge accumulation system. Every time the Tribunal (multi-model consensus engine) answers a question, the result is automatically classified and stored as a **proof**, **hypothesis**, or **noise**. Over time this builds a searchable library of verified knowledge — a living proof base.

## How Often Does It Update?

Aletheia updates **every time a Tribunal call completes**. There are two paths:

**Automatic capture** (tribunal_api.py → aletheia_pipeline.py):
- `POST /tribunal` — standard consensus query
- `POST /tribunal/ice` — iterative critique & evaluation
- `POST /tribunal/sceptic` — adversarial devil's-advocate mode

After each response is returned to the caller, a background capture hook classifies and stores the result. This is wrapped in try/except so it never blocks or breaks the tribunal response.

**Manual submission** (aletheia_api.py via rhead.py):
- `POST :8000/aletheia/submit` — submit a proof manually with your own scores

You can submit proofs from any source: literature reviews, personal research, external tools. The manual path uses the same classification and storage pipeline.

## Can I Add Entries Manually?

Yes. Use the `/aletheia/submit` endpoint:

```bash
curl -X POST http://localhost:8000/aletheia/submit \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Melatonin suppression under blue light peaks at 460nm wavelength",
    "consensus_text": "Multiple studies confirm peak suppression at 446-477nm with maximum effect around 460nm.",
    "ontology": "chronobiology",
    "agreement_score": 0.91,
    "confidence": 0.85,
    "models": ["manual", "PubMed review"],
    "mode": "manual"
  }'
```

Or through Python:

```python
import requests
r = requests.post("http://localhost:8000/aletheia/submit", json={
    "prompt": "Cortisol awakening response peaks 30-45min after waking",
    "consensus_text": "CAR is a well-established phenomenon...",
    "ontology": "chronobiology",
    "agreement_score": 0.95,
    "confidence": 0.90,
})
print(r.json()["id"])  # → proof ID
```

Or via CLI:

```bash
python3 src/aletheia_pipeline.py stats      # library statistics
python3 src/aletheia_pipeline.py recent     # recent entries
python3 src/aletheia_pipeline.py search "melatonin"
python3 src/aletheia_pipeline.py verify     # DB ↔ filesystem check
python3 src/aletheia_pipeline.py export --format json --output proofs.json
python3 src/aletheia_pipeline.py chain <proof_id>
python3 src/aletheia_pipeline.py prune --older-than 90  # remove old noise
```

## Tier Classification

Every entry is classified into one of three tiers:

| Tier | Agreement Score | Description | File Created? |
|------|----------------|-------------|---------------|
| **proof** | ≥ 85% OR (≥ 75% with math verification) | High-confidence verified knowledge | Yes → `friends/aletheia/proofs/` |
| **hypothesis** | 50–84% | Promising but not fully confirmed | Yes → `friends/aletheia/hypotheses/` |
| **noise** | < 50% | Low agreement, unreliable | No file — logged to DB only |

Math boost: if any Ruliad math plugin returns `verified`, the threshold for proof drops from 85% to 75%.

## Storage Architecture

Aletheia stores data in two parallel formats:

### 1. SQLite Database (`data/proof.db`)

Primary structured store. Schema:

```
proofs (
  id              TEXT PRIMARY KEY    -- 24-char SHA256 hash
  type            TEXT                -- consensus | agreement | divergence | math | ice
  tier            TEXT                -- proof | hypothesis | noise
  prompt          TEXT                -- original question
  prompt_hash     TEXT                -- 16-char hash for dedup
  ontology        TEXT                -- general | chronobiology | pharmacology | ...
  mode            TEXT                -- local | chairman | ice | sceptic | manual
  consensus_text  TEXT                -- the actual answer
  agreement_score REAL                -- 0.0 to 1.0
  confidence      REAL                -- 0.0 to 1.0
  models          TEXT (JSON array)   -- ["gpt-4o", "claude-opus-4-6", ...]
  agreement_points TEXT (JSON array)  -- what models agreed on
  divergence_points TEXT (JSON array) -- where models disagreed
  math_verification TEXT (JSON)       -- Ruliad plugin results
  stance_summary  TEXT (JSON)         -- per-model position summary
  analysis_method TEXT                -- local_count | chairman_synthesis | ...
  rounds_completed INTEGER            -- ICE rounds (0 for standard)
  convergence_achieved BOOLEAN        -- ICE convergence flag
  parent_id       TEXT                -- links to previous proof (chain)
  file_path       TEXT                -- relative path to markdown file
  created_at      TEXT                -- ISO 8601 timestamp
  tokens_total    INTEGER             -- total API tokens consumed
  latency_total_s REAL                -- total wall-clock seconds
  raw_responses   TEXT (JSON)         -- full model responses
)

proof_chains (
  parent_id  TEXT    -- source proof
  child_id   TEXT    -- derived proof
  relation   TEXT    -- refines | contradicts | extends | confirms
  created_at TEXT
)
```

Indexes: ontology, agreement_score, tier, type, prompt_hash, created_at.

Aggregate view:

```sql
SELECT * FROM aletheia_stats;
-- → total_artifacts, proof_count, hypothesis_count, noise_count,
--   avg_agreement, avg_confidence, ontology_count, unique_queries,
--   total_tokens, last_capture
```

### 2. Markdown Files (`friends/aletheia/`)

Human-readable proof documents, organized by tier and ontology:

```
friends/aletheia/
├── proofs/
│   ├── chronobiology/
│   │   └── 0650a31a247b77e6a719f701.md
│   ├── pharmacology/
│   ├── general/
│   └── ...
├── hypotheses/
│   ├── chronobiology/
│   └── ...
└── .gitkeep
```

Each markdown file follows this format:

```markdown
# [PROVEN] Circadian rhythm disruption correlates with increased inflammatory...
> Ontology: chronobiology | Agreement: 88% | Confidence: 75%
> Models: manual
> Mode: manual | Method: manual_submit | Date: 2026-02-26T16:32:52+00:00
> ID: 0650a31a247b77e6a719f701

## Consensus
Multiple studies confirm elevated IL-6 and CRP in rotating shift workers...

## Agreement Points
- IL-6 elevated
- CRP elevated
- TNF-alpha trend

## Divergence Points
- Cortisol timing unclear

## Mathematical Verification
- [PASS] information_geometry: verified
- [FAIL] proof_theory: falsified

## Stance Summary
- **gpt-4o**: Strong agreement
- **claude-opus-4-6**: Agreement with caveats

## Metadata
- Type: consensus
- Rounds: 0 | Converged: False
- Tokens: 1247 | Latency: 3.2s
- Parent: none (root)
- Session: unknown
```

## Proof Chains

Proofs can link to form knowledge chains (DAGs):

```
[root proof] ──refines──→ [refined proof] ──extends──→ [extended proof]
                                 ↑
                     ──contradicts── [counter-proof]
```

Relations: `refines` (same question, better answer), `contradicts` (opposite conclusion), `extends` (adds new dimension), `confirms` (independent replication).

When you submit a proof with the same prompt as an existing one, the pipeline auto-detects the parent and creates a chain link.

## API Endpoints

All endpoints are served by rhead.py at `:8000/aletheia/`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/aletheia/submit` | Manual proof submission |
| GET | `/aletheia/proofs?tier=proof&limit=50` | List proofs (filterable by tier) |
| GET | `/aletheia/proofs/{id}` | Get single proof with full detail |
| GET | `/aletheia/stats` | Library statistics |
| GET | `/aletheia/search?q=melatonin&limit=10&tier=proof` | Keyword search |
| GET | `/aletheia/chain/{id}` | Proof chain (ancestors + descendants) |
| POST | `/aletheia/verify` | DB ↔ filesystem consistency check |

### Submit Request Schema

```json
{
  "prompt": "string (required) — the claim or question",
  "consensus_text": "string — the proof body / answer",
  "ontology": "string — e.g. 'chronobiology', 'pharmacology', 'general'",
  "agreement_score": 0.88,   // 0.0–1.0, determines tier
  "confidence": 0.75,         // 0.0–1.0
  "models": ["manual"],       // list of model names or 'manual'
  "mode": "manual"            // capture mode
}
```

### Response Schema (ProofDetail)

```json
{
  "id": "0650a31a247b77e6a719f701",
  "type": "consensus",
  "tier": "proof",
  "prompt": "...",
  "prompt_hash": "18bb40fe0fbb7f1b",
  "ontology": "chronobiology",
  "mode": "manual",
  "consensus_text": "...",
  "agreement_score": 0.88,
  "confidence": 0.75,
  "models": ["manual"],
  "agreement_points": ["IL-6 elevated", "CRP elevated"],
  "divergence_points": ["Cortisol timing unclear"],
  "math_verification": {},
  "stance_summary": {},
  "analysis_method": "manual_submit",
  "rounds_completed": 0,
  "convergence_achieved": false,
  "parent_id": null,
  "session_id": null,
  "file_path": "friends/aletheia/proofs/chronobiology/0650a31a247b77e6a719f701.md",
  "created_at": "2026-02-26T16:32:52.873690+00:00",
  "tokens_total": 0,
  "latency_total_s": 0.0
}
```

## Architecture Summary

```
                    ┌─────────────────┐
  User question ───→│ tribunal_api.py │───→ Response to user
                    │     :8400       │
                    └────────┬────────┘
                             │ aletheia.capture()
                             ▼
                    ┌─────────────────┐
                    │aletheia_pipeline│
                    │     .py         │
                    └──┬──────────┬───┘
                       │          │
              ┌────────▼──┐  ┌───▼────────────┐
              │ proof.db   │  │ friends/aletheia│
              │ (SQLite)   │  │ /{proofs,hypo}/ │
              └────────────┘  └────────────────┘
                       ▲          ▲
                       │          │
                    ┌──┴──────────┴───┐
                    │ aletheia_api.py  │ ← /submit, /proofs, /stats...
                    │ (via rhead.py)   │
                    │     :8000        │
                    └─────────────────┘
```

## Maintenance

```bash
# Check library health
python3 src/aletheia_pipeline.py verify

# Export all proofs
python3 src/aletheia_pipeline.py export --format json --output all_proofs.json
python3 src/aletheia_pipeline.py export --format csv --output all_proofs.csv

# Remove old noise (keeps proofs + hypotheses)
python3 src/aletheia_pipeline.py prune --older-than 90

# Quick stats
python3 src/aletheia_pipeline.py stats
```

## Ontology Namespaces

Proofs are organized by ontology (research domain). Current namespaces:

- `general` — default for unclassified queries
- `chronobiology` — circadian rhythms, sleep, light exposure, HRV
- `pharmacology` — drug interactions, receptors, dose-response, ADME
- `biochemistry` — molecular mechanisms, enzymes, metabolic pathways
- `logic` — formal proof structure, inference rules
- `topology` — continuity, compactness, homeomorphic invariants
- `systems_biology` — network dynamics, feedback loops, emergent properties

New ontologies are created automatically when you submit proofs with new ontology names.

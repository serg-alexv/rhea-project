# ALETHEIA COMPLETE ABSORPTION PLAN
> For Orion (GPT-5.3) · 2026-02-26 · Approved by Rex
> "ἀλήθεια — un-concealment. Truth as the act of revealing what was hidden."

---

## Why This Matters

Every tribunal query produces knowledge. Right now that knowledge lives for one
browser session and dies. Aletheia captures it, structures it, makes it searchable,
and feeds it back into the system. No repeated queries. No lost proofs.
The system remembers what it proved.

---

## Architecture Overview

```
                    ┌──────────────┐
                    │ User Query   │
                    └──────┬───────┘
                           ▼
                  ┌────────────────┐
                  │ tribunal_api.py │ ← /tribunal, /tribunal/ice, /tribunal/sceptic
                  └────────┬───────┘
                           ▼
                  ┌────────────────┐
                  │ consensus_     │ ← TF-IDF + ICE + Chairman
                  │ analyzer.py    │    Returns: ConsensusReport
                  └────────┬───────┘
                           ▼
              ┌────────────────────────┐
              │ ALETHEIA CAPTURE LAYER │ ← NEW: src/aletheia_pipeline.py
              └────────┬───────┬───────┘
                       │       │
            ┌──────────▼──┐  ┌─▼──────────────┐
            │ data/proof.db│  │ friends/aletheia│
            │ (SQLite)     │  │ (Markdown files)│
            └──────────────┘  └────────────────┘
                       │       │
              ┌────────▼───────▼───────┐
              │ RETRIEVAL LAYER        │
              │ rhea_ingest.py (Redis) │ ← Embed proofs → vector search
              └────────────┬───────────┘
                           ▼
              ┌────────────────────────┐
              │ UI: HudLeft + Oceanus  │ ← Proof count, density spheres
              └────────────────────────┘
                           ▼
              ┌────────────────────────┐
              │ PRE-QUERY DEDUP        │ ← "Already proven?" check
              └────────────────────────┘
```

---

## PHASE A — Core Pipeline (`src/aletheia_pipeline.py`)

### A1. Proof Capture Function

```python
"""
Aletheia Pipeline — Proof capture, storage, and retrieval.
'Un-concealment': truth emerges from tribunal consensus.
"""
import hashlib, json, sqlite3, os
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Literal

PROOF_DB = Path(__file__).parent.parent / "data" / "proof.db"
ALETHEIA_ROOT = Path(__file__).parent.parent / "friends" / "aletheia"

ProofType = Literal["consensus", "agreement", "divergence", "math", "ice"]
ProofTier = Literal["proof", "hypothesis", "noise"]


@dataclass
class ProofArtifact:
    id: str                          # SHA-256 of (prompt + timestamp)
    type: ProofType                  # What kind of proof
    tier: ProofTier                  # proof (>85%), hypothesis (50-84%), noise (<50%)
    prompt: str                      # Original query
    prompt_hash: str                 # SHA-256[:16] of prompt
    ontology: str                    # Active ontology
    mode: str                        # tribunal | sceptic | ice
    consensus_text: str              # Synthesized answer
    agreement_score: float           # 0.0 - 1.0
    confidence: float                # 0.0 - 1.0
    models: list[str]                # Models that participated
    agreement_points: list[str]      # What they agreed on
    divergence_points: list[str]     # Where they diverged
    math_verification: dict          # Ruliad plugin verdicts
    stance_summary: dict             # Per-model stance breakdown
    pairwise_similarity: dict        # Model-to-model semantic alignment
    analysis_method: str             # tfidf_local | ice | chairman
    rounds_completed: int            # ICE rounds (if applicable)
    convergence_achieved: bool       # Did ICE converge?
    parent_id: Optional[str]         # Chain to previous proof
    session_id: Optional[str]        # Session context
    file_path: Optional[str]         # Path in friends/aletheia/
    created_at: str                  # ISO timestamp
    tokens_total: int                # Total tokens consumed
    latency_total_s: float           # Total response time
    raw_responses: list[dict]        # Per-model response summaries
```

### A2. Tier Classification

```python
def classify_tier(agreement_score: float, confidence: float,
                  math_verification: dict) -> ProofTier:
    """
    Determine if result is proof, hypothesis, or noise.

    Rules:
      proof      — agreement >= 0.85 OR (agreement >= 0.75 AND math verified)
      hypothesis — agreement >= 0.50
      noise      — agreement < 0.50
    """
    math_boost = False
    if math_verification:
        verdicts = math_verification.get("verdicts", {})
        math_boost = any(v == "verified" for v in verdicts.values())

    if agreement_score >= 0.85:
        return "proof"
    if agreement_score >= 0.75 and math_boost:
        return "proof"  # Math verification elevates to proof
    if agreement_score >= 0.50:
        return "hypothesis"
    return "noise"
```

### A3. Capture Entry Point

```python
def capture(tribunal_response: dict, consensus_report: dict,
            raw_responses: list[dict], request_meta: dict) -> Optional[ProofArtifact]:
    """
    Main capture function. Called from tribunal_api.py after every response.

    Args:
        tribunal_response: The TribunalResponse dict
        consensus_report:  The ConsensusReport dict
        raw_responses:     List of ModelResponse dicts
        request_meta:      {prompt, k, mode, ontology, session_id}

    Returns:
        ProofArtifact if tier != noise, else None
    """
    prompt = request_meta["prompt"]
    now = datetime.now(timezone.utc).isoformat()
    proof_id = hashlib.sha256(f"{prompt}:{now}".encode()).hexdigest()[:24]
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

    agreement_score = consensus_report.get("agreement_score", 0.0)
    confidence = consensus_report.get("confidence", 0.0)
    math_ver = consensus_report.get("math_verification", {})

    tier = classify_tier(agreement_score, confidence, math_ver)

    if tier == "noise":
        # Still log to DB for audit, but don't create artifact file
        _log_to_db(proof_id, tier, prompt_hash, agreement_score, now, request_meta)
        return None

    # Extract model metadata
    models = [r.get("model", "unknown") for r in raw_responses]
    tokens = sum(r.get("tokens_used", 0) for r in raw_responses)
    latency = sum(r.get("latency_s", 0.0) for r in raw_responses)

    artifact = ProofArtifact(
        id=proof_id,
        type=_detect_proof_type(consensus_report, request_meta),
        tier=tier,
        prompt=prompt,
        prompt_hash=prompt_hash,
        ontology=request_meta.get("ontology", "general"),
        mode=request_meta.get("mode", "tribunal"),
        consensus_text=tribunal_response.get("consensus", ""),
        agreement_score=agreement_score,
        confidence=confidence,
        models=models,
        agreement_points=consensus_report.get("agreement_points", []),
        divergence_points=consensus_report.get("divergence_points", []),
        math_verification=math_ver,
        stance_summary=consensus_report.get("stance_summary", {}),
        pairwise_similarity=consensus_report.get("pairwise_similarity", {}),
        analysis_method=consensus_report.get("analysis_method", "unknown"),
        rounds_completed=consensus_report.get("rounds_completed", 0),
        convergence_achieved=consensus_report.get("convergence_achieved", False),
        parent_id=_find_parent(prompt_hash),
        session_id=request_meta.get("session_id"),
        file_path=None,  # Set after writing
        created_at=now,
        tokens_total=tokens,
        latency_total_s=latency,
        raw_responses=[{
            "model": r.get("model"),
            "provider": r.get("provider"),
            "latency_s": r.get("latency_s"),
            "tokens": r.get("tokens_used"),
            "text_preview": r.get("text", "")[:200]
        } for r in raw_responses]
    )

    # Write to filesystem and DB
    artifact.file_path = _write_markdown(artifact)
    _store_to_db(artifact)

    return artifact


def _detect_proof_type(report: dict, meta: dict) -> ProofType:
    """Classify the proof type based on content."""
    if report.get("math_verification", {}).get("domains_tested"):
        return "math"
    if meta.get("mode") == "ice":
        return "ice"
    if report.get("rounds_completed", 0) > 1:
        return "ice"
    if len(report.get("divergence_points", [])) > len(report.get("agreement_points", [])):
        return "divergence"
    if report.get("agreement_points"):
        return "agreement"
    return "consensus"
```

---

## PHASE B — Storage Layer

### B1. SQLite Schema Upgrade (`data/proof.db`)

```sql
-- Keep existing logic_audit table untouched (backward compat)

-- New: Main proofs table
CREATE TABLE IF NOT EXISTS proofs (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,              -- consensus|agreement|divergence|math|ice
    tier TEXT NOT NULL,              -- proof|hypothesis|noise
    prompt TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,
    ontology TEXT NOT NULL DEFAULT 'general',
    mode TEXT NOT NULL,              -- tribunal|sceptic|ice
    consensus_text TEXT,
    agreement_score REAL NOT NULL,
    confidence REAL NOT NULL,
    models TEXT NOT NULL,            -- JSON array
    agreement_points TEXT,           -- JSON array
    divergence_points TEXT,          -- JSON array
    math_verification TEXT,          -- JSON dict
    stance_summary TEXT,             -- JSON dict
    pairwise_similarity TEXT,        -- JSON dict
    analysis_method TEXT,
    rounds_completed INTEGER DEFAULT 0,
    convergence_achieved BOOLEAN DEFAULT FALSE,
    parent_id TEXT,                  -- FK to self (proof chain)
    session_id TEXT,
    file_path TEXT,
    created_at TEXT NOT NULL,
    tokens_total INTEGER DEFAULT 0,
    latency_total_s REAL DEFAULT 0.0,
    raw_responses TEXT,              -- JSON array of summaries
    embedded BOOLEAN DEFAULT FALSE,  -- Has been embedded to Redis?
    FOREIGN KEY (parent_id) REFERENCES proofs(id)
);

-- Indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_proofs_ontology ON proofs(ontology);
CREATE INDEX IF NOT EXISTS idx_proofs_score ON proofs(agreement_score);
CREATE INDEX IF NOT EXISTS idx_proofs_tier ON proofs(tier);
CREATE INDEX IF NOT EXISTS idx_proofs_type ON proofs(type);
CREATE INDEX IF NOT EXISTS idx_proofs_prompt_hash ON proofs(prompt_hash);
CREATE INDEX IF NOT EXISTS idx_proofs_created ON proofs(created_at);

-- Proof chains: track how proofs build on each other
CREATE TABLE IF NOT EXISTS proof_chains (
    parent_id TEXT NOT NULL,
    child_id TEXT NOT NULL,
    relation TEXT NOT NULL,          -- refines|contradicts|extends|confirms
    created_at TEXT NOT NULL,
    PRIMARY KEY (parent_id, child_id),
    FOREIGN KEY (parent_id) REFERENCES proofs(id),
    FOREIGN KEY (child_id) REFERENCES proofs(id)
);

-- Aggregated stats view (for /api/aletheia/stats)
CREATE VIEW IF NOT EXISTS aletheia_stats AS
SELECT
    COUNT(*) as total_artifacts,
    COUNT(CASE WHEN tier = 'proof' THEN 1 END) as proof_count,
    COUNT(CASE WHEN tier = 'hypothesis' THEN 1 END) as hypothesis_count,
    COUNT(CASE WHEN tier = 'noise' THEN 1 END) as noise_count,
    AVG(agreement_score) as avg_agreement,
    AVG(confidence) as avg_confidence,
    COUNT(DISTINCT ontology) as ontology_count,
    COUNT(DISTINCT prompt_hash) as unique_queries,
    SUM(tokens_total) as total_tokens,
    MAX(created_at) as last_capture
FROM proofs;
```

### B2. Markdown File Writer

```python
def _write_markdown(artifact: ProofArtifact) -> str:
    """Write proof artifact as structured markdown."""
    tier_dir = "proofs" if artifact.tier == "proof" else "hypotheses"
    ontology_dir = artifact.ontology.lower().replace(" ", "_")
    target_dir = ALETHEIA_ROOT / tier_dir / ontology_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{artifact.id}.md"
    filepath = target_dir / filename

    # Build title from first 80 chars of prompt
    title = artifact.prompt[:80].strip()
    if len(artifact.prompt) > 80:
        title += "..."

    models_str = ", ".join(artifact.models)
    tier_badge = "PROVEN" if artifact.tier == "proof" else "HYPOTHESIS"

    content = f"""# [{tier_badge}] {title}
> Ontology: {artifact.ontology} | Agreement: {artifact.agreement_score:.0%} | Confidence: {artifact.confidence:.0%}
> Models: {models_str}
> Mode: {artifact.mode} | Method: {artifact.analysis_method} | Date: {artifact.created_at}
> ID: {artifact.id}

## Consensus
{artifact.consensus_text}

## Agreement Points
"""
    for point in artifact.agreement_points:
        content += f"- {point}\n"

    if artifact.divergence_points:
        content += "\n## Divergence Points\n"
        for point in artifact.divergence_points:
            content += f"- {point}\n"

    if artifact.math_verification and artifact.math_verification.get("domains_tested"):
        content += "\n## Mathematical Verification\n"
        for domain, verdict in artifact.math_verification.get("verdicts", {}).items():
            emoji = "PASS" if verdict == "verified" else "FAIL" if verdict == "falsified" else "SKIP"
            content += f"- [{emoji}] {domain}: {verdict}\n"

    if artifact.stance_summary:
        content += "\n## Stance Summary\n"
        for model, stance in artifact.stance_summary.items():
            content += f"- **{model}**: {stance}\n"

    content += f"""
## Metadata
- Type: {artifact.type}
- Rounds: {artifact.rounds_completed} | Converged: {artifact.convergence_achieved}
- Tokens: {artifact.tokens_total} | Latency: {artifact.latency_total_s:.1f}s
- Parent: {artifact.parent_id or 'none (root)'}
- Session: {artifact.session_id or 'unknown'}
"""

    filepath.write_text(content, encoding="utf-8")
    return str(filepath.relative_to(ALETHEIA_ROOT.parent.parent))
```

---

## PHASE C — API Endpoints (tribunal_api.py)

### C1. Hook into Tribunal Response

In `tribunal_api.py`, after building TribunalResponse (line ~521):

```python
from aletheia_pipeline import capture as aletheia_capture

# Inside POST /tribunal handler, after result is built:
try:
    proof = aletheia_capture(
        tribunal_response=result.dict(),
        consensus_report=report,
        raw_responses=[r.dict() for r in result.responses],
        request_meta={
            "prompt": req.prompt,
            "k": req.k,
            "mode": "tribunal",
            "ontology": req.ontology if hasattr(req, "ontology") else "general",
            "session_id": getattr(req, "session_id", None),
        }
    )
    if proof:
        logger.info(f"Aletheia captured: {proof.tier}/{proof.type} id={proof.id}")
except Exception as e:
    logger.warning(f"Aletheia capture failed (non-blocking): {e}")
```

Same hook for `/tribunal/ice` and `/tribunal/sceptic` with appropriate `mode` value.

**Critical:** Capture is non-blocking. If it fails, tribunal still returns normally.

### C2. New REST Endpoints

```python
# ═══════════════ ALETHEIA ENDPOINTS ═══════════════

@app.get("/api/aletheia/stats")
async def aletheia_stats():
    """Return aggregated proof library statistics."""
    from aletheia_pipeline import get_stats
    return get_stats()

@app.get("/api/aletheia/search")
async def aletheia_search(q: str, k: int = 5, tier: str = None):
    """Search proof library by semantic similarity."""
    from aletheia_pipeline import search_proofs
    return search_proofs(q, k=k, tier_filter=tier)

@app.get("/api/aletheia/proof/{proof_id}")
async def aletheia_get_proof(proof_id: str):
    """Get a specific proof by ID."""
    from aletheia_pipeline import get_proof
    proof = get_proof(proof_id)
    if not proof:
        raise HTTPException(404, "Proof not found")
    return proof

@app.get("/api/aletheia/recent")
async def aletheia_recent(limit: int = 20, tier: str = None):
    """Get most recent proofs/hypotheses."""
    from aletheia_pipeline import get_recent
    return get_recent(limit=limit, tier_filter=tier)

@app.get("/api/aletheia/chain/{proof_id}")
async def aletheia_chain(proof_id: str):
    """Get the proof chain (ancestry + descendants) for a proof."""
    from aletheia_pipeline import get_chain
    return get_chain(proof_id)

@app.get("/api/aletheia/ontology/{ontology}")
async def aletheia_by_ontology(ontology: str, limit: int = 50):
    """Get all proofs for a specific ontology."""
    from aletheia_pipeline import get_by_ontology
    return get_by_ontology(ontology, limit=limit)

@app.get("/api/aletheia/dedup")
async def aletheia_dedup_check(q: str, threshold: float = 0.85):
    """Pre-query: check if this question has already been answered."""
    from aletheia_pipeline import check_existing
    return check_existing(q, threshold=threshold)
```

---

## PHASE D — Pre-Query Deduplication

### D1. "Already Proven?" Check

Before sending a query to tribunal, check if Aletheia already has an answer:

```python
def check_existing(query: str, threshold: float = 0.85) -> dict:
    """
    Check if query has already been answered with sufficient confidence.

    Returns:
        {
            "found": bool,
            "proof_id": str or None,
            "agreement_score": float,
            "consensus_preview": str (first 300 chars),
            "recommendation": "use_cached" | "re_query" | "no_match"
        }
    """
    prompt_hash = hashlib.sha256(query.encode()).hexdigest()[:16]

    # 1. Exact match by prompt hash
    conn = sqlite3.connect(PROOF_DB)
    row = conn.execute(
        "SELECT id, agreement_score, consensus_text, tier FROM proofs "
        "WHERE prompt_hash = ? AND tier = 'proof' "
        "ORDER BY agreement_score DESC LIMIT 1",
        (prompt_hash,)
    ).fetchone()

    if row:
        return {
            "found": True,
            "proof_id": row[0],
            "agreement_score": row[1],
            "consensus_preview": row[2][:300],
            "recommendation": "use_cached"
        }

    # 2. Semantic similarity via Redis (if embeddings exist)
    try:
        from rhea_ingest import search as redis_search
        results = redis_search(query, k=3, index_name="aletheia_proofs")
        if results and results[0].get("score", 0) >= threshold:
            proof_id = results[0].get("proof_id")
            proof = get_proof(proof_id)
            return {
                "found": True,
                "proof_id": proof_id,
                "agreement_score": proof.get("agreement_score", 0),
                "consensus_preview": proof.get("consensus_text", "")[:300],
                "recommendation": "use_cached"
            }
    except Exception:
        pass  # Redis not available, fall through

    # 3. No match
    return {
        "found": False,
        "proof_id": None,
        "agreement_score": 0.0,
        "consensus_preview": "",
        "recommendation": "no_match"
    }
```

### D2. Frontend Integration

In `ResearchPanel.tsx`, before submitting tribunal query:

```typescript
// Pre-query dedup check
const dedupCheck = await fetch(`${TRIBUNAL_API}/aletheia/dedup?q=${encodeURIComponent(query)}`);
const dedup = await dedupCheck.json();

if (dedup.found && dedup.recommendation === 'use_cached') {
  // Show cached result with "Previously proven" badge
  setResult({
    text: dedup.consensus_preview,
    proofId: dedup.proof_id,
    cached: true,
    agreement: dedup.agreement_score
  });
  // User can still click "Re-query" to force fresh tribunal
  return;
}

// No cache hit — proceed with normal tribunal query
```

---

## PHASE E — Redis Vector Embedding

### E1. Embed Proofs into Redis

Extend `rhea_ingest.py` to support proof artifacts:

```python
def embed_proof(proof: ProofArtifact):
    """Embed a proof artifact into Redis vector store."""
    # Combine key fields for embedding
    embed_text = f"{proof.prompt}\n\n{proof.consensus_text}"
    if proof.agreement_points:
        embed_text += "\n\n" + "\n".join(proof.agreement_points)

    embedding = get_embedding(embed_text)  # Google text-embedding-004

    # Store in Redis with proof metadata
    key = f"aletheia:proof:{proof.id}"
    redis_client.hset(key, mapping={
        "text": embed_text,
        "proof_id": proof.id,
        "tier": proof.tier,
        "ontology": proof.ontology,
        "agreement_score": proof.agreement_score,
        "source": proof.file_path,
        "embedding": embedding.tobytes()
    })

    # Mark as embedded in SQLite
    conn = sqlite3.connect(PROOF_DB)
    conn.execute("UPDATE proofs SET embedded = TRUE WHERE id = ?", (proof.id,))
    conn.commit()
```

### E2. Batch Embed Existing Proofs (CLI)

```bash
python3 src/aletheia_pipeline.py embed --all    # Embed all un-embedded proofs
python3 src/aletheia_pipeline.py embed --recent  # Embed last 24h of proofs
```

---

## PHASE F — UI Integration (rhea-atlas)

### F1. Store Additions (useAtlasStore.ts)

```typescript
// Add to AtlasState:
aletheiaStats: {
  proofCount: number;
  hypothesisCount: number;
  totalArtifacts: number;
  avgAgreement: number;
  lastCapture: string | null;
  ontologyCount: number;
  uniqueQueries: number;
};
setAletheiaStats: (stats: AletheidStats) => void;
```

### F2. Sync Hook Addition (useAtlasSync.ts)

```typescript
// Add to polling cycle (every 30s, not 5s — less critical than health):
const aletheiaInterval = setInterval(async () => {
  try {
    const res = await fetch(`${API_BASE}/api/aletheia/stats`);
    if (res.ok) {
      const stats = await res.json();
      setAletheiaStats(stats);
    }
  } catch { /* non-critical */ }
}, 30_000);
```

### F3. HudLeft Display (page.tsx)

After redis status block in HudLeft, add:

```tsx
{/* Aletheia proof count */}
<div className="flex items-center gap-1.5">
  <span className="text-[9px] text-white/30 uppercase tracking-widest">PROOFS</span>
  <span className="text-[10px] text-emerald-400 font-bold">
    {aletheiaStats.proofCount}
  </span>
  <span className="text-[8px] text-white/20">
    / {aletheiaStats.hypothesisCount} hyp
  </span>
</div>
```

### F4. Oceanus Flow Density Mapping

Proofs from Aletheia feed directly into ContextDensity:

```typescript
// In useDensityAnalysis.ts:
function proofsToContextDensity(stats: AletheiaStats, proofs: Proof[]): ContextDensity[] {
  // Group proofs by ontology
  const groups = groupBy(proofs, p => p.ontology);

  return Object.entries(groups).map(([ontology, items]) => {
    const avgScore = mean(items.map(p => p.agreement_score));
    const count = items.length;

    return {
      id: `aletheia-${ontology}`,
      label: ontology,
      density: Math.min(1, (count / 10) * avgScore),  // More proofs + higher score = denser
      consistency: 1 - standardDeviation(items.map(p => p.agreement_score)) / 0.5,
      position: ontologyToPosition(ontology),
      color: ontologyColor(ontology),
      ontology,
      sampleCount: count,
      vectorField: computeTemporalVectors(items),
    };
  });
}
```

This means:
- 1 proof in "pharmacology" with 90% agreement → small bright sphere
- 15 proofs in "cancer biology" with 92% avg → large dense sphere with full Krikoi rings
- 3 hypotheses in "weed shops" with 55% avg → diffuse nebula

### F5. Mnemosyne Whisper Integration

Add proof-triggered whispers:

```typescript
// In useWhisperStore.ts mood detection:
if (aletheiaStats.proofCount > prevProofCount) {
  // A new proof was just captured
  triggerWhisper('triumphant', 'proof_captured');
}
```

New whisper in `whispers.ts`:

```typescript
{
  id: 'triumphant-proof',
  mood: 'triumphant',
  glyph: 'star',
  text: 'A proof has crystallized. Aletheia remembers what the tribunal confirmed.',
  attribution: 'Aletheia'
}
```

---

## PHASE G — CLI Interface

### G1. Standalone Commands

```bash
# Search proofs by keyword
python3 src/aletheia_pipeline.py search "BRCA1 resistance mechanisms"

# List recent proofs
python3 src/aletheia_pipeline.py recent --limit 20

# Show stats
python3 src/aletheia_pipeline.py stats

# Export all proofs as JSON
python3 src/aletheia_pipeline.py export --format json --output proofs_export.json

# Export as CSV (for spreadsheets)
python3 src/aletheia_pipeline.py export --format csv --output proofs_export.csv

# Show proof chain (ancestry)
python3 src/aletheia_pipeline.py chain <proof_id>

# Embed all un-embedded proofs to Redis
python3 src/aletheia_pipeline.py embed --all

# Validate integrity (files match DB)
python3 src/aletheia_pipeline.py verify

# Prune noise entries older than 30 days
python3 src/aletheia_pipeline.py prune --older-than 30
```

### G2. Integration with rhea_orchestrate.py

In the 8-agent Chronos Protocol, each agent response can generate proofs:

```python
# In delegate() function, after agent response:
if response.agreement_score >= 0.5:
    from aletheia_pipeline import capture
    capture(
        tribunal_response={"consensus": response.text},
        consensus_report={"agreement_score": response.agreement_score, ...},
        raw_responses=[response.raw],
        request_meta={
            "prompt": task,
            "mode": "orchestration",
            "ontology": agent.domain,
            "session_id": session_id,
        }
    )
```

---

## PHASE H — Proof Chains (Knowledge Graph)

### H1. Parent Detection

```python
def _find_parent(prompt_hash: str) -> Optional[str]:
    """Find the most recent proof with similar prompt hash."""
    conn = sqlite3.connect(PROOF_DB)
    row = conn.execute(
        "SELECT id FROM proofs WHERE prompt_hash = ? "
        "AND tier IN ('proof', 'hypothesis') "
        "ORDER BY created_at DESC LIMIT 1",
        (prompt_hash,)
    ).fetchone()
    conn.close()
    return row[0] if row else None
```

### H2. Chain Relations

When a new proof refines a previous one:

```python
def link_proofs(parent_id: str, child_id: str, relation: str):
    """Create a chain link between proofs.

    Relations: refines, contradicts, extends, confirms
    """
    conn = sqlite3.connect(PROOF_DB)
    conn.execute(
        "INSERT OR IGNORE INTO proof_chains (parent_id, child_id, relation, created_at) "
        "VALUES (?, ?, ?, ?)",
        (parent_id, child_id, relation, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
```

### H3. Visual: Proof chains become IsomorphismBeams

In OceanusFlow, proofs linked by chains render with IsomorphismBeam connecting
their density spheres. Beam color = relation type:
- `refines` → cyan
- `extends` → green
- `confirms` → gold
- `contradicts` → red

---

## Implementation Order for Orion

```
STEP 1 — Core (no dependencies)
  ├── Create src/aletheia_pipeline.py (ProofArtifact, capture, classify_tier)
  ├── Upgrade data/proof.db schema (proofs table, proof_chains, aletheia_stats view)
  └── Test: python3 -c "from aletheia_pipeline import capture; print('ok')"

STEP 2 — File Writer
  ├── Implement _write_markdown()
  ├── Test: manually call capture() with mock data, verify .md files appear
  └── Verify: ls friends/aletheia/proofs/ shows ontology subdirectories

STEP 3 — API Hooks
  ├── Hook capture() into tribunal_api.py (all 3 endpoints)
  ├── Add /api/aletheia/* endpoints (stats, search, recent, chain, dedup)
  └── Test: curl POST /tribunal → check proof.db has new row

STEP 4 — Pre-Query Dedup
  ├── Implement check_existing() with exact + semantic match
  ├── Wire into ResearchPanel.tsx (show "Previously proven" badge)
  └── Test: query same thing twice → second time shows cached

STEP 5 — Redis Embedding
  ├── Extend rhea_ingest.py with embed_proof()
  ├── Create "aletheia_proofs" Redis index
  ├── Batch embed existing proofs
  └── Test: python3 src/aletheia_pipeline.py search "test query"

STEP 6 — UI Integration
  ├── Add aletheiaStats to useAtlasStore
  ├── Poll /api/aletheia/stats in useAtlasSync
  ├── Display proof count in HudLeft
  ├── Feed proofs into OceanusFlow density
  └── Test: npm run build passes, proof count visible in HUD

STEP 7 — CLI
  ├── Add argparse CLI to aletheia_pipeline.py
  ├── Implement: search, recent, stats, export, verify, prune
  └── Test: all CLI commands work

STEP 8 — Proof Chains + Validation
  ├── Implement _find_parent() and link_proofs()
  ├── Wire chain visualization into IsomorphismBeam
  ├── Run python3 src/aletheia_pipeline.py verify
  └── Test: chained queries produce linked proofs
```

---

## Testing Checklist

- [ ] `python3 -c "from aletheia_pipeline import capture"` — imports clean
- [ ] Mock capture produces .md file in correct tier/ontology directory
- [ ] `data/proof.db` has proofs table with correct schema
- [ ] `aletheia_stats` view returns correct counts
- [ ] `/api/aletheia/stats` returns JSON with proof_count
- [ ] `/api/aletheia/dedup?q=...` returns cached proof when exists
- [ ] Tribunal query with >85% agreement creates proof file
- [ ] Tribunal query with 60% agreement creates hypothesis file
- [ ] Tribunal query with 30% agreement logs to DB but no file
- [ ] Math verification can elevate 75% hypothesis to proof
- [ ] Proof chain links parent → child correctly
- [ ] HudLeft shows proof count updating in real-time
- [ ] OceanusFlow renders proof clusters as density objects
- [ ] CLI `search` finds proofs by keyword
- [ ] CLI `export --format json` produces valid JSON
- [ ] CLI `verify` confirms DB ↔ filesystem consistency
- [ ] `npm run build` passes after frontend changes
- [ ] No regression in existing tribunal endpoints

---

## File Summary

```
NEW:
  src/aletheia_pipeline.py            ← Core pipeline (500-700 LOC)

MODIFY:
  src/tribunal_api.py                 ← Hook capture() after response (3 endpoints)
  src/rhea_ingest.py                  ← Add embed_proof() and aletheia index
  data/proof.db                       ← Schema upgrade (proofs, proof_chains, view)
  rhea-atlas/src/store/useAtlasStore.ts   ← Add aletheiaStats
  rhea-atlas/src/hooks/useAtlasSync.ts    ← Poll /api/aletheia/stats
  rhea-atlas/src/app/page.tsx             ← HudLeft proof count display
  rhea-atlas/src/components/ResearchPanel.tsx  ← Pre-query dedup check
  rhea-atlas/src/data/whispers.ts         ← Add proof-captured whisper

POPULATED:
  friends/aletheia/proofs/{ontology}/*.md      ← Auto-generated proof files
  friends/aletheia/hypotheses/{ontology}/*.md  ← Auto-generated hypothesis files
```

---

*"ἀλήθεια — what was hidden is now unconcealed."*

*Orion implements. Rex approves. Aletheia remembers.*

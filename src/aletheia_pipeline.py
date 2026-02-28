"""
Aletheia Pipeline — Proof capture, storage, and retrieval.
ἀλήθεια — 'un-concealment': truth as the act of revealing what was hidden.

Usage:
    python3 src/aletheia_pipeline.py stats
    python3 src/aletheia_pipeline.py search "query"
    python3 src/aletheia_pipeline.py recent [--limit 20]
    python3 src/aletheia_pipeline.py export --format json --output proofs.json
    python3 src/aletheia_pipeline.py verify
    python3 src/aletheia_pipeline.py prune --older-than 30
"""

import hashlib
import json
import logging
import sqlite3
import os
import sys
import argparse
import csv
import threading
import requests as _requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, Literal, List, Dict, Any

_log = logging.getLogger("aletheia")

# ═══════════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════════

ROOT = Path(__file__).parent.parent
PROOF_DB = ROOT / "data" / "proof.db"
ALETHEIA_ROOT = ROOT / "friends" / "aletheia"
PROOFS_DIR = ALETHEIA_ROOT / "proofs"
HYPOTHESES_DIR = ALETHEIA_ROOT / "hypotheses"

# ═══════════════════════════════════════════════════════════════════════
# FIRESTORE SYNC (persistent storage across Cloud Run deploys)
# ═══════════════════════════════════════════════════════════════════════

_FS_PROJECT = os.environ.get("GCP_PROJECT", "rhea-office-sync")
_FS_COLLECTION = "aletheia_proofs"
_FS_BASE = f"https://firestore.googleapis.com/v1/projects/{_FS_PROJECT}/databases/(default)/documents"
_fs_hydrated = False


def _fs_token() -> Optional[str]:
    """Get access token — works on Cloud Run (metadata) and local (gcloud)."""
    # Cloud Run: use metadata server
    try:
        r = _requests.get(
            "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
            headers={"Metadata-Flavor": "Google"}, timeout=2)
        if r.ok:
            return r.json().get("access_token")
    except Exception:
        pass
    # Local: use gcloud
    try:
        import subprocess
        tok = subprocess.check_output(
            ["gcloud", "auth", "application-default", "print-access-token"],
            stderr=subprocess.DEVNULL, timeout=5).decode().strip()
        if tok:
            return tok
    except Exception:
        pass
    return None


def _fs_write(proof_id: str, data: Dict):
    """Write proof to Firestore (fire-and-forget in background thread)."""
    def _do():
        try:
            tok = _fs_token()
            if not tok:
                return
            fields = {}
            for k, v in data.items():
                if isinstance(v, bool):
                    fields[k] = {"booleanValue": v}
                elif isinstance(v, int):
                    fields[k] = {"integerValue": str(v)}
                elif isinstance(v, float):
                    fields[k] = {"doubleValue": v}
                elif v is None:
                    fields[k] = {"nullValue": None}
                else:
                    fields[k] = {"stringValue": str(v)}
            _requests.patch(
                f"{_FS_BASE}/{_FS_COLLECTION}/{proof_id}",
                json={"fields": fields},
                headers={"Authorization": f"Bearer {tok}"},
                timeout=10)
        except Exception as e:
            _log.warning(f"Firestore write failed for {proof_id}: {e}")
    threading.Thread(target=_do, daemon=True).start()


def _fs_hydrate_sqlite():
    """On first boot, pull all proofs from Firestore into local SQLite."""
    global _fs_hydrated
    if _fs_hydrated:
        return
    _fs_hydrated = True
    try:
        tok = _fs_token()
        if not tok:
            _log.info("No Firestore token — skipping hydration")
            return
        conn = sqlite3.connect(str(PROOF_DB))
        local_count = conn.execute("SELECT COUNT(*) FROM proofs").fetchone()[0]
        conn.close()
        if local_count > 0:
            _log.info(f"SQLite has {local_count} proofs — skipping Firestore hydration")
            return
        # Fetch all docs from Firestore (paginated)
        all_docs = []
        page_token = None
        while True:
            params = {"pageSize": 300}
            if page_token:
                params["pageToken"] = page_token
            r = _requests.get(
                f"{_FS_BASE}/{_FS_COLLECTION}",
                headers={"Authorization": f"Bearer {tok}"},
                params=params, timeout=30)
            if not r.ok:
                _log.warning(f"Firestore hydration fetch failed: {r.status_code}")
                break
            body = r.json()
            docs = body.get("documents", [])
            all_docs.extend(docs)
            page_token = body.get("nextPageToken")
            if not page_token:
                break

        if not all_docs:
            _log.info("Firestore empty — nothing to hydrate")
            return

        conn = _get_conn_raw()
        inserted = 0
        for doc in all_docs:
            fields = doc.get("fields", {})
            row = {}
            for k, v in fields.items():
                if "stringValue" in v:
                    row[k] = v["stringValue"]
                elif "integerValue" in v:
                    row[k] = int(v["integerValue"])
                elif "doubleValue" in v:
                    row[k] = float(v["doubleValue"])
                elif "booleanValue" in v:
                    row[k] = v["booleanValue"]
                else:
                    row[k] = None
            if "id" not in row or "prompt" not in row:
                continue
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO proofs "
                    "(id, type, tier, prompt, prompt_hash, ontology, mode, consensus_text, "
                    "agreement_score, confidence, models, agreement_points, divergence_points, "
                    "math_verification, stance_summary, pairwise_similarity, analysis_method, "
                    "rounds_completed, convergence_achieved, parent_id, session_id, file_path, "
                    "created_at, tokens_total, latency_total_s, raw_responses) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        row.get("id"), row.get("type", "consensus"), row.get("tier", "proof"),
                        row.get("prompt", ""), row.get("prompt_hash", ""),
                        row.get("ontology", "general"), row.get("mode", "manual"),
                        row.get("consensus_text", ""),
                        float(row.get("agreement_score", 0)),
                        float(row.get("confidence", 0)),
                        row.get("models", "[]"),
                        row.get("agreement_points", "[]"),
                        row.get("divergence_points", "[]"),
                        row.get("math_verification", "{}"),
                        row.get("stance_summary", "{}"),
                        row.get("pairwise_similarity", "{}"),
                        row.get("analysis_method", ""),
                        int(row.get("rounds_completed", 0)),
                        bool(row.get("convergence_achieved", False)),
                        row.get("parent_id"),
                        row.get("session_id"),
                        row.get("file_path"),
                        row.get("created_at", ""),
                        int(row.get("tokens_total", 0)),
                        float(row.get("latency_total_s", 0)),
                        row.get("raw_responses", "[]"),
                    ))
                inserted += 1
            except Exception as e:
                _log.warning(f"Hydration insert failed: {e}")
        conn.commit()
        conn.close()
        _log.info(f"Hydrated {inserted}/{len(all_docs)} proofs from Firestore")
    except Exception as e:
        _log.warning(f"Firestore hydration failed: {e}")


def _get_conn_raw() -> sqlite3.Connection:
    """Get SQLite connection with schema but WITHOUT hydration (avoids recursion)."""
    PROOF_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(PROOF_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_SCHEMA_SQL)
    try:
        conn.execute("DROP VIEW IF EXISTS aletheia_stats")
        conn.executescript(_STATS_VIEW_SQL)
    except Exception:
        pass
    return conn


# ═══════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════

ProofType = Literal["consensus", "agreement", "divergence", "math", "ice"]
ProofTier = Literal["proof", "hypothesis", "noise"]


@dataclass
class ProofArtifact:
    id: str
    type: ProofType
    tier: ProofTier
    prompt: str
    prompt_hash: str
    ontology: str
    mode: str
    consensus_text: str
    agreement_score: float
    confidence: float
    models: List[str]
    agreement_points: List[str]
    divergence_points: List[str]
    math_verification: Dict[str, Any]
    stance_summary: Dict[str, Any]
    pairwise_similarity: Dict[str, Any]
    analysis_method: str
    rounds_completed: int
    convergence_achieved: bool
    parent_id: Optional[str]
    session_id: Optional[str]
    file_path: Optional[str]
    created_at: str
    tokens_total: int
    latency_total_s: float
    raw_responses: List[Dict[str, Any]]


# ═══════════════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════════════

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS proofs (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    tier TEXT NOT NULL,
    prompt TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,
    ontology TEXT NOT NULL DEFAULT 'general',
    mode TEXT NOT NULL,
    consensus_text TEXT,
    agreement_score REAL NOT NULL,
    confidence REAL NOT NULL,
    models TEXT NOT NULL,
    agreement_points TEXT,
    divergence_points TEXT,
    math_verification TEXT,
    stance_summary TEXT,
    pairwise_similarity TEXT,
    analysis_method TEXT,
    rounds_completed INTEGER DEFAULT 0,
    convergence_achieved BOOLEAN DEFAULT FALSE,
    parent_id TEXT,
    session_id TEXT,
    file_path TEXT,
    created_at TEXT NOT NULL,
    tokens_total INTEGER DEFAULT 0,
    latency_total_s REAL DEFAULT 0.0,
    raw_responses TEXT,
    embedded BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (parent_id) REFERENCES proofs(id)
);

CREATE INDEX IF NOT EXISTS idx_proofs_ontology ON proofs(ontology);
CREATE INDEX IF NOT EXISTS idx_proofs_score ON proofs(agreement_score);
CREATE INDEX IF NOT EXISTS idx_proofs_tier ON proofs(tier);
CREATE INDEX IF NOT EXISTS idx_proofs_type ON proofs(type);
CREATE INDEX IF NOT EXISTS idx_proofs_prompt_hash ON proofs(prompt_hash);
CREATE INDEX IF NOT EXISTS idx_proofs_created ON proofs(created_at);

CREATE TABLE IF NOT EXISTS proof_chains (
    parent_id TEXT NOT NULL,
    child_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (parent_id, child_id),
    FOREIGN KEY (parent_id) REFERENCES proofs(id),
    FOREIGN KEY (child_id) REFERENCES proofs(id)
);
"""

_STATS_VIEW_SQL = """
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
"""


def _get_conn() -> sqlite3.Connection:
    """Get SQLite connection with schema initialized. Hydrates from Firestore on first call."""
    conn = _get_conn_raw()
    _fs_hydrate_sqlite()
    return conn


# ═══════════════════════════════════════════════════════════════════════
# TIER CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════

def classify_tier(agreement_score: float, confidence: float,
                  math_verification: Optional[Dict] = None) -> ProofTier:
    """
    Determine if result is proof, hypothesis, or noise.

    proof      — agreement >= 0.85 OR (>= 0.75 AND math verified)
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
        return "proof"
    if agreement_score >= 0.50:
        return "hypothesis"
    return "noise"


def _detect_proof_type(report: Dict, meta: Dict) -> ProofType:
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


# ═══════════════════════════════════════════════════════════════════════
# PARENT DETECTION (proof chains)
# ═══════════════════════════════════════════════════════════════════════

def _find_parent(prompt_hash: str) -> Optional[str]:
    """Find most recent proof with same prompt hash."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT id FROM proofs WHERE prompt_hash = ? "
        "AND tier IN ('proof', 'hypothesis') "
        "ORDER BY created_at DESC LIMIT 1",
        (prompt_hash,)
    ).fetchone()
    conn.close()
    return row["id"] if row else None


def link_proofs(parent_id: str, child_id: str, relation: str):
    """Create a chain link between proofs.

    Relations: refines, contradicts, extends, confirms
    """
    conn = _get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO proof_chains (parent_id, child_id, relation, created_at) "
        "VALUES (?, ?, ?, ?)",
        (parent_id, child_id, relation, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════════════
# MARKDOWN FILE WRITER
# ═══════════════════════════════════════════════════════════════════════

def _write_markdown(artifact: ProofArtifact) -> str:
    """Write proof artifact as structured markdown. Returns relative path."""
    base_dir = PROOFS_DIR if artifact.tier == "proof" else HYPOTHESES_DIR
    ontology_dir = artifact.ontology.lower().replace(" ", "_").replace("/", "_")
    target_dir = base_dir / ontology_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    filepath = target_dir / f"{artifact.id}.md"

    title = artifact.prompt[:80].strip()
    if len(artifact.prompt) > 80:
        title += "..."

    tier_badge = "PROVEN" if artifact.tier == "proof" else "HYPOTHESIS"
    models_str = ", ".join(artifact.models)

    lines = [
        f"# [{tier_badge}] {title}",
        f"> Ontology: {artifact.ontology} | Agreement: {artifact.agreement_score:.0%} | Confidence: {artifact.confidence:.0%}",
        f"> Models: {models_str}",
        f"> Mode: {artifact.mode} | Method: {artifact.analysis_method} | Date: {artifact.created_at}",
        f"> ID: {artifact.id}",
        "",
        "## Consensus",
        artifact.consensus_text or "(no consensus text)",
        "",
        "## Agreement Points",
    ]

    if artifact.agreement_points:
        for point in artifact.agreement_points:
            lines.append(f"- {point}")
    else:
        lines.append("- (none recorded)")

    if artifact.divergence_points:
        lines.append("")
        lines.append("## Divergence Points")
        for point in artifact.divergence_points:
            lines.append(f"- {point}")

    if artifact.math_verification and artifact.math_verification.get("domains_tested"):
        lines.append("")
        lines.append("## Mathematical Verification")
        for domain, verdict in artifact.math_verification.get("verdicts", {}).items():
            tag = "PASS" if verdict == "verified" else "FAIL" if verdict == "falsified" else "SKIP"
            lines.append(f"- [{tag}] {domain}: {verdict}")

    if artifact.stance_summary:
        lines.append("")
        lines.append("## Stance Summary")
        for model, stance in artifact.stance_summary.items():
            lines.append(f"- **{model}**: {stance}")

    lines.extend([
        "",
        "## Metadata",
        f"- Type: {artifact.type}",
        f"- Rounds: {artifact.rounds_completed} | Converged: {artifact.convergence_achieved}",
        f"- Tokens: {artifact.tokens_total} | Latency: {artifact.latency_total_s:.1f}s",
        f"- Parent: {artifact.parent_id or 'none (root)'}",
        f"- Session: {artifact.session_id or 'unknown'}",
    ])

    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(filepath.relative_to(ROOT))


# ═══════════════════════════════════════════════════════════════════════
# DB STORAGE
# ═══════════════════════════════════════════════════════════════════════

def _store_to_db(artifact: ProofArtifact):
    """Store proof artifact to SQLite + Firestore (persistent)."""
    conn = _get_conn()
    data = {
        "id": artifact.id, "type": artifact.type, "tier": artifact.tier,
        "prompt": artifact.prompt, "prompt_hash": artifact.prompt_hash,
        "ontology": artifact.ontology, "mode": artifact.mode,
        "consensus_text": artifact.consensus_text,
        "agreement_score": artifact.agreement_score,
        "confidence": artifact.confidence,
        "models": json.dumps(artifact.models),
        "agreement_points": json.dumps(artifact.agreement_points),
        "divergence_points": json.dumps(artifact.divergence_points),
        "math_verification": json.dumps(artifact.math_verification),
        "stance_summary": json.dumps(artifact.stance_summary),
        "pairwise_similarity": json.dumps(artifact.pairwise_similarity),
        "analysis_method": artifact.analysis_method,
        "rounds_completed": artifact.rounds_completed,
        "convergence_achieved": artifact.convergence_achieved,
        "parent_id": artifact.parent_id, "session_id": artifact.session_id,
        "file_path": artifact.file_path, "created_at": artifact.created_at,
        "tokens_total": artifact.tokens_total,
        "latency_total_s": artifact.latency_total_s,
        "raw_responses": json.dumps(artifact.raw_responses),
    }
    conn.execute(
        "INSERT OR REPLACE INTO proofs "
        "(id, type, tier, prompt, prompt_hash, ontology, mode, consensus_text, "
        "agreement_score, confidence, models, agreement_points, divergence_points, "
        "math_verification, stance_summary, pairwise_similarity, analysis_method, "
        "rounds_completed, convergence_achieved, parent_id, session_id, file_path, "
        "created_at, tokens_total, latency_total_s, raw_responses) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            data["id"], data["type"], data["tier"],
            data["prompt"], data["prompt_hash"],
            data["ontology"], data["mode"], data["consensus_text"],
            data["agreement_score"], data["confidence"],
            data["models"], data["agreement_points"], data["divergence_points"],
            data["math_verification"], data["stance_summary"],
            data["pairwise_similarity"], data["analysis_method"],
            data["rounds_completed"], data["convergence_achieved"],
            data["parent_id"], data["session_id"], data["file_path"],
            data["created_at"], data["tokens_total"], data["latency_total_s"],
            data["raw_responses"],
        )
    )
    conn.commit()
    conn.close()
    # Persist to Firestore (async, won't block)
    _fs_write(artifact.id, data)


def _log_noise(proof_id: str, prompt_hash: str, agreement_score: float,
               created_at: str, meta: Dict):
    """Log noise-tier results to DB without creating a file."""
    conn = _get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO proofs "
        "(id, type, tier, prompt, prompt_hash, ontology, mode, "
        "agreement_score, confidence, models, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            proof_id, "consensus", "noise",
            meta.get("prompt", ""), prompt_hash,
            meta.get("ontology", "general"), meta.get("mode", "tribunal"),
            agreement_score, 0.0, "[]", created_at,
        )
    )
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════════════
# MAIN CAPTURE FUNCTION
# ═══════════════════════════════════════════════════════════════════════

def capture(tribunal_response: Dict, consensus_report: Dict,
            raw_responses: List[Dict], request_meta: Dict) -> Optional[ProofArtifact]:
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
    prompt = request_meta.get("prompt", "")
    now = datetime.now(timezone.utc).isoformat()
    proof_id = hashlib.sha256(f"{prompt}:{now}".encode()).hexdigest()[:24]
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

    agreement_score = consensus_report.get("agreement_score", 0.0)
    confidence = consensus_report.get("confidence", 0.0)
    math_ver = consensus_report.get("math_verification", {})

    tier = classify_tier(agreement_score, confidence, math_ver)

    if tier == "noise":
        _log_noise(proof_id, prompt_hash, agreement_score, now, request_meta)
        return None

    models = [r.get("model", "unknown") for r in raw_responses if not r.get("error")]
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
        math_verification=math_ver or {},
        stance_summary=consensus_report.get("stance_summary", {}),
        pairwise_similarity=consensus_report.get("pairwise_similarity", {}),
        analysis_method=consensus_report.get("analysis_method", "unknown"),
        rounds_completed=consensus_report.get("rounds_completed", 0),
        convergence_achieved=consensus_report.get("convergence_achieved", False),
        parent_id=_find_parent(prompt_hash),
        session_id=request_meta.get("session_id"),
        file_path=None,
        created_at=now,
        tokens_total=tokens,
        latency_total_s=latency,
        raw_responses=[{
            "model": r.get("model"),
            "provider": r.get("provider"),
            "latency_s": r.get("latency_s"),
            "tokens": r.get("tokens_used"),
            "text_preview": r.get("text", "")[:200]
        } for r in raw_responses],
    )

    # Write markdown file
    artifact.file_path = _write_markdown(artifact)

    # Store to database
    _store_to_db(artifact)

    # Link to parent if found
    if artifact.parent_id:
        relation = "refines" if tier == "proof" else "extends"
        link_proofs(artifact.parent_id, artifact.id, relation)

    return artifact


# ═══════════════════════════════════════════════════════════════════════
# QUERY FUNCTIONS (used by API endpoints)
# ═══════════════════════════════════════════════════════════════════════

def get_stats() -> Dict[str, Any]:
    """Return aggregated proof library statistics."""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM aletheia_stats").fetchone()
    conn.close()
    if not row:
        return {
            "total_artifacts": 0, "proof_count": 0, "hypothesis_count": 0,
            "noise_count": 0, "avg_agreement": 0.0, "avg_confidence": 0.0,
            "ontology_count": 0, "unique_queries": 0, "total_tokens": 0,
            "last_capture": None,
        }
    return dict(row)


def get_proof(proof_id: str) -> Optional[Dict]:
    """Get a specific proof by ID."""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM proofs WHERE id = ?", (proof_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    for field_name in ("models", "agreement_points", "divergence_points",
                       "math_verification", "stance_summary",
                       "pairwise_similarity", "raw_responses"):
        if d.get(field_name) and isinstance(d[field_name], str):
            try:
                d[field_name] = json.loads(d[field_name])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


def get_recent(limit: int = 20, tier_filter: Optional[str] = None) -> List[Dict]:
    """Get most recent proofs/hypotheses."""
    conn = _get_conn()
    if tier_filter:
        rows = conn.execute(
            "SELECT id, type, tier, prompt, ontology, agreement_score, confidence, "
            "created_at FROM proofs WHERE tier = ? ORDER BY created_at DESC LIMIT ?",
            (tier_filter, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, type, tier, prompt, ontology, agreement_score, confidence, "
            "created_at FROM proofs WHERE tier != 'noise' ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_by_ontology(ontology: str, limit: int = 50) -> List[Dict]:
    """Get all proofs for a specific ontology."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, type, tier, prompt, agreement_score, confidence, created_at "
        "FROM proofs WHERE ontology = ? AND tier != 'noise' "
        "ORDER BY agreement_score DESC LIMIT ?",
        (ontology, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_chain(proof_id: str) -> Dict:
    """Get proof chain (ancestry + descendants)."""
    conn = _get_conn()

    # Ancestors
    ancestors = []
    current = proof_id
    for _ in range(20):  # max depth
        row = conn.execute(
            "SELECT parent_id, relation FROM proof_chains WHERE child_id = ?",
            (current,)
        ).fetchone()
        if not row:
            break
        ancestors.append({"id": row["parent_id"], "relation": row["relation"]})
        current = row["parent_id"]

    # Descendants
    descendants = conn.execute(
        "SELECT child_id as id, relation FROM proof_chains WHERE parent_id = ?",
        (proof_id,)
    ).fetchall()

    conn.close()
    return {
        "proof_id": proof_id,
        "ancestors": ancestors,
        "descendants": [dict(d) for d in descendants],
    }


def check_existing(query: str, threshold: float = 0.85) -> Dict:
    """Pre-query dedup: check if this question has already been answered."""
    prompt_hash = hashlib.sha256(query.encode()).hexdigest()[:16]

    conn = _get_conn()
    row = conn.execute(
        "SELECT id, agreement_score, consensus_text, tier FROM proofs "
        "WHERE prompt_hash = ? AND tier = 'proof' "
        "ORDER BY agreement_score DESC LIMIT 1",
        (prompt_hash,)
    ).fetchone()
    conn.close()

    if row:
        return {
            "found": True,
            "proof_id": row["id"],
            "agreement_score": row["agreement_score"],
            "consensus_preview": (row["consensus_text"] or "")[:300],
            "recommendation": "use_cached",
        }

    # TODO: Add Redis semantic similarity search when embeddings are live
    # from rhea_ingest import search as redis_search
    # results = redis_search(query, k=3, index_name="aletheia_proofs")

    return {
        "found": False,
        "proof_id": None,
        "agreement_score": 0.0,
        "consensus_preview": "",
        "recommendation": "no_match",
    }


def search_proofs(query: str, k: int = 5, tier_filter: Optional[str] = None) -> List[Dict]:
    """Search proofs by keyword (simple LIKE search; Redis semantic search TODO)."""
    conn = _get_conn()
    sql = (
        "SELECT id, type, tier, prompt, ontology, agreement_score, confidence, "
        "consensus_text, created_at FROM proofs "
        "WHERE (prompt LIKE ? OR consensus_text LIKE ?) AND tier != 'noise'"
    )
    params: list = [f"%{query}%", f"%{query}%"]

    if tier_filter:
        sql += " AND tier = ?"
        params.append(tier_filter)

    sql += " ORDER BY agreement_score DESC LIMIT ?"
    params.append(k)

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════
# VERIFICATION & MAINTENANCE
# ═══════════════════════════════════════════════════════════════════════

def verify() -> Dict:
    """Verify DB ↔ filesystem consistency."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, file_path, tier FROM proofs WHERE tier != 'noise' AND file_path IS NOT NULL"
    ).fetchall()
    conn.close()

    missing_files = []
    orphan_files = []
    ok_count = 0

    db_paths = set()
    for row in rows:
        fp = ROOT / row["file_path"]
        db_paths.add(str(fp))
        if fp.exists():
            ok_count += 1
        else:
            missing_files.append({"id": row["id"], "expected": row["file_path"]})

    # Check for orphan files (on disk but not in DB)
    for tier_dir in [PROOFS_DIR, HYPOTHESES_DIR]:
        if tier_dir.exists():
            for md_file in tier_dir.rglob("*.md"):
                if str(md_file) not in db_paths:
                    orphan_files.append(str(md_file.relative_to(ROOT)))

    return {
        "total_in_db": len(rows),
        "files_ok": ok_count,
        "missing_files": missing_files,
        "orphan_files": orphan_files,
        "healthy": len(missing_files) == 0 and len(orphan_files) == 0,
    }


def prune(older_than_days: int = 30):
    """Remove noise entries older than N days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=older_than_days)).isoformat()
    conn = _get_conn()
    result = conn.execute(
        "DELETE FROM proofs WHERE tier = 'noise' AND created_at < ?", (cutoff,)
    )
    count = result.rowcount
    conn.commit()
    conn.close()
    return {"pruned": count, "cutoff": cutoff}


def export_proofs(fmt: str = "json", output: Optional[str] = None,
                  tier_filter: Optional[str] = None) -> str:
    """Export all proofs to JSON or CSV."""
    conn = _get_conn()
    sql = "SELECT * FROM proofs WHERE tier != 'noise'"
    params = []
    if tier_filter:
        sql += " AND tier = ?"
        params.append(tier_filter)
    sql += " ORDER BY created_at DESC"

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    data = [dict(r) for r in rows]

    if fmt == "json":
        # Parse JSON fields
        for d in data:
            for field_name in ("models", "agreement_points", "divergence_points",
                               "math_verification", "stance_summary",
                               "pairwise_similarity", "raw_responses"):
                if d.get(field_name) and isinstance(d[field_name], str):
                    try:
                        d[field_name] = json.loads(d[field_name])
                    except (json.JSONDecodeError, TypeError):
                        pass

        content = json.dumps(data, indent=2, ensure_ascii=False)
        ext = ".json"
    elif fmt == "csv":
        if not data:
            content = ""
        else:
            from io import StringIO
            buf = StringIO()
            writer = csv.DictWriter(buf, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            content = buf.getvalue()
        ext = ".csv"
    else:
        raise ValueError(f"Unknown format: {fmt}")

    if output:
        outpath = Path(output)
    else:
        outpath = ROOT / f"data/aletheia_export{ext}"

    outpath.write_text(content, encoding="utf-8")
    return str(outpath)


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

def _cli():
    parser = argparse.ArgumentParser(
        description="Aletheia — Proof Library Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    # stats
    sub.add_parser("stats", help="Show proof library statistics")

    # search
    p_search = sub.add_parser("search", help="Search proofs by keyword")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--k", type=int, default=10, help="Max results")
    p_search.add_argument("--tier", choices=["proof", "hypothesis"], help="Filter by tier")

    # recent
    p_recent = sub.add_parser("recent", help="Show recent proofs")
    p_recent.add_argument("--limit", type=int, default=20)
    p_recent.add_argument("--tier", choices=["proof", "hypothesis"])

    # export
    p_export = sub.add_parser("export", help="Export proofs to file")
    p_export.add_argument("--format", choices=["json", "csv"], default="json")
    p_export.add_argument("--output", help="Output file path")
    p_export.add_argument("--tier", choices=["proof", "hypothesis"])

    # verify
    sub.add_parser("verify", help="Verify DB/filesystem consistency")

    # prune
    p_prune = sub.add_parser("prune", help="Remove old noise entries")
    p_prune.add_argument("--older-than", type=int, default=30, help="Days")

    # chain
    p_chain = sub.add_parser("chain", help="Show proof chain")
    p_chain.add_argument("proof_id", help="Proof ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "stats":
        stats = get_stats()
        print(f"Aletheia Proof Library")
        print(f"  Proofs:      {stats['proof_count']}")
        print(f"  Hypotheses:  {stats['hypothesis_count']}")
        print(f"  Noise:       {stats['noise_count']}")
        print(f"  Total:       {stats['total_artifacts']}")
        print(f"  Avg agree:   {(stats['avg_agreement'] or 0):.1%}")
        print(f"  Avg conf:    {(stats['avg_confidence'] or 0):.1%}")
        print(f"  Ontologies:  {stats['ontology_count']}")
        print(f"  Unique Qs:   {stats['unique_queries']}")
        print(f"  Tokens:      {stats['total_tokens'] or 0:,}")
        print(f"  Last:        {stats['last_capture'] or 'never'}")

    elif args.command == "search":
        results = search_proofs(args.query, k=args.k, tier_filter=args.tier)
        if not results:
            print("No proofs found.")
            return
        for r in results:
            print(f"  [{r['tier'].upper():10}] {r['agreement_score']:.0%} | "
                  f"{r['ontology']:12} | {r['prompt'][:60]}")
            print(f"             id={r['id']}  {r['created_at']}")

    elif args.command == "recent":
        results = get_recent(limit=args.limit, tier_filter=args.tier)
        if not results:
            print("No proofs found.")
            return
        for r in results:
            print(f"  [{r['tier'].upper():10}] {r['agreement_score']:.0%} | "
                  f"{r['ontology']:12} | {r['prompt'][:60]}")

    elif args.command == "export":
        path = export_proofs(fmt=args.format, output=args.output, tier_filter=args.tier)
        print(f"Exported to: {path}")

    elif args.command == "verify":
        result = verify()
        status = "HEALTHY" if result["healthy"] else "ISSUES FOUND"
        print(f"Verification: {status}")
        print(f"  DB records: {result['total_in_db']}")
        print(f"  Files OK:   {result['files_ok']}")
        if result["missing_files"]:
            print(f"  Missing:    {len(result['missing_files'])}")
            for m in result["missing_files"][:5]:
                print(f"    - {m['id']}: {m['expected']}")
        if result["orphan_files"]:
            print(f"  Orphans:    {len(result['orphan_files'])}")
            for o in result["orphan_files"][:5]:
                print(f"    - {o}")

    elif args.command == "prune":
        result = prune(older_than_days=args.older_than)
        print(f"Pruned {result['pruned']} noise entries older than {args.older_than} days")

    elif args.command == "chain":
        chain = get_chain(args.proof_id)
        print(f"Proof chain for {args.proof_id}:")
        if chain["ancestors"]:
            print("  Ancestors:")
            for a in chain["ancestors"]:
                print(f"    <- {a['id']} ({a['relation']})")
        if chain["descendants"]:
            print("  Descendants:")
            for d in chain["descendants"]:
                print(f"    -> {d['id']} ({d['relation']})")
        if not chain["ancestors"] and not chain["descendants"]:
            print("  (root proof, no chain)")


if __name__ == "__main__":
    _cli()

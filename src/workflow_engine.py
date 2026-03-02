"""
workflow_engine.py — Workflow CRUD + DAG execution engine for Rhea Automation.

Stores workflows (nodes + edges) in SQLite, executes them as DAGs with
topological ordering, passing outputs between connected nodes.

Node types: tribunal, llm_call, aletheia_search, aletheia_store,
            http_request, transform, condition, office_send

Mount:
    from workflow_engine import workflow_router
    app.include_router(workflow_router, prefix="/workflows")
"""
from __future__ import annotations

import asyncio
import json
import sqlite3
import time
import traceback
import httpx
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DB_PATH = _PROJECT_ROOT / "data" / "workflows.db"

# ---------------------------------------------------------------------------
# Lazy imports (avoid circular import at module level)
# ---------------------------------------------------------------------------
_bridge = None
_broadcast = None


def _get_bridge():
    global _bridge
    if _bridge is None:
        from rhea_bridge import RheaBridge
        _bridge = RheaBridge()
    return _bridge


def _get_broadcast():
    global _broadcast
    if _broadcast is None:
        try:
            from tribunal_api import _broadcast_event
            _broadcast = _broadcast_event
        except ImportError:
            _broadcast = lambda e: None  # noqa: E731
    return _broadcast


# ---------------------------------------------------------------------------
# Available node types (returned by GET /workflows/node-types)
# ---------------------------------------------------------------------------
AVAILABLE_NODE_TYPES = {
    "tribunal": {
        "label": "Tribunal Consensus",
        "description": "Run multi-model tribunal consensus query.",
        "inputs": {"prompt": "string"},
        "outputs": {"consensus": "string", "agreement": "number", "confidence": "number"},
        "defaults": {"k": 5, "tier": "cheap", "mode": "local"},
    },
    "llm_call": {
        "label": "LLM Call",
        "description": "Direct LLM call via Rhea Bridge.",
        "inputs": {"prompt": "string"},
        "outputs": {"response": "string"},
        "defaults": {"model": None, "tier": "cheap"},
    },
    "aletheia_search": {
        "label": "Aletheia Search",
        "description": "Search the Aletheia proof store.",
        "inputs": {"query": "string"},
        "outputs": {"results": "array"},
        "defaults": {"k": 5},
    },
    "aletheia_store": {
        "label": "Aletheia Store",
        "description": "Store a proof in Aletheia.",
        "inputs": {"claim": "string", "evidence": "string", "verdict": "string"},
        "outputs": {"proof_id": "string"},
        "defaults": {},
    },
    "http_request": {
        "label": "HTTP Request",
        "description": "Make an HTTP request to any URL.",
        "inputs": {"url": "string"},
        "outputs": {"status": "number", "body": "string"},
        "defaults": {"method": "GET", "body": None, "headers": {}},
    },
    "transform": {
        "label": "Transform",
        "description": "JSON/text transform using a template string.",
        "inputs": {"data": "any", "template": "string"},
        "outputs": {"result": "any"},
        "defaults": {},
    },
    "office_send": {
        "label": "Office Send",
        "description": "Send a message to the virtual office outbox.",
        "inputs": {"sender": "string", "receiver": "string", "text": "string"},
        "outputs": {"id": "string"},
        "defaults": {},
    },
    "condition": {
        "label": "Condition",
        "description": "Branch execution based on a comparison.",
        "inputs": {"value": "any", "operator": "string", "threshold": "any"},
        "outputs": {"true_branch": "boolean", "false_branch": "boolean"},
        "defaults": {"operator": ">="},
    },
}

# ---------------------------------------------------------------------------
# SQLite helpers
# ---------------------------------------------------------------------------

def _get_conn() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _ensure_tables(conn)
    return conn


def _ensure_tables(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS workflows (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            nodes TEXT NOT NULL,
            edges TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS executions (
            id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            results TEXT,
            started_at TEXT,
            completed_at TEXT,
            error TEXT,
            FOREIGN KEY (workflow_id) REFERENCES workflows(id)
        );
        CREATE TABLE IF NOT EXISTS scheduler_loops (
            id TEXT PRIMARY KEY,
            prompt TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            target_agreement REAL NOT NULL DEFAULT 0.9,
            max_iterations INTEGER NOT NULL DEFAULT 20,
            interval_seconds REAL NOT NULL DEFAULT 30,
            k INTEGER NOT NULL DEFAULT 5,
            tier TEXT NOT NULL DEFAULT 'cheap',
            mode TEXT NOT NULL DEFAULT 'local',
            current_iteration INTEGER DEFAULT 0,
            best_agreement REAL DEFAULT 0.0,
            best_consensus TEXT,
            history TEXT,
            started_at TEXT,
            completed_at TEXT,
            error TEXT
        );
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class NodePosition(BaseModel):
    x: float = 0
    y: float = 0


class WorkflowNode(BaseModel):
    id: str
    type: str
    position: NodePosition = Field(default_factory=NodePosition)
    data: dict = Field(default_factory=dict)


class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    nodes: list[WorkflowNode]
    edges: list[WorkflowEdge] = Field(default_factory=list)


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    nodes: Optional[list[WorkflowNode]] = None
    edges: Optional[list[WorkflowEdge]] = None


class SchedulerLoopRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="The claim or question to reach consensus on")
    target_agreement: float = Field(0.9, ge=0.5, le=1.0, description="Stop when agreement >= this (0.9 = 90%)")
    max_iterations: int = Field(20, ge=1, le=100, description="Max tribunal rounds before giving up")
    interval_seconds: float = Field(30, ge=5, le=600, description="Seconds between iterations")
    k: int = Field(5, ge=2, le=10, description="Number of models per tribunal call")
    tier: str = Field("cheap", description="Model cost tier")
    mode: str = Field("local", description="Execution mode (local/sceptic/ice)")
    refine_prompt: bool = Field(True, description="Auto-refine prompt based on divergence points")


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
workflow_router = APIRouter(tags=["workflows"])


@workflow_router.get("/node-types")
async def get_node_types():
    """Return all available node type definitions."""
    return AVAILABLE_NODE_TYPES


@workflow_router.post("")
async def create_workflow(req: WorkflowCreate):
    """Save a new workflow. Returns {id}."""
    wf_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO workflows (id, name, nodes, edges, created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (
                wf_id,
                req.name,
                json.dumps([n.model_dump() for n in req.nodes]),
                json.dumps([e.model_dump() for e in req.edges]),
                now,
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return {"id": wf_id}


@workflow_router.get("")
async def list_workflows():
    """List all workflows (summary: id, name, updated_at)."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT id, name, updated_at FROM workflows ORDER BY updated_at DESC"
        ).fetchall()
    finally:
        conn.close()
    return [{"id": r["id"], "name": r["name"], "updated_at": r["updated_at"]} for r in rows]


@workflow_router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get full workflow by ID."""
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,)).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {
        "id": row["id"],
        "name": row["name"],
        "nodes": json.loads(row["nodes"]),
        "edges": json.loads(row["edges"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@workflow_router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow and its executions."""
    conn = _get_conn()
    try:
        cur = conn.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Workflow not found")
        conn.execute("DELETE FROM executions WHERE workflow_id = ?", (workflow_id,))
        conn.commit()
    finally:
        conn.close()
    return {"deleted": workflow_id}


@workflow_router.post("/{workflow_id}/execute")
async def execute_workflow_endpoint(workflow_id: str):
    """Start executing a workflow (background). Returns {execution_id}."""
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,)).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Workflow not found")

    exec_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO executions (id, workflow_id, status, started_at) VALUES (?,?,?,?)",
            (exec_id, workflow_id, "running", now),
        )
        conn.commit()
    finally:
        conn.close()

    # Fire and forget — execution runs in the background
    asyncio.create_task(_run_workflow(exec_id, workflow_id))

    # Broadcast to radio
    _get_broadcast()({
        "id": f"workflow-exec-{exec_id[:8]}",
        "type": "workflow",
        "sender": "workflow_engine",
        "receiver": "all",
        "text": f"Workflow '{row['name']}' execution started → {exec_id[:8]}",
    })

    return {"execution_id": exec_id}


@workflow_router.get("/executions/{execution_id}")
async def get_execution(execution_id: str):
    """Get execution status and per-node results."""
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM executions WHERE id = ?", (execution_id,)).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Execution not found")
    return {
        "id": row["id"],
        "workflow_id": row["workflow_id"],
        "status": row["status"],
        "results": json.loads(row["results"]) if row["results"] else None,
        "started_at": row["started_at"],
        "completed_at": row["completed_at"],
        "error": row["error"],
    }


# ---------------------------------------------------------------------------
# DAG execution engine
# ---------------------------------------------------------------------------

def _topo_sort(nodes: list[dict], edges: list[dict]) -> list[str]:
    """Topological sort of node IDs. Raises ValueError on cycles."""
    node_ids = {n["id"] for n in nodes}
    in_degree: dict[str, int] = {nid: 0 for nid in node_ids}
    adj: dict[str, list[str]] = defaultdict(list)

    for e in edges:
        src, tgt = e["source"], e["target"]
        if src in node_ids and tgt in node_ids:
            adj[src].append(tgt)
            in_degree[tgt] = in_degree.get(tgt, 0) + 1

    queue = deque(nid for nid, deg in in_degree.items() if deg == 0)
    order: list[str] = []

    while queue:
        nid = queue.popleft()
        order.append(nid)
        for neighbor in adj[nid]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(order) != len(node_ids):
        raise ValueError("Workflow contains a cycle — cannot execute")
    return order


def _resolve_inputs(node: dict, edges: list[dict], results: dict[str, dict]) -> dict:
    """Resolve a node's inputs from upstream outputs via edges.

    For each edge targeting this node, merge the source node's outputs
    into this node's data dict. Explicit data values take precedence.
    """
    resolved = dict(node.get("data", {}))
    for edge in edges:
        if edge["target"] == node["id"]:
            src_id = edge["source"]
            src_handle = edge.get("sourceHandle")
            tgt_handle = edge.get("targetHandle")
            if src_id in results:
                src_out = results[src_id]
                if src_handle and tgt_handle:
                    # Wire specific output → specific input
                    if src_handle in src_out:
                        resolved[tgt_handle] = src_out[src_handle]
                elif tgt_handle and not src_handle:
                    # All source outputs → specific input key (JSON)
                    resolved[tgt_handle] = src_out
                else:
                    # Merge all source outputs into inputs
                    for k, v in src_out.items():
                        if k not in resolved:
                            resolved[k] = v
    return resolved


async def _run_workflow(exec_id: str, workflow_id: str):
    """Execute a workflow DAG. Runs as a background asyncio task."""
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,)).fetchone()
    finally:
        conn.close()

    if not row:
        _update_execution(exec_id, status="failed", error="Workflow not found")
        return

    nodes = json.loads(row["nodes"])
    edges = json.loads(row["edges"])
    node_map = {n["id"]: n for n in nodes}

    try:
        order = _topo_sort(nodes, edges)
    except ValueError as e:
        _update_execution(exec_id, status="failed", error=str(e))
        return

    results: dict[str, dict] = {}

    for node_id in order:
        node = node_map[node_id]
        node_type = node.get("type", "unknown")
        inputs = _resolve_inputs(node, edges, results)

        try:
            output = await _execute_node(node_type, inputs)
            results[node_id] = output
        except Exception as e:
            results[node_id] = {"error": str(e)}
            _update_execution(
                exec_id,
                status="failed",
                results=results,
                error=f"Node '{node_id}' ({node_type}) failed: {e}",
            )
            return

        # Persist intermediate results so polling shows progress
        _update_execution(exec_id, status="running", results=results)

    _update_execution(exec_id, status="completed", results=results)

    # Broadcast completion
    _get_broadcast()({
        "id": f"workflow-done-{exec_id[:8]}",
        "type": "workflow",
        "sender": "workflow_engine",
        "receiver": "all",
        "text": f"Workflow execution {exec_id[:8]} completed ({len(results)} nodes)",
    })


def _update_execution(exec_id: str, status: str, results: dict = None, error: str = None):
    """Update execution row in DB."""
    conn = _get_conn()
    try:
        now = datetime.now(timezone.utc).isoformat()
        completed = now if status in ("completed", "failed") else None
        conn.execute(
            "UPDATE executions SET status=?, results=?, completed_at=?, error=? WHERE id=?",
            (
                status,
                json.dumps(results) if results else None,
                completed,
                error,
                exec_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Node executors
# ---------------------------------------------------------------------------

async def _execute_node(node_type: str, inputs: dict) -> dict:
    """Dispatch to the correct executor based on node type."""
    executor = _NODE_EXECUTORS.get(node_type)
    if not executor:
        raise ValueError(f"Unknown node type: {node_type}")
    return await executor(inputs)


async def _exec_tribunal(inputs: dict) -> dict:
    """Run tribunal consensus query."""
    prompt = inputs.get("prompt", "")
    if not prompt:
        raise ValueError("tribunal node requires 'prompt' input")

    bridge = _get_bridge()
    k = int(inputs.get("k", 5))
    tier = inputs.get("tier", "cheap")
    mode = inputs.get("mode", "local")

    result = await asyncio.to_thread(
        bridge.tribunal,
        prompt=prompt,
        k=k,
        tier=tier,
        mode=mode,
    )

    report = result.consensus_report
    return {
        "consensus": report.get("consensus_text", result.consensus),
        "agreement": report.get("agreement_score", 0.0),
        "confidence": report.get("confidence", 0.0),
    }


async def _exec_llm_call(inputs: dict) -> dict:
    """Direct LLM call via bridge."""
    prompt = inputs.get("prompt", "")
    if not prompt:
        raise ValueError("llm_call node requires 'prompt' input")

    bridge = _get_bridge()
    tier = inputs.get("tier", "cheap")
    model = inputs.get("model")
    system = inputs.get("system", "")

    if model:
        resp = await asyncio.to_thread(
            bridge.ask,
            prompt=prompt,
            model=model,
            system=system,
        )
    else:
        resp = await asyncio.to_thread(
            bridge.ask_tier,
            tier=tier,
            prompt=prompt,
            system=system,
        )

    if resp.error:
        raise RuntimeError(f"LLM error: {resp.error}")
    return {"response": resp.text}


async def _exec_aletheia_search(inputs: dict) -> dict:
    """Search Aletheia proof store."""
    query = inputs.get("query", "")
    if not query:
        raise ValueError("aletheia_search node requires 'query' input")

    import aletheia_pipeline as aletheia
    k = int(inputs.get("k", 5))
    results = await asyncio.to_thread(aletheia.search_proofs, query, k)
    return {"results": results}


async def _exec_aletheia_store(inputs: dict) -> dict:
    """Store a proof directly into Aletheia's proof.db."""
    claim = inputs.get("claim", "")
    evidence = inputs.get("evidence", "")
    verdict = inputs.get("verdict", "")
    if not claim:
        raise ValueError("aletheia_store node requires 'claim' input")

    import aletheia_pipeline as aletheia
    import hashlib

    now = datetime.now(timezone.utc).isoformat()
    proof_id = hashlib.sha256(f"{claim}:{now}".encode()).hexdigest()[:24]

    conn = aletheia._get_conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO proofs "
            "(id, type, tier, prompt, prompt_hash, ontology, mode, consensus_text, "
            "agreement_score, confidence, models, agreement_points, divergence_points, "
            "math_verification, stance_summary, pairwise_similarity, analysis_method, "
            "rounds_completed, convergence_achieved, parent_id, session_id, file_path, "
            "created_at, tokens_total, latency_total_s, raw_responses) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                proof_id, "axiom", "gold", claim,
                hashlib.sha256(claim.encode()).hexdigest()[:16],
                "general", "workflow",
                verdict or evidence,
                1.0, 1.0,
                "[]", "[]", "[]", "{}", "{}", "{}", "workflow",
                1, True, None, None, None,
                now, 0, 0.0,
                json.dumps([{"claim": claim, "evidence": evidence, "verdict": verdict}]),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return {"proof_id": proof_id}


async def _exec_http_request(inputs: dict) -> dict:
    """Make an HTTP request."""
    url = inputs.get("url", "")
    if not url:
        raise ValueError("http_request node requires 'url' input")

    method = inputs.get("method", "GET").upper()
    body = inputs.get("body")
    headers = inputs.get("headers", {})
    if isinstance(headers, str):
        headers = json.loads(headers)

    async with httpx.AsyncClient(timeout=30.0) as client:
        kwargs: dict[str, Any] = {"headers": headers}
        if body and method in ("POST", "PUT", "PATCH"):
            kwargs["content"] = body if isinstance(body, str) else json.dumps(body)
            kwargs["headers"].setdefault("content-type", "application/json")

        resp = await client.request(method, url, **kwargs)

    try:
        resp_body = resp.json()
    except Exception:
        resp_body = resp.text

    return {"status": resp.status_code, "body": resp_body}


async def _exec_transform(inputs: dict) -> dict:
    """JSON/text transform using a Python-style template.

    Template uses {key} placeholders replaced from data dict.
    If template is empty, pass data through unchanged.
    """
    data = inputs.get("data", {})
    template = inputs.get("template", "")

    if not template:
        return {"result": data}

    if isinstance(data, dict):
        try:
            result = template.format(**data)
        except (KeyError, IndexError):
            result = template
    else:
        result = template.replace("{data}", str(data))

    # Try to parse as JSON if it looks like JSON
    if result.startswith(("{", "[")):
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            pass

    return {"result": result}


async def _exec_office_send(inputs: dict) -> dict:
    """Write a message to the virtual office outbox."""
    sender = inputs.get("sender", "WORKFLOW")
    receiver = inputs.get("receiver", "ALL")
    text = inputs.get("text", "")
    if not text:
        raise ValueError("office_send node requires 'text' input")

    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d_%H%M%S")
    msg_id = f"{sender}_{ts}_{uuid4().hex[:6]}"
    filename = f"{msg_id}.md"

    outbox = _PROJECT_ROOT / "opera" / "ops" / "virtual-office" / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)

    content = (
        f"# {sender} → {receiver}\n"
        f"**Time:** {now.isoformat()}\n"
        f"**Source:** workflow_engine\n\n"
        f"{text}\n"
    )
    (outbox / filename).write_text(content)

    # Also broadcast to radio
    _get_broadcast()({
        "id": msg_id,
        "type": "office",
        "sender": sender,
        "receiver": receiver,
        "text": text[:200],
    })

    return {"id": msg_id}


async def _exec_condition(inputs: dict) -> dict:
    """Evaluate a condition and return branch flags."""
    value = inputs.get("value")
    operator = inputs.get("operator", ">=")
    threshold = inputs.get("threshold")

    # Coerce to float for numeric comparisons
    try:
        val = float(value) if value is not None else 0
        thr = float(threshold) if threshold is not None else 0
    except (ValueError, TypeError):
        val = str(value)
        thr = str(threshold)

    ops = {
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        ">": lambda a, b: a > b,
        ">=": lambda a, b: a >= b,
        "<": lambda a, b: a < b,
        "<=": lambda a, b: a <= b,
        "contains": lambda a, b: str(b) in str(a),
    }

    compare = ops.get(operator, ops[">="])
    result = compare(val, thr)

    return {"true_branch": result, "false_branch": not result}


# Node type → executor mapping
_NODE_EXECUTORS = {
    "tribunal": _exec_tribunal,
    "llm_call": _exec_llm_call,
    "aletheia_search": _exec_aletheia_search,
    "aletheia_store": _exec_aletheia_store,
    "http_request": _exec_http_request,
    "transform": _exec_transform,
    "office_send": _exec_office_send,
    "condition": _exec_condition,
}


# ---------------------------------------------------------------------------
# Scheduler-Looper: run tribunal until consensus >= target
# ---------------------------------------------------------------------------

# In-memory set of active loop IDs (for cancellation)
_ACTIVE_LOOPS: set[str] = set()


@workflow_router.post("/scheduler/loop")
async def scheduler_loop_start(req: SchedulerLoopRequest):
    """Start a consensus loop. Runs tribunal repeatedly until agreement >= target or max_iterations.

    ComfyUI-style: submit a prompt, set your quality bar, walk away.
    The scheduler keeps refining until the result is brilliant.
    """
    loop_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    conn = _get_conn()
    try:
        conn.execute(
            """INSERT INTO scheduler_loops
               (id, prompt, status, target_agreement, max_iterations,
                interval_seconds, k, tier, mode, current_iteration,
                best_agreement, history, started_at)
               VALUES (?,?,?,?,?,?,?,?,?,0,0.0,'[]',?)""",
            (loop_id, req.prompt, "running", req.target_agreement,
             req.max_iterations, req.interval_seconds, req.k,
             req.tier, req.mode, now),
        )
        conn.commit()
    finally:
        conn.close()

    _ACTIVE_LOOPS.add(loop_id)
    asyncio.create_task(_run_loop(loop_id, req))

    _get_broadcast()({
        "id": f"loop-start-{loop_id[:8]}",
        "type": "scheduler",
        "sender": "scheduler",
        "receiver": "all",
        "text": f"Consensus loop started: target {req.target_agreement:.0%}, max {req.max_iterations} rounds",
    })

    return {"loop_id": loop_id, "status": "running"}


@workflow_router.get("/scheduler/loops")
async def scheduler_loop_list():
    """List all scheduler loops."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT id, prompt, status, target_agreement, current_iteration, "
            "max_iterations, best_agreement, started_at, completed_at "
            "FROM scheduler_loops ORDER BY started_at DESC"
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


@workflow_router.get("/scheduler/loops/{loop_id}")
async def scheduler_loop_status(loop_id: str):
    """Get full status of a scheduler loop including iteration history."""
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM scheduler_loops WHERE id = ?", (loop_id,)).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Loop not found")
    result = dict(row)
    result["history"] = json.loads(result["history"]) if result["history"] else []
    return result


@workflow_router.post("/scheduler/loops/{loop_id}/stop")
async def scheduler_loop_stop(loop_id: str):
    """Stop a running loop gracefully."""
    _ACTIVE_LOOPS.discard(loop_id)
    conn = _get_conn()
    try:
        conn.execute(
            "UPDATE scheduler_loops SET status='stopped', completed_at=? WHERE id=? AND status='running'",
            (datetime.now(timezone.utc).isoformat(), loop_id),
        )
        conn.commit()
    finally:
        conn.close()
    return {"loop_id": loop_id, "status": "stopped"}


async def _run_loop(loop_id: str, req: SchedulerLoopRequest):
    """Background task: run tribunal in a loop until consensus reached."""
    bridge = _get_bridge()
    history: list[dict] = []
    best_agreement = 0.0
    best_consensus = ""
    current_prompt = req.prompt

    for iteration in range(1, req.max_iterations + 1):
        if loop_id not in _ACTIVE_LOOPS:
            break  # cancelled

        try:
            # Choose execution mode
            if req.mode == "ice":
                result = await asyncio.to_thread(
                    bridge.tribunal,
                    prompt=current_prompt,
                    k=req.k,
                    tier=req.tier,
                    mode="ice",
                )
            elif req.mode == "sceptic":
                result = await asyncio.to_thread(
                    bridge.tribunal,
                    prompt=current_prompt,
                    k=req.k,
                    tier=req.tier,
                    mode="sceptic",
                )
            else:
                result = await asyncio.to_thread(
                    bridge.tribunal,
                    prompt=current_prompt,
                    k=req.k,
                    tier=req.tier,
                    mode="local",
                )

            report = result.consensus_report if hasattr(result, "consensus_report") else {}
            agreement = report.get("agreement_score", 0.0) if isinstance(report, dict) else 0.0
            consensus_text = report.get("consensus_text", getattr(result, "consensus", "")) if isinstance(report, dict) else ""
            divergence = report.get("divergence_points", []) if isinstance(report, dict) else []

            round_record = {
                "iteration": iteration,
                "agreement_score": agreement,
                "consensus": consensus_text[:500],
                "divergence_points": divergence[:5],
                "prompt_used": current_prompt[:200],
                "models_responded": report.get("models_responded", 0) if isinstance(report, dict) else 0,
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            history.append(round_record)

            if agreement > best_agreement:
                best_agreement = agreement
                best_consensus = consensus_text

            # Update DB with progress
            _update_loop(loop_id, iteration, best_agreement, best_consensus, history)

            # Broadcast progress
            _get_broadcast()({
                "id": f"loop-iter-{loop_id[:8]}-{iteration}",
                "type": "scheduler",
                "sender": "scheduler",
                "receiver": "all",
                "text": f"Loop {loop_id[:8]} iter {iteration}/{req.max_iterations}: agreement={agreement:.1%} (target={req.target_agreement:.0%})",
            })

            # Check exit condition
            if agreement >= req.target_agreement:
                _finalize_loop(loop_id, "converged", best_agreement, best_consensus, history)
                _ACTIVE_LOOPS.discard(loop_id)
                _get_broadcast()({
                    "id": f"loop-done-{loop_id[:8]}",
                    "type": "scheduler",
                    "sender": "scheduler",
                    "receiver": "all",
                    "text": f"CONVERGED at {agreement:.1%} after {iteration} iterations",
                })
                return

            # Auto-refine: if enabled, sharpen prompt using divergence points
            if req.refine_prompt and divergence:
                refinement = "; ".join(d[:80] for d in divergence[:3])
                current_prompt = (
                    f"{req.prompt}\n\n"
                    f"[Previous models diverged on: {refinement}]\n"
                    f"Please address these specific points of disagreement."
                )

        except Exception as e:
            round_record = {
                "iteration": iteration,
                "error": str(e),
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            history.append(round_record)
            _update_loop(loop_id, iteration, best_agreement, best_consensus, history)

        # Wait before next iteration
        if iteration < req.max_iterations and loop_id in _ACTIVE_LOOPS:
            await asyncio.sleep(req.interval_seconds)

    # Exhausted all iterations without convergence
    status = "exhausted" if loop_id in _ACTIVE_LOOPS else "stopped"
    _finalize_loop(loop_id, status, best_agreement, best_consensus, history)
    _ACTIVE_LOOPS.discard(loop_id)


def _update_loop(loop_id: str, iteration: int, best_agreement: float,
                 best_consensus: str, history: list):
    conn = _get_conn()
    try:
        conn.execute(
            """UPDATE scheduler_loops
               SET current_iteration=?, best_agreement=?,
                   best_consensus=?, history=?
               WHERE id=?""",
            (iteration, best_agreement, best_consensus,
             json.dumps(history), loop_id),
        )
        conn.commit()
    finally:
        conn.close()


def _finalize_loop(loop_id: str, status: str, best_agreement: float,
                   best_consensus: str, history: list):
    conn = _get_conn()
    try:
        conn.execute(
            """UPDATE scheduler_loops
               SET status=?, best_agreement=?, best_consensus=?,
                   history=?, completed_at=?
               WHERE id=?""",
            (status, best_agreement, best_consensus,
             json.dumps(history),
             datetime.now(timezone.utc).isoformat(), loop_id),
        )
        conn.commit()
    finally:
        conn.close()

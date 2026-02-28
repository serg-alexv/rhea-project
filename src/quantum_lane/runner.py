#!/usr/bin/env python3
"""
Deterministic quantum-lane runner with auditable receipts.

Primary mode:
- Qiskit simulator execution (when available)

Fallback mode:
- Deterministic local sampler for baseline templates

This module is intentionally strict about receipt completeness so claims can be
audited later by a second lane.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import random
import uuid
from pathlib import Path
from typing import Any, Dict, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOG = PROJECT_ROOT / "logs" / "quantum_lane" / "receipts.jsonl"

REQUIRED_RECEIPT_FIELDS = [
    "schema_version",
    "run_id",
    "ts",
    "template",
    "circuit_hash",
    "sdk",
    "sdk_version",
    "transpiler_hash",
    "backend_id",
    "mode",
    "seed",
    "shots",
    "result_digest",
    "counts",
    "status",
    "provenance",
]


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def canonical_json(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest_obj(obj: Dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def build_circuit_spec(template: str) -> Dict[str, Any]:
    if template == "bell_state_baseline":
        return {
            "name": template,
            "qubits": 2,
            "ops": [
                {"op": "h", "q": 0},
                {"op": "cx", "q0": 0, "q1": 1},
                {"op": "measure_all"},
            ],
        }
    if template == "superposition_collapse_baseline":
        return {
            "name": template,
            "qubits": 1,
            "ops": [
                {"op": "h", "q": 0},
                {"op": "measure_all"},
            ],
        }
    if template == "entanglement_consistency_baseline":
        return {
            "name": template,
            "qubits": 2,
            "ops": [
                {"op": "x", "q": 1},
                {"op": "h", "q": 0},
                {"op": "cx", "q0": 0, "q1": 1},
                {"op": "measure_all"},
            ],
        }
    raise ValueError(f"unknown template: {template}")


def _sample_weighted(rng: random.Random, probs: Dict[str, float]) -> str:
    x = rng.random()
    acc = 0.0
    last = ""
    for bitstring, p in probs.items():
        last = bitstring
        acc += p
        if x <= acc:
            return bitstring
    return last


def run_fallback(template: str, shots: int, seed: int) -> Tuple[Dict[str, int], Dict[str, Any]]:
    """Deterministic fallback sampler for baseline experiments."""
    rng = random.Random(seed)
    if template == "bell_state_baseline":
        probs = {"00": 0.5, "11": 0.5}
    elif template == "superposition_collapse_baseline":
        probs = {"0": 0.5, "1": 0.5}
    elif template == "entanglement_consistency_baseline":
        probs = {"01": 0.5, "10": 0.5}
    else:
        raise ValueError(f"unknown template: {template}")

    counts: Dict[str, int] = {k: 0 for k in probs}
    for _ in range(shots):
        counts[_sample_weighted(rng, probs)] += 1

    meta = {
        "sdk": "fallback_sampler",
        "sdk_version": "1",
        "backend_id": "local-deterministic",
        "mode": "sim",
        "transpiler_hash": hashlib.sha256(
            f"{template}|fallback|seed={seed}".encode("utf-8")
        ).hexdigest(),
    }
    return counts, meta


def run_with_qiskit(circuit_spec: Dict[str, Any], shots: int, seed: int) -> Tuple[Dict[str, int], Dict[str, Any]]:
    """Run on qiskit simulator if installed."""
    from qiskit import QuantumCircuit

    sdk_version = "unknown"
    try:
        import qiskit as _qiskit  # type: ignore

        sdk_version = getattr(_qiskit, "__version__", "unknown")
    except Exception:
        pass

    qubits = circuit_spec["qubits"]
    qc = QuantumCircuit(qubits, qubits)
    for op in circuit_spec["ops"]:
        name = op["op"]
        if name == "h":
            qc.h(op["q"])
        elif name == "x":
            qc.x(op["q"])
        elif name == "cx":
            qc.cx(op["q0"], op["q1"])
        elif name == "measure_all":
            qc.measure(range(qubits), range(qubits))
        else:
            raise ValueError(f"unsupported op: {name}")

    backend = None
    backend_name = "unknown"
    transpiler_hash = ""
    counts: Dict[str, int] = {}

    # Prefer Aer simulator where available.
    try:
        from qiskit_aer import AerSimulator  # type: ignore
        from qiskit import transpile

        backend = AerSimulator(seed_simulator=seed)
        backend_name = backend.name
        tqc = transpile(qc, backend, seed_transpiler=seed)
        transpiler_hash = hashlib.sha256(tqc.qasm().encode("utf-8")).hexdigest()
        result = backend.run(tqc, shots=shots).result()
        counts = {str(k): int(v) for k, v in result.get_counts().items()}
    except Exception:
        # Broad compatibility fallback for older/newer qiskit packaging.
        try:
            from qiskit import Aer, execute  # type: ignore

            backend = Aer.get_backend("qasm_simulator")
            backend_name = getattr(backend, "name", lambda: "qasm_simulator")()
            transpiler_hash = hashlib.sha256(qc.qasm().encode("utf-8")).hexdigest()
            result = execute(qc, backend, shots=shots, seed_simulator=seed).result()
            counts = {str(k): int(v) for k, v in result.get_counts().items()}
        except Exception as exc:
            raise RuntimeError(f"qiskit simulator unavailable: {exc}") from exc

    meta = {
        "sdk": "qiskit",
        "sdk_version": sdk_version,
        "backend_id": backend_name,
        "mode": "sim",
        "transpiler_hash": transpiler_hash or hashlib.sha256(
            f"{circuit_spec['name']}|qiskit|seed={seed}".encode("utf-8")
        ).hexdigest(),
    }
    return counts, meta


def validate_receipt(receipt: Dict[str, Any]) -> Tuple[bool, str]:
    for key in REQUIRED_RECEIPT_FIELDS:
        if key not in receipt:
            return False, f"missing required field: {key}"
    if receipt.get("status") != "ok":
        return False, f"status not ok: {receipt.get('status')}"
    if not isinstance(receipt.get("counts"), dict) or not receipt.get("counts"):
        return False, "counts missing or empty"
    if int(receipt.get("shots", 0)) <= 0:
        return False, "shots must be > 0"
    return True, "ok"


def append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def single_run(template: str, shots: int, seed: int, task_id: str, commit_sha: str) -> Dict[str, Any]:
    circuit_spec = build_circuit_spec(template)
    circuit_hash = digest_obj(circuit_spec)

    status = "ok"
    error = ""
    try:
        counts, meta = run_with_qiskit(circuit_spec, shots=shots, seed=seed)
    except Exception as exc:
        counts, meta = run_fallback(template, shots=shots, seed=seed)
        status = "ok"
        error = f"qiskit_unavailable_fallback: {exc}"

    digest_payload = {
        "template": template,
        "seed": seed,
        "shots": shots,
        "counts": counts,
        "backend_id": meta["backend_id"],
    }
    result_digest = digest_obj(digest_payload)

    receipt = {
        "schema_version": "quantum-receipt-v1",
        "run_id": str(uuid.uuid4()),
        "ts": now_iso(),
        "template": template,
        "circuit_hash": circuit_hash,
        "sdk": meta["sdk"],
        "sdk_version": meta["sdk_version"],
        "transpiler_hash": meta["transpiler_hash"],
        "backend_id": meta["backend_id"],
        "mode": meta["mode"],
        "seed": seed,
        "shots": shots,
        "result_digest": result_digest,
        "counts": counts,
        "status": status,
        "error": error,
        "provenance": {
            "task_id": task_id,
            "commit_sha": commit_sha,
            "source": "quantum_lane.runner",
        },
    }
    ok, reason = validate_receipt(receipt)
    if not ok:
        raise RuntimeError(f"invalid receipt: {reason}")
    return receipt


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run deterministic quantum lane experiments")
    p.add_argument(
        "--template",
        required=True,
        choices=[
            "bell_state_baseline",
            "superposition_collapse_baseline",
            "entanglement_consistency_baseline",
        ],
    )
    p.add_argument("--shots", type=int, default=256)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--repeats", type=int, default=1)
    p.add_argument("--task-id", default="")
    p.add_argument("--commit-sha", default=os.getenv("GIT_COMMIT", ""))
    p.add_argument("--out", default=str(DEFAULT_LOG))
    return p


def main() -> int:
    args = build_parser().parse_args()
    out = Path(args.out)

    task_id = args.task_id or "T-4fba2777"
    commit_sha = args.commit_sha or "local"

    digests = []
    for _ in range(args.repeats):
        receipt = single_run(
            template=args.template,
            shots=args.shots,
            seed=args.seed,
            task_id=task_id,
            commit_sha=commit_sha,
        )
        append_jsonl(out, receipt)
        digests.append(receipt["result_digest"])
        print(
            json.dumps(
                {
                    "run_id": receipt["run_id"],
                    "template": receipt["template"],
                    "seed": receipt["seed"],
                    "sdk": receipt["sdk"],
                    "backend": receipt["backend_id"],
                    "digest": receipt["result_digest"][:16],
                    "out": str(out),
                },
                ensure_ascii=False,
            )
        )

    summary = {
        "template": args.template,
        "repeats": args.repeats,
        "shots": args.shots,
        "deterministic_same_digest": len(set(digests)) == 1 if args.repeats > 1 else True,
        "out": str(out),
    }
    print(json.dumps({"summary": summary}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

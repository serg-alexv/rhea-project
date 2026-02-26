#!/usr/bin/env /usr/bin/python3
"""
observability.py — SLOs, Metrics, and Alerts for Rhea Agent System

Computes key observability metrics from JSONL event logs:
  - Job latency (bridge calls)
  - Error rate (per provider)
  - Token spend
  - Relay health (pending, expired, dedup)
  - Chain integrity
  - Lease status
  - Effect intent completion rate

SLO table defines thresholds. Alert system flags violations.

Usage:
  python3 observability.py metrics         # compute all metrics
  python3 observability.py slos            # show SLO status
  python3 observability.py alerts          # show active alerts
  python3 observability.py dashboard       # compact dashboard
"""
from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

OPS_DIR = Path(__file__).parent.parent / "virtual-office"
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"

# ---------------------------------------------------------------------------
# SLO definitions
# ---------------------------------------------------------------------------

SLOS = {
    "bridge_error_rate": {
        "description": "Provider error rate per hour",
        "target": "< 10%",
        "threshold": 0.10,
        "severity": "P1",
    },
    "bridge_p95_latency_s": {
        "description": "95th percentile bridge call latency",
        "target": "< 30s",
        "threshold": 30.0,
        "severity": "P2",
    },
    "relay_pending_count": {
        "description": "Messages pending delivery",
        "target": "< 20",
        "threshold": 20,
        "severity": "P1",
    },
    "chain_integrity": {
        "description": "Hash chain is valid",
        "target": "always valid",
        "threshold": True,
        "severity": "P0",
    },
    "effect_failure_rate": {
        "description": "Effect intent failure rate",
        "target": "< 5%",
        "threshold": 0.05,
        "severity": "P1",
    },
    "lease_expired_count": {
        "description": "Unexpectedly expired leases",
        "target": "0",
        "threshold": 0,
        "severity": "P1",
    },
    "daily_token_spend": {
        "description": "Total API tokens per day",
        "target": "< 500K",
        "threshold": 500000,
        "severity": "P2",
    },
}


# ---------------------------------------------------------------------------
# Metric collectors
# ---------------------------------------------------------------------------

def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text().strip().split("\n"):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def collect_bridge_metrics() -> dict:
    """Metrics from bridge_calls.jsonl."""
    calls = _load_jsonl(LOGS_DIR / "bridge_calls.jsonl")
    if not calls:
        return {"total_calls": 0}

    total = len(calls)
    errors = sum(1 for c in calls if c.get("error") or c.get("status") == "error")
    error_rate = errors / total if total else 0

    latencies = [c.get("latency_s", 0) or 0 for c in calls]
    latencies_sorted = sorted(latencies)
    p50 = latencies_sorted[len(latencies_sorted) // 2] if latencies_sorted else 0
    p95_idx = int(len(latencies_sorted) * 0.95)
    p95 = latencies_sorted[p95_idx] if latencies_sorted else 0
    p99_idx = int(len(latencies_sorted) * 0.99)
    p99 = latencies_sorted[p99_idx] if latencies_sorted else 0

    tokens = sum(c.get("tokens_used", 0) or 0 for c in calls)

    by_provider = defaultdict(lambda: {"calls": 0, "errors": 0, "tokens": 0})
    for c in calls:
        p = c.get("provider", "unknown")
        by_provider[p]["calls"] += 1
        by_provider[p]["tokens"] += c.get("tokens_used", 0) or 0
        if c.get("error") or c.get("status") == "error":
            by_provider[p]["errors"] += 1

    return {
        "total_calls": total,
        "error_count": errors,
        "error_rate": round(error_rate, 4),
        "total_tokens": tokens,
        "latency_p50": round(p50, 3),
        "latency_p95": round(p95, 3),
        "latency_p99": round(p99, 3),
        "by_provider": {k: dict(v) for k, v in by_provider.items()},
    }


def collect_relay_metrics() -> dict:
    """Metrics from relay mailbox and acks."""
    mailbox = _load_jsonl(OPS_DIR / "relay_mailbox.jsonl")
    acks = _load_jsonl(OPS_DIR / "relay_acks.jsonl")
    ack_ids = {a.get("message_id") or a.get("id") for a in acks}

    total = len(mailbox)
    pending = sum(1 for m in mailbox if m.get("id") not in ack_ids)
    acked = total - pending

    by_priority = defaultdict(int)
    by_target = defaultdict(int)
    for m in mailbox:
        by_priority[m.get("priority", "?")] += 1
        by_target[m.get("target", "?")] += 1

    return {
        "total_messages": total,
        "pending": pending,
        "acked": acked,
        "by_priority": dict(by_priority),
        "by_target": dict(by_target),
    }


def collect_chain_metrics() -> dict:
    """Chain integrity check."""
    import rex_pager as rp
    valid, count, detail = rp.chain_verify()
    return {"valid": valid, "entries": count, "detail": detail}


def collect_lease_metrics() -> dict:
    """Lease status across all agents."""
    import rex_pager as rp
    leases_dir = rp.LEASES_DIR
    if not leases_dir.exists():
        return {"agents": 0, "expired": 0}

    agents = []
    expired_count = 0
    for f in leases_dir.glob("*.json"):
        lease = json.loads(f.read_text())
        lease["expired"] = rp._is_expired(lease.get("expires_at"))
        if lease["expired"]:
            expired_count += 1
        agents.append({
            "agent": lease.get("agent", f.stem),
            "token": lease.get("lease_token", 0),
            "expired": lease["expired"],
            "ttl_s": lease.get("ttl_s", 0),
        })

    return {"agents": len(agents), "expired": expired_count, "leases": agents}


def collect_intent_metrics() -> dict:
    """Effect intent completion rates."""
    import rex_pager as rp
    status = rp.intent_status()
    by_status = status.get("by_status", {})
    total = status.get("total", 0)
    failed = by_status.get("failed", 0)
    failure_rate = failed / total if total else 0

    return {
        "total": total,
        "by_status": by_status,
        "failure_rate": round(failure_rate, 4),
    }


def collect_all_metrics() -> dict:
    """Collect all observability metrics."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "bridge": collect_bridge_metrics(),
        "relay": collect_relay_metrics(),
        "chain": collect_chain_metrics(),
        "leases": collect_lease_metrics(),
        "intents": collect_intent_metrics(),
    }


# ---------------------------------------------------------------------------
# SLO evaluation
# ---------------------------------------------------------------------------

def evaluate_slos(metrics: dict) -> list[dict]:
    """Evaluate SLOs against current metrics. Returns list of SLO results."""
    results = []

    # bridge_error_rate
    bridge = metrics.get("bridge", {})
    err_rate = bridge.get("error_rate", 0)
    results.append({
        "slo": "bridge_error_rate",
        "value": err_rate,
        "target": SLOS["bridge_error_rate"]["target"],
        "ok": err_rate < SLOS["bridge_error_rate"]["threshold"],
        "severity": SLOS["bridge_error_rate"]["severity"],
    })

    # bridge_p95_latency_s
    p95 = bridge.get("latency_p95", 0)
    results.append({
        "slo": "bridge_p95_latency_s",
        "value": p95,
        "target": SLOS["bridge_p95_latency_s"]["target"],
        "ok": p95 < SLOS["bridge_p95_latency_s"]["threshold"],
        "severity": SLOS["bridge_p95_latency_s"]["severity"],
    })

    # relay_pending_count
    relay = metrics.get("relay", {})
    pending = relay.get("pending", 0)
    results.append({
        "slo": "relay_pending_count",
        "value": pending,
        "target": SLOS["relay_pending_count"]["target"],
        "ok": pending < SLOS["relay_pending_count"]["threshold"],
        "severity": SLOS["relay_pending_count"]["severity"],
    })

    # chain_integrity
    chain = metrics.get("chain", {})
    chain_ok = chain.get("valid", False)
    results.append({
        "slo": "chain_integrity",
        "value": "valid" if chain_ok else "BROKEN",
        "target": SLOS["chain_integrity"]["target"],
        "ok": chain_ok,
        "severity": SLOS["chain_integrity"]["severity"],
    })

    # effect_failure_rate
    intents = metrics.get("intents", {})
    fail_rate = intents.get("failure_rate", 0)
    results.append({
        "slo": "effect_failure_rate",
        "value": fail_rate,
        "target": SLOS["effect_failure_rate"]["target"],
        "ok": fail_rate < SLOS["effect_failure_rate"]["threshold"],
        "severity": SLOS["effect_failure_rate"]["severity"],
    })

    # lease_expired_count
    leases = metrics.get("leases", {})
    expired = leases.get("expired", 0)
    results.append({
        "slo": "lease_expired_count",
        "value": expired,
        "target": SLOS["lease_expired_count"]["target"],
        "ok": expired <= SLOS["lease_expired_count"]["threshold"],
        "severity": SLOS["lease_expired_count"]["severity"],
    })

    # daily_token_spend
    tokens = bridge.get("total_tokens", 0)
    results.append({
        "slo": "daily_token_spend",
        "value": tokens,
        "target": SLOS["daily_token_spend"]["target"],
        "ok": tokens < SLOS["daily_token_spend"]["threshold"],
        "severity": SLOS["daily_token_spend"]["severity"],
    })

    return results


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

def get_alerts(slo_results: list[dict]) -> list[dict]:
    """Extract active alerts from SLO violations."""
    return [r for r in slo_results if not r["ok"]]


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def display_metrics(metrics: dict):
    """Compact metrics display."""
    b = metrics["bridge"]
    r = metrics["relay"]
    c = metrics["chain"]
    l = metrics["leases"]
    i = metrics["intents"]

    print(f"METRICS — {metrics['timestamp'][:19]}Z")
    print(f"{'=' * 60}")
    print(f"\n  Bridge:")
    print(f"    Calls: {b['total_calls']}  Errors: {b['error_count']} ({b['error_rate']*100:.1f}%)")
    print(f"    Tokens: {b['total_tokens']}  Latency p50/p95/p99: {b['latency_p50']}/{b['latency_p95']}/{b['latency_p99']}s")
    for prov, pdata in b.get("by_provider", {}).items():
        print(f"    {prov}: {pdata['calls']} calls, {pdata['errors']} errors, {pdata['tokens']} tok")

    print(f"\n  Relay:")
    print(f"    Total: {r['total_messages']}  Pending: {r['pending']}  Acked: {r['acked']}")

    print(f"\n  Chain: {'VALID' if c['valid'] else 'BROKEN'} ({c['entries']} entries)")

    print(f"\n  Leases: {l['agents']} agents, {l['expired']} expired")
    for la in l.get("leases", []):
        status = "EXPIRED" if la["expired"] else "active"
        print(f"    {la['agent']}: token={la['token']} TTL={la['ttl_s']}s [{status}]")

    print(f"\n  Intents: {i['total']} total")
    for s, c_val in i.get("by_status", {}).items():
        print(f"    {s}: {c_val}")


def display_slos(slo_results: list[dict]):
    """SLO status table."""
    print(f"\nSLO STATUS")
    print(f"{'=' * 60}")
    print(f"  {'SLO':<25} {'Value':<15} {'Target':<12} {'Status':<6}")
    print(f"  {'-'*25} {'-'*15} {'-'*12} {'-'*6}")
    for r in slo_results:
        val_str = str(r['value'])[:14]
        status = "OK" if r["ok"] else f"FAIL ({r['severity']})"
        print(f"  {r['slo']:<25} {val_str:<15} {r['target']:<12} {status}")

    violations = [r for r in slo_results if not r["ok"]]
    print(f"\n  {len(slo_results) - len(violations)}/{len(slo_results)} SLOs met")


def display_dashboard(metrics: dict, slo_results: list[dict], alerts: list[dict]):
    """Compact dashboard combining everything."""
    print(f"\n{'#' * 60}")
    print(f"  RHEA OBSERVABILITY DASHBOARD")
    print(f"  {metrics['timestamp'][:19]}Z")
    print(f"{'#' * 60}")

    display_metrics(metrics)
    display_slos(slo_results)

    if alerts:
        print(f"\n  ACTIVE ALERTS ({len(alerts)}):")
        for a in alerts:
            print(f"    [{a['severity']}] {a['slo']}: {a['value']} (target: {a['target']})")
    else:
        print(f"\n  No active alerts.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "metrics":
        metrics = collect_all_metrics()
        display_metrics(metrics)

    elif cmd == "slos":
        metrics = collect_all_metrics()
        slo_results = evaluate_slos(metrics)
        display_slos(slo_results)

    elif cmd == "alerts":
        metrics = collect_all_metrics()
        slo_results = evaluate_slos(metrics)
        alerts = get_alerts(slo_results)
        if alerts:
            print(f"ACTIVE ALERTS ({len(alerts)}):")
            for a in alerts:
                print(f"  [{a['severity']}] {a['slo']}: {a['value']} (target: {a['target']})")
        else:
            print("No active alerts.")

    elif cmd == "dashboard":
        metrics = collect_all_metrics()
        slo_results = evaluate_slos(metrics)
        alerts = get_alerts(slo_results)
        display_dashboard(metrics, slo_results, alerts)

        # Save snapshot
        out = LOGS_DIR / "observability_snapshot.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({
            "timestamp": metrics["timestamp"],
            "metrics": metrics,
            "slos": slo_results,
            "alerts": alerts,
        }, indent=2, default=str))
        print(f"\n  Snapshot: {out}")

    else:
        print(f"Unknown: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()

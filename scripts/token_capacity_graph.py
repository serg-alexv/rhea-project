#!/usr/bin/env python3
"""
token_capacity_graph.py — aggregate token spend vs theoretical capacity.

Theoretical model (explicit assumptions):
1) API-billed agents (orion/gemini/shared): daily token capacity = budget_cap_usd / ref_cost_per_token_usd
2) ref_cost_per_token_usd is estimated from successful historical calls (median cost/token),
   with conservative fallback constants if data is insufficient.
3) Subscription agent (rex): no hard upper cap in USD; we include only guaranteed floor
   (MIN_DAILY_TOKENS) as conservative baseline contribution.

Outputs:
- opera/metrics/token_capacity.json
- opera/metrics/token_capacity_ascii.txt

Usage:
  python3 scripts/token_capacity_graph.py
  python3 scripts/token_capacity_graph.py --window-days 14
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = REPO_ROOT / "logs" / "bridge_calls.jsonl"
OUT_JSON = REPO_ROOT / "opera" / "metrics" / "token_capacity.json"
OUT_ASCII = REPO_ROOT / "opera" / "metrics" / "token_capacity_ascii.txt"

# Import canonical budget/floor settings from governor
sys.path.insert(0, str(REPO_ROOT / "src"))
from token_governor import BUDGET_CAPS, MIN_DAILY_TOKENS, AGENT_MAP, _load_billing_policy

# Conservative fallback cost/token (USD per token) when no reliable sample
FALLBACK_CPT = {
    "orion": 2.0e-6,
    "gemini": 1.0e-6,
    "shared": 1.5e-6,
}

TRACKED_AGENTS = ["rex", "orion", "gemini", "shared"]


def parse_ts(raw: str) -> datetime | None:
    if not raw:
        return None
    s = raw.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def infer_agent(rec: dict) -> str:
    name = str(rec.get("agent_name") or "").strip().lower()
    if name:
        return name
    prov = str(rec.get("provider") or "").strip().lower()
    return AGENT_MAP.get(prov, "shared")


def load_records(window_days: int | None = None) -> list[dict]:
    if not LOG_PATH.exists():
        return []

    since = None
    if window_days is not None and window_days > 0:
        since = datetime.now(timezone.utc) - timedelta(days=window_days)

    out = []
    with LOG_PATH.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            ts = parse_ts(str(rec.get("timestamp", "")))
            if not ts:
                continue
            if since and ts < since:
                continue
            rec["_ts"] = ts
            rec["_agent"] = infer_agent(rec)
            out.append(rec)

    out.sort(key=lambda r: r["_ts"])
    return out


def estimate_ref_cpt(records: list[dict], api_agents: list[str]) -> tuple[dict, dict]:
    samples = defaultdict(list)

    for r in records:
        if str(r.get("status", "")).lower() != "ok":
            continue
        tok = int(r.get("total_tokens") or 0)
        cost = float(r.get("cost_usd") or 0.0)
        ag = r.get("_agent", "shared")
        if ag not in api_agents:
            continue
        if tok > 0 and cost > 0:
            samples[ag].append(cost / tok)

    ref = {}
    provenance = {}
    for ag in api_agents:
        vals = samples.get(ag, [])
        if len(vals) >= 5:
            ref[ag] = float(median(vals))
            provenance[ag] = {
                "source": "median_log_cost_per_token",
                "n": len(vals),
                "min": min(vals),
                "max": max(vals),
            }
        else:
            ref[ag] = FALLBACK_CPT.get(ag, 2.0e-6)
            provenance[ag] = {
                "source": "fallback_constant",
                "n": len(vals),
                "min": min(vals) if vals else None,
                "max": max(vals) if vals else None,
            }
    return ref, provenance


def daily_capacity(ref_cpt: dict, api_agents: list[str], subscription_agents: list[str], billing_policy: dict) -> dict:
    cap = {}
    for ag in api_agents:
        usd = float(billing_policy.get(ag, {}).get("budget_cap", BUDGET_CAPS.get(ag, 0.0)))
        cpt = float(ref_cpt[ag]) if ref_cpt.get(ag) else 0.0
        cap[ag] = int(usd / cpt) if usd > 0 and cpt > 0 else 0

    # Conservative subscription contribution: guaranteed floor only.
    # Real subscription upper capacity is unbounded from this model's perspective.
    for ag in subscription_agents:
        cap[f"{ag}_floor"] = int(MIN_DAILY_TOKENS.get(ag, 0))

    cap["total_baseline"] = sum(cap[a] for a in api_agents) + sum(cap.get(f"{a}_floor", 0) for a in subscription_agents)
    cap["has_unbounded_subscription_capacity"] = bool(subscription_agents)
    return cap


def build_day_series(records: list[dict], cap_total_day: int) -> list[dict]:
    if not records:
        return []

    by_day = defaultdict(int)
    for r in records:
        day = r["_ts"].date().isoformat()
        by_day[day] += int(r.get("total_tokens") or 0)

    days = sorted(by_day.keys())
    series = []
    cum_actual = 0
    cum_baseline = 0

    for d in days:
        day_actual = by_day[d]
        cum_actual += day_actual
        cum_baseline += cap_total_day
        util = (cum_actual / cum_baseline) if cum_baseline else 0.0
        series.append(
            {
                "date": d,
                "actual_tokens_day": day_actual,
                "actual_tokens_cum": cum_actual,
                "theoretical_tokens_cum_baseline": cum_baseline,
                "utilization_vs_baseline_cum": util,
            }
        )

    return series


def render_ascii(series: list[dict], has_unbounded_subscription_capacity: bool, width: int = 52) -> str:
    lines = []
    if has_unbounded_subscription_capacity:
        lines.append("TOKEN CAPACITY (cumulative): actual vs baseline (subscription upper bound = unbounded)")
    else:
        lines.append("TOKEN CAPACITY (cumulative): actual vs theoretical")
    lines.append("=" * 76)
    if not series:
        lines.append("No data")
        return "\n".join(lines)

    max_theory = max(row["theoretical_tokens_cum_baseline"] for row in series) or 1

    for row in series:
        a = row["actual_tokens_cum"]
        t = row["theoretical_tokens_cum_baseline"]
        util = row["utilization_vs_baseline_cum"] * 100
        a_len = min(width, int((a / max_theory) * width))
        t_len = min(width, int((t / max_theory) * width))
        a_bar = "#" * max(1, a_len) if a > 0 else ""
        t_bar = "-" * max(1, t_len)
        lines.append(f"{row['date']} |A {a:>9,} {a_bar}")
        lines.append(f"           |B {t:>9,} {t_bar}  ({util:5.2f}% util vs baseline)")

    lines.append("=" * 76)
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Aggregate token spend vs theoretical capacity")
    ap.add_argument("--window-days", type=int, default=0, help="Limit analysis to last N days (0 = all)")
    args = ap.parse_args()

    window = args.window_days if args.window_days > 0 else None
    records = load_records(window)
    billing_policy = _load_billing_policy()
    api_agents = [a for a in TRACKED_AGENTS if billing_policy.get(a, {}).get("billing_mode") == "api"]
    subscription_agents = [a for a in TRACKED_AGENTS if billing_policy.get(a, {}).get("billing_mode") == "subscription"]
    ref_cpt, cpt_meta = estimate_ref_cpt(records, api_agents)
    cap = daily_capacity(ref_cpt, api_agents, subscription_agents, billing_policy)
    series = build_day_series(records, cap["total_baseline"])

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "log_path": str(LOG_PATH),
        "window_days": args.window_days,
        "billing_modes": {a: billing_policy.get(a, {}).get("billing_mode") for a in TRACKED_AGENTS},
        "assumptions": {
            "api_billed_daily_capacity": "budget_cap_usd / reference_cost_per_token (api-mode agents only)",
            "reference_cost_per_token": "median successful call cost/token per agent (fallback constants if sparse)",
            "subscription_agent_handling": "subscription agents contribute conservative floor baseline only; upper capacity unbounded",
        },
        "reference_cost_per_token_usd": ref_cpt,
        "reference_cost_meta": cpt_meta,
        "daily_capacity_tokens": cap,
        "series": series,
        "totals": {
            "actual_tokens_cum": series[-1]["actual_tokens_cum"] if series else 0,
            "baseline_tokens_cum": series[-1]["theoretical_tokens_cum_baseline"] if series else 0,
            "utilization_vs_baseline_cum": series[-1]["utilization_vs_baseline_cum"] if series else 0.0,
            "days": len(series),
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    ascii_graph = render_ascii(series, cap["has_unbounded_subscription_capacity"])
    OUT_ASCII.write_text(ascii_graph + "\n", encoding="utf-8")

    print(ascii_graph)
    print(f"Saved JSON: {OUT_JSON}")
    print(f"Saved ASCII: {OUT_ASCII}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

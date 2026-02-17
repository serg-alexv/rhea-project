#!/usr/bin/env python3
"""
test_tribunal_e2e.py — End-to-end test for Tribunal API

Tests both direct Python path (no server needed) and HTTP API path.
DoD: at least 3 providers respond, consensus report has agreement > 0.

Usage:
    python3 tests/test_tribunal_e2e.py           # direct (no server)
    python3 tests/test_tribunal_e2e.py --api      # against running server (localhost:8400)
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# Add src/ to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Load .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

PASS = 0
FAIL = 0
RESULTS = []


def check(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    status = "PASS" if condition else "FAIL"
    if condition:
        PASS += 1
    else:
        FAIL += 1
    line = f"  [{status}] {name}"
    if detail:
        line += f" — {detail}"
    print(line)
    RESULTS.append({"test": name, "status": status, "detail": detail})


def test_direct():
    """Test via direct Python imports (no HTTP server)."""
    print("\n=== DIRECT MODE (Python imports) ===\n")

    # 1. Bridge instantiation
    from rhea_bridge import RheaBridge
    bridge = RheaBridge()
    check("Bridge instantiation", bridge is not None)

    # 2. Provider availability
    status = bridge.models_status()
    avail = status["summary"]["available_providers"]
    total = status["summary"]["total_providers"]
    check("Provider availability", avail >= 3, f"{avail}/{total} providers")

    print(f"\n  Available providers:")
    for name, info in status["providers"].items():
        mark = "+" if info["available"] else "-"
        print(f"    [{mark}] {name}: {info['model_count']} models")

    # 3. Single-provider call (cheapest: Gemini flash)
    print("\n  Testing single call (gemini-2.0-flash-lite)...")
    t0 = time.time()
    resp = bridge.ask("Reply with exactly: TRIBUNAL_TEST_OK", model="gemini-2.0-flash-lite", max_tokens=20)
    t1 = time.time()
    check("Single call (Gemini)", resp.text and not resp.error, f"{t1-t0:.1f}s, {resp.tokens_used} tokens")

    # 4. Tribunal k=3 (minimal, fast)
    print("\n  Testing tribunal k=3, tier=cheap, mode=local...")
    t0 = time.time()
    result = bridge.tribunal("What is 2+2? Answer with just the number.", k=3, tier="cheap", mode="local")
    t1 = time.time()

    responded = len([r for r in result.responses if r.text and not r.error])
    providers_used = set(r.provider for r in result.responses if r.text)
    check("Tribunal k=3 responded", responded >= 3, f"{responded}/3 models")
    check("Tribunal k=3 multi-provider", len(providers_used) >= 2, f"providers: {providers_used}")

    report = result.consensus_report
    agreement = report.get("agreement_score", 0)
    # Local analysis with k=3 may report 0 if responses are too short for TF-IDF
    check("Tribunal k=3 has consensus report", bool(report), f"score={agreement:.2f}")
    check("Tribunal consensus text exists", bool(report.get("consensus_text")),
          f"'{report.get('consensus_text', '')[:80]}'")
    print(f"  Elapsed: {t1-t0:.1f}s")

    # 5. Tribunal k=5 (fuller test)
    print("\n  Testing tribunal k=5, tier=cheap, mode=chairman...")
    t0 = time.time()
    result5 = bridge.tribunal(
        "Is water wet? Give a one-sentence answer.",
        k=5, tier="cheap", mode="chairman"
    )
    t1 = time.time()

    responded5 = len([r for r in result5.responses if r.text and not r.error])
    providers5 = set(r.provider for r in result5.responses if r.text)
    report5 = result5.consensus_report
    agreement5 = report5.get("agreement_score", 0)

    check("Tribunal k=5 responded", responded5 >= 3, f"{responded5}/5 models")
    check("Tribunal k=5 providers ≥ 3", len(providers5) >= 3, f"providers: {providers5}")
    check("Tribunal k=5 agreement > 0", agreement5 > 0, f"score={agreement5:.2f}")
    check("Tribunal chairman analysis", "chairman" in str(report5.get("analysis_method", "")),
          f"method={report5.get('analysis_method')}")
    print(f"  Elapsed: {t1-t0:.1f}s")

    # 6. Consensus analyzer (ICE level 3)
    print("\n  Testing ICE consensus (k=3, rounds=1)...")
    from consensus_analyzer import ConsensusAnalyzer
    analyzer = ConsensusAnalyzer(bridge=bridge)
    t0 = time.time()
    ice = analyzer.analyze_ice("What color is the sky on a clear day?", k=3, rounds=1, tier="cheap")
    t1 = time.time()

    ice_d = ice.to_dict()
    check("ICE analysis completed", "ice" in str(ice_d.get("analysis_method", "")).lower(),
          f"method={ice_d.get('analysis_method')}")
    check("ICE agreement > 0", ice_d.get("agreement_score", 0) > 0,
          f"score={ice_d.get('agreement_score', 0):.2f}")
    print(f"  Elapsed: {t1-t0:.1f}s")

    return PASS, FAIL


def test_api():
    """Test via HTTP against running server."""
    import urllib.request
    import urllib.error

    print("\n=== API MODE (HTTP) ===\n")
    base = os.environ.get("TRIBUNAL_URL", "http://localhost:8400")

    # Health
    try:
        resp = urllib.request.urlopen(f"{base}/health", timeout=5)
        health = json.loads(resp.read())
        check("API /health", health.get("status") == "ok", json.dumps(health))
    except Exception as e:
        check("API /health", False, str(e))
        print("  Server not reachable. Start with: scripts/deploy_tribunal.sh local")
        return PASS, FAIL

    # Models
    resp = urllib.request.urlopen(f"{base}/models", timeout=5)
    models = json.loads(resp.read())
    check("API /models", models.get("summary", {}).get("available_providers", 0) >= 3)

    # Tribunal POST
    print("\n  Testing POST /tribunal...")
    payload = json.dumps({
        "prompt": "What is 2+2? Answer with just the number.",
        "k": 3, "tier": "cheap", "mode": "local"
    }).encode()
    req = urllib.request.Request(
        f"{base}/tribunal",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    t0 = time.time()
    resp = urllib.request.urlopen(req, timeout=60)
    result = json.loads(resp.read())
    t1 = time.time()

    check("API /tribunal responded", result.get("models_responded", 0) >= 3,
          f"{result.get('models_responded')}/{result.get('models_queried')} models")
    check("API /tribunal agreement > 0", result.get("agreement_score", 0) > 0,
          f"score={result.get('agreement_score', 0):.2f}")
    print(f"  Elapsed: {t1-t0:.1f}s")

    return PASS, FAIL


def main():
    mode = "api" if "--api" in sys.argv else "direct"
    print(f"Tribunal E2E Test — {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
    print(f"Mode: {mode}")

    if mode == "api":
        p, f = test_api()
    else:
        p, f = test_direct()

    # Summary
    print(f"\n{'=' * 50}")
    print(f"RESULTS: {p} passed, {f} failed, {p+f} total")
    if f == 0:
        print("ALL TESTS PASSED")
    else:
        print(f"FAILURES: {f}")

    # Write results to file
    out = Path(__file__).parent.parent / "logs" / "tribunal_e2e_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        "mode": mode,
        "passed": p,
        "failed": f,
        "tests": RESULTS,
    }, indent=2))
    print(f"\nResults written to: {out}")

    sys.exit(0 if f == 0 else 1)


if __name__ == "__main__":
    main()

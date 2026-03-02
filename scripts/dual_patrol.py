#!/usr/bin/env python3
"""
dual_patrol.py — two-unit patrol loop (mutual ping/ack + flow drain signal).

Purpose:
- emulate/operate "2 police units" pattern for AI flow continuity
- each unit monitors peer liveness by active ping, not passive assumptions
- emits append-only trace and local state for dashboards

Usage:
  # Unit A
  python3 scripts/dual_patrol.py serve --unit A --port 8411 --peer http://127.0.0.1:8412 --interval 3
  # Unit B
  python3 scripts/dual_patrol.py serve --unit B --port 8412 --peer http://127.0.0.1:8411 --interval 3

  # Status
  python3 scripts/dual_patrol.py status
"""

from __future__ import annotations

import argparse
import json
import subprocess
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".rhea" / "patrol"
TRACE_FILE = ROOT / "opera" / "metrics" / "patrol_trace.jsonl"
LOG_DIR = ROOT / "logs"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def append_trace(event: dict[str, Any]) -> None:
    TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with TRACE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now_iso(), **event}, ensure_ascii=False) + "\n")


class PatrolState:
    def __init__(self, unit: str):
        self.lock = threading.Lock()
        self.unit = unit
        self.started_at = now_iso()
        self.seq = 0
        self.ok_count = 0
        self.fail_count = 0
        self.consecutive_failures = 0
        self.last_peer_ok_at = ""
        self.last_peer_status = "unknown"
        self.last_peer_latency_ms = 0.0
        self.last_incoming_from = ""
        self.last_incoming_at = ""
        self.last_alert_at = ""

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return {
                "unit": self.unit,
                "started_at": self.started_at,
                "seq": self.seq,
                "ok_count": self.ok_count,
                "fail_count": self.fail_count,
                "consecutive_failures": self.consecutive_failures,
                "last_peer_ok_at": self.last_peer_ok_at,
                "last_peer_status": self.last_peer_status,
                "last_peer_latency_ms": self.last_peer_latency_ms,
                "last_incoming_from": self.last_incoming_from,
                "last_incoming_at": self.last_incoming_at,
                "last_alert_at": self.last_alert_at,
                "_updated": now_iso(),
            }

    def save(self) -> None:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        data = self.snapshot()
        p = STATE_DIR / f"{self.unit}.json"
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(p)


def post_json(url: str, payload: dict[str, Any], timeout: int = 4) -> tuple[bool, dict[str, Any], float]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        dt_ms = (time.time() - t0) * 1000.0
        return True, (json.loads(raw) if raw.strip() else {}), dt_ms
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        dt_ms = (time.time() - t0) * 1000.0
        return False, {}, dt_ms


def maybe_alert(unit: str, target: str, reason: str, cooldown_s: int = 300) -> None:
    state_file = STATE_DIR / f"{unit}.json"
    last_alert = ""
    if state_file.exists():
        try:
            last_alert = str(json.loads(state_file.read_text(encoding="utf-8")).get("last_alert_at", ""))
        except Exception:
            last_alert = ""
    if last_alert:
        try:
            last_ts = datetime.fromisoformat(last_alert.replace("Z", "+00:00")).timestamp()
            if (time.time() - last_ts) < cooldown_s:
                return
        except Exception:
            pass

    msg = f"P0 PATROL ALERT {unit}: peer degraded ({reason})"
    subprocess.run(
        ["python3", "opera/ops/rex_pager.py", "send", "PATROL", target, msg, "--priority", "P0", "--ttl", "1800"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    append_trace({"event": "patrol.alert", "unit": unit, "target": target, "reason": reason})


def serve(unit: str, port: int, peer: str, interval: int, fail_threshold: int, escalate_target: str) -> int:
    state = PatrolState(unit=unit)
    stop = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, obj: dict[str, Any]) -> None:
            raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, _fmt: str, *_args):
            return

        def do_GET(self):
            if self.path == "/health":
                self._send(200, {"ok": True, "unit": unit, "state": state.snapshot()})
                return
            self._send(404, {"ok": False, "error": "not_found"})

        def do_POST(self):
            if self.path != "/ping":
                self._send(404, {"ok": False, "error": "not_found"})
                return
            n = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(max(0, n)).decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw or "{}")
            except json.JSONDecodeError:
                payload = {}
            src = str(payload.get("from", "unknown"))
            with state.lock:
                state.last_incoming_from = src
                state.last_incoming_at = now_iso()
            state.save()
            append_trace({"event": "patrol.ping.in", "unit": unit, "from": src, "port": port})
            self._send(200, {"ok": True, "unit": unit, "ts": now_iso()})

    def ping_loop() -> None:
        peer_ping = peer.rstrip("/") + "/ping"
        while not stop.is_set():
            with state.lock:
                state.seq += 1
                seq = state.seq
            ok, resp, latency = post_json(peer_ping, {"from": unit, "seq": seq, "ts": now_iso()})
            with state.lock:
                state.last_peer_latency_ms = latency
                if ok and bool(resp.get("ok")):
                    state.ok_count += 1
                    state.consecutive_failures = 0
                    state.last_peer_ok_at = now_iso()
                    state.last_peer_status = "ok"
                    append_trace({"event": "patrol.ping.out.ok", "unit": unit, "peer": peer, "seq": seq, "latency_ms": round(latency, 2)})
                else:
                    state.fail_count += 1
                    state.consecutive_failures += 1
                    state.last_peer_status = "degraded"
                    append_trace({"event": "patrol.ping.out.fail", "unit": unit, "peer": peer, "seq": seq, "latency_ms": round(latency, 2), "fails": state.consecutive_failures})
                    if state.consecutive_failures >= fail_threshold:
                        state.last_alert_at = now_iso()
                        maybe_alert(unit, escalate_target, f"consecutive_failures={state.consecutive_failures}")
            state.save()
            stop.wait(interval)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    append_trace({"event": "patrol.start", "unit": unit, "port": port, "peer": peer, "interval": interval})
    state.save()

    t = threading.Thread(target=ping_loop, daemon=True)
    t.start()

    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    try:
        print(json.dumps({"ok": True, "mode": "serve", "unit": unit, "port": port, "peer": peer, "interval": interval}, ensure_ascii=False))
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        srv.shutdown()
        state.save()
        append_trace({"event": "patrol.stop", "unit": unit})
    return 0


def status(lines: int = 12) -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    states = []
    for p in sorted(STATE_DIR.glob("*.json")):
        try:
            states.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    print(json.dumps({"states": states}, ensure_ascii=False, indent=2))
    if TRACE_FILE.exists():
        tail = TRACE_FILE.read_text(encoding="utf-8", errors="replace").splitlines()[-max(1, lines) :]
        print("\n# trace_tail")
        for line in tail:
            print(line)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Dual patrol mutual ping loop")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("serve", help="run one patrol unit")
    sp.add_argument("--unit", required=True, help="unit label, e.g. A or B")
    sp.add_argument("--port", type=int, required=True, help="listen port")
    sp.add_argument("--peer", required=True, help="peer base url, e.g. http://127.0.0.1:8412")
    sp.add_argument("--interval", type=int, default=5, help="ping interval sec")
    sp.add_argument("--fail-threshold", type=int, default=3, help="consecutive failures before alert")
    sp.add_argument("--escalate-target", default="REX", help="relay target on failure")

    ss = sub.add_parser("status", help="show patrol states + trace tail")
    ss.add_argument("--lines", type=int, default=12, help="trace tail lines")

    args = ap.parse_args()
    if args.cmd == "serve":
        return serve(args.unit, args.port, args.peer, args.interval, args.fail_threshold, args.escalate_target)
    if args.cmd == "status":
        return status(args.lines)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())


#!/usr/bin/env python3
"""
server.py — Web server for Rhea Ontology Explorer

Lightweight Flask/aiohttp-free server using only stdlib.
Serves the dashboard + REST API for hypothesis management.

Usage:
    python3 rhea-ontology-explorer/server.py [--port 8420]
"""

import json
import os
import sys
import subprocess
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "rhea-ontology-explorer"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from core.engine import (
    OntologyEngine, Hypothesis, Evidence, MathUniversePlugin,
    AgentTeamConfig, HypothesisStatus
)

# ---------------------------------------------------------------------------
# Initialize engine
# ---------------------------------------------------------------------------

engine = OntologyEngine(project_root=PROJECT_ROOT)

# Register built-in plugins (loaded from plugins/ directory)
PLUGINS_DIR = Path(__file__).resolve().parent / "plugins"

def load_plugins():
    """Auto-discover and load all plugins from the plugins directory."""
    if not PLUGINS_DIR.exists():
        return
    for plugin_file in sorted(PLUGINS_DIR.glob("*.py")):
        if plugin_file.name.startswith("_"):
            continue
        try:
            # Execute plugin file which should call register_plugin(engine)
            plugin_globals = {"__file__": str(plugin_file)}
            exec(plugin_file.read_text(), plugin_globals)
            if "register_plugin" in plugin_globals:
                plugin_globals["register_plugin"](engine)
                print(f"  ✓ Loaded plugin: {plugin_file.stem}")
        except Exception as e:
            print(f"  ✗ Failed to load {plugin_file.stem}: {e}")

# ---------------------------------------------------------------------------
# API Handler
# ---------------------------------------------------------------------------

class OntologyAPIHandler(SimpleHTTPRequestHandler):
    """Serves both the static dashboard and the REST API."""

    STATIC_DIR = Path(__file__).resolve().parent / "static"

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # API endpoints
        if path == "/api/status":
            self._json_response(engine.status())
        elif path == "/api/graph":
            self._json_response(engine.graph.export_for_viz())
        elif path == "/api/graph/full":
            self._json_response(json.loads(engine.graph.to_json()))
        elif path == "/api/plugins":
            self._json_response(engine.registry.info())
        elif path.startswith("/api/hypothesis/"):
            hid = path.split("/")[-1]
            h = engine.graph.get(hid)
            if h:
                from dataclasses import asdict
                self._json_response(asdict(h))
            else:
                self._json_response({"error": "not found"}, 404)
        elif path == "/api/verification-log":
            self._json_response({"log": engine.verifier.results_log})
        # Static files
        elif path == "/" or path == "/index.html":
            self._serve_file(self.STATIC_DIR / "index.html", "text/html")
        elif path.endswith(".js"):
            self._serve_file(self.STATIC_DIR / path.lstrip("/"), "application/javascript")
        elif path.endswith(".css"):
            self._serve_file(self.STATIC_DIR / path.lstrip("/"), "text/css")
        else:
            self._serve_file(self.STATIC_DIR / path.lstrip("/"))

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_body()

        if path == "/api/propose":
            h = engine.propose(
                title=body.get("title", ""),
                statement=body.get("statement", ""),
                domain=body.get("domain", "general"),
                parent_id=body.get("parent_id"),
                tags=body.get("tags", []),
            )
            from dataclasses import asdict
            self._json_response(asdict(h), 201)

        elif path == "/api/verify":
            hid = body.get("hypothesis_id")
            if not hid:
                self._json_response({"error": "hypothesis_id required"}, 400)
                return
            report = engine.verify(hid)
            self._json_response(report)

        elif path == "/api/explore":
            seed = body.get("seed", "")
            domains = body.get("domains")
            depth = body.get("depth", 3)
            hypotheses = engine.explore(seed, domains, depth)
            from dataclasses import asdict
            self._json_response({
                "generated": len(hypotheses),
                "hypotheses": [asdict(h) for h in hypotheses],
            })

        elif path == "/api/evidence":
            hid = body.get("hypothesis_id")
            ev = Evidence(
                source=body.get("source", "manual"),
                content=body.get("content", ""),
                evidence_type=body.get("type", "support"),
                severity=body.get("severity", "info"),
                confidence=body.get("confidence", 0.5),
            )
            engine.graph.add_evidence(hid, ev)
            self._json_response({"ok": True})

        elif path == "/api/bridge/tribunal":
            # Execute Rhea bridge tribunal directly
            prompt = body.get("prompt", "")
            k = body.get("k", 5)
            tier = body.get("tier", "balanced")
            result = self._run_bridge_tribunal(prompt, k)
            self._json_response(result)

        elif path == "/api/red-team/attack":
            hid = body.get("hypothesis_id")
            h = engine.graph.get(hid)
            if not h:
                self._json_response({"error": "not found"}, 404)
                return
            report = engine.verifier.run_red_team(h, body.get("num_attackers", 3))
            self._json_response(report)

        else:
            self._json_response({"error": "unknown endpoint"}, 404)

    def _run_bridge_tribunal(self, prompt: str, k: int = 5) -> dict:
        """Execute a Rhea bridge tribunal command."""
        bridge_path = PROJECT_ROOT / "src" / "rhea_bridge.py"
        if not bridge_path.exists():
            return {"error": "rhea_bridge.py not found", "status": "unavailable"}
        try:
            result = subprocess.run(
                [sys.executable, str(bridge_path), "tribunal", prompt, "--k", str(k)],
                capture_output=True, text=True, timeout=120,
                cwd=str(PROJECT_ROOT),
                env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT / "src")}
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "status": "success" if result.returncode == 0 else "error"
            }
        except subprocess.TimeoutExpired:
            return {"error": "tribunal timed out (120s)", "status": "timeout"}
        except Exception as e:
            return {"error": str(e), "status": "error"}

    def _json_response(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def _serve_file(self, filepath: Path, content_type: str = None):
        if not filepath.exists():
            self.send_error(404)
            return
        data = filepath.read_bytes()
        self.send_response(200)
        ct = content_type or self._guess_type(filepath)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def _guess_type(self, filepath: Path) -> str:
        ext = filepath.suffix.lower()
        return {
            ".html": "text/html",
            ".js": "application/javascript",
            ".css": "text/css",
            ".json": "application/json",
            ".svg": "image/svg+xml",
            ".png": "image/png",
            ".ico": "image/x-icon",
        }.get(ext, "application/octet-stream")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        # Quieter logging
        if "/api/" in (args[0] if args else ""):
            sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8420
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        port = int(sys.argv[idx + 1])

    print(f"\n{'='*60}")
    print(f"  RHEA ONTOLOGY EXPLORER")
    print(f"  http://localhost:{port}")
    print(f"{'='*60}")
    print(f"\nLoading plugins...")
    load_plugins()
    print(f"\nEngine status: {json.dumps(engine.status(), indent=2)}")
    print(f"\nReady. Open http://localhost:{port} in your browser.\n")

    server = HTTPServer(("0.0.0.0", port), OntologyAPIHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.server_close()


if __name__ == "__main__":
    main()

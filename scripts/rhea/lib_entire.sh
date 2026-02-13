#!/usr/bin/env bash
set -euo pipefail

ENTIRE_DIR="${ENTIRE_DIR:-.entire}"
LOG_DIR="$ENTIRE_DIR/logs"
SNAP_DIR="$ENTIRE_DIR/snapshots"
OPS_LOG="$LOG_DIR/ops.jsonl"

mkdir -p "$LOG_DIR" "$SNAP_DIR"

iso_now() {
  # максимально простой и надёжный формат времени
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

git_head() {
  git rev-parse --short HEAD 2>/dev/null || echo "no-git"
}

log_event() {
  local cmd="$1"; shift || true
  local status="${1:-ok}"
  local msg="${1:-}"
  if [ -n "$msg" ]; then
    printf '{"ts":"%s","git":"%s","cmd":"%s","status":"%s","msg":"%s"}\n' \
      "$(iso_now)" "$(git_head)" "$cmd" "$status" "$msg" >>"$OPS_LOG"
  else
    printf '{"ts":"%s","git":"%s","cmd":"%s","status":"%s"}\n' \
      "$(iso_now)" "$(git_head)" "$cmd" "$status" >>"$OPS_LOG"
  fi
}

snapshot_repo_state() {
  local label="${1:-STATE}"
  local ts head out
  ts="$(iso_now | tr ':' '-' | tr '+' '_')"
  head="$(git_head)"
  out="$SNAP_DIR/${label}-${ts}-${head}.json"

  python3 - <<PY > "$out"
import json, subprocess, os

def sh(cmd):
    return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()

def read(path):
    return open(path, "r", encoding="utf-8").read() if os.path.exists(path) else None

snap = {
    "label": "${label}",
    "git": sh("git rev-parse --short HEAD") if os.path.isdir(".git") else None,
    "branch": sh("git rev-parse --abbrev-ref HEAD") if os.path.isdir(".git") else None,
    "status_porcelain": sh("git status --porcelain") if os.path.isdir(".git") else None,
    "files": {
        "docs_state": read("docs/state.md"),
        "root_state": read("state.md"),
        "docs_decisions": read("docs/decisions.md"),
        "root_decisions": read("decisions.md"),
        "docs_architecture": read("docs/architecture.md"),
        "root_architecture": read("architecture.md"),
    }
}
print(json.dumps(snap, ensure_ascii=False, indent=2))
PY
  echo "snapshot: $out"
}

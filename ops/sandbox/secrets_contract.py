#!/usr/bin/env /usr/bin/python3
"""
secrets_contract.py — Secrets Management Contract for Rhea

Enforces:
  1. Models never see raw secrets (redaction at every boundary)
  2. Secrets only live in .env (not in code, logs, or artifacts)
  3. Access is audited (every read logged)
  4. Rotation tracking (last rotated, age, alerts)
  5. Scoped access (which components use which keys)

Usage:
  python3 secrets_contract.py audit      # check all secrets for violations
  python3 secrets_contract.py status     # show rotation status
  python3 secrets_contract.py scan       # scan codebase for leaked secrets
  python3 secrets_contract.py contract   # show the secrets contract
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

# ---------------------------------------------------------------------------
# Secret registry
# ---------------------------------------------------------------------------

SECRETS_REGISTRY = {
    "OPENAI_API_KEY": {
        "pattern": r"sk-proj-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{20,}",
        "used_by": ["rhea_bridge.py (openai provider)"],
        "rotation_interval_days": 90,
        "scope": "OpenAI API calls only",
        "env_var": "OPENAI_API_KEY",
    },
    "ANTHROPIC_API_KEY": {
        "pattern": r"sk-ant-[A-Za-z0-9_-]{20,}",
        "used_by": ["rhea_bridge.py (anthropic provider via openrouter)"],
        "rotation_interval_days": 90,
        "scope": "Anthropic API calls only",
        "env_var": "ANTHROPIC_API_KEY",
    },
    "GEMINI_API_KEY": {
        "pattern": r"AIzaSy[A-Za-z0-9_-]{33}",
        "used_by": ["rhea_bridge.py (gemini provider)"],
        "rotation_interval_days": 90,
        "scope": "Google Gemini API calls only",
        "env_var": "GEMINI_API_KEY",
    },
    "DEEPSEEK_API_KEY": {
        "pattern": r"dsk-[A-Za-z0-9]{20,}",
        "used_by": ["rhea_bridge.py (deepseek provider)"],
        "rotation_interval_days": 90,
        "scope": "DeepSeek API calls only",
        "env_var": "DEEPSEEK_API_KEY",
    },
    "OPENROUTER_API_KEY": {
        "pattern": r"sk-or-[A-Za-z0-9_-]{20,}",
        "used_by": ["rhea_bridge.py (openrouter provider)"],
        "rotation_interval_days": 90,
        "scope": "OpenRouter API calls only",
        "env_var": "OPENROUTER_API_KEY",
    },
    "AZURE_API_KEY": {
        "pattern": r"[A-Za-z0-9]{32,}",
        "used_by": ["rhea_bridge.py (azure provider)"],
        "rotation_interval_days": 90,
        "scope": "Azure AI Foundry calls only",
        "env_var": "AZURE_API_KEY",
    },
    "HF_TOKEN": {
        "pattern": r"hf_[A-Za-z0-9]{20,}",
        "used_by": ["rhea_bridge.py (huggingface provider)"],
        "rotation_interval_days": 180,
        "scope": "HuggingFace inference only",
        "env_var": "HF_TOKEN",
    },
}


# ---------------------------------------------------------------------------
# Contract rules
# ---------------------------------------------------------------------------

CONTRACT = """
RHEA SECRETS CONTRACT v1
========================

1. STORAGE
   - Secrets live ONLY in .env files (never committed to git)
   - .env MUST be in .gitignore
   - No hardcoded secrets in source code
   - No secrets in log files, artifacts, or model context

2. ACCESS
   - Models read env vars through bridge.py ONLY
   - Raw key values never appear in model context/prompts
   - Every key access is through os.environ.get() in bridge code
   - Access audit: bridge_calls.jsonl logs provider but NOT key value

3. REDACTION
   - redact_secrets() applied to ALL log writes
   - Patterns: sk-proj-*, sk-ant-*, AIzaSy*, hf_*, gsk_*, dsk-*
   - Adversarial tests verify redaction (test_adversarial.py)

4. ROTATION
   - Target: rotate every 90 days (180 for HF)
   - Track last rotation date in secrets_rotation.json
   - Alert when key age > threshold

5. SCOPE
   - Each key used by exactly one provider in bridge.py
   - No cross-component secret sharing
   - Tribunal API uses bridge.py (inherits its secret scope)

6. VIOLATIONS
   - Secret in git history: rotate immediately + BFG cleanup
   - Secret in log file: truncate log + rotate key
   - Secret in model output: investigate prompt injection
"""


# ---------------------------------------------------------------------------
# Audit functions
# ---------------------------------------------------------------------------

def check_gitignore() -> tuple[bool, str]:
    """Verify .env is in .gitignore."""
    gitignore = PROJECT_ROOT / ".gitignore"
    if not gitignore.exists():
        return False, ".gitignore not found"
    content = gitignore.read_text()
    if ".env" in content:
        return True, ".env is in .gitignore"
    return False, ".env NOT in .gitignore — CRITICAL"


def scan_codebase() -> list[dict]:
    """Scan source files for leaked secrets."""
    violations = []
    scan_dirs = [
        PROJECT_ROOT / "src",
        PROJECT_ROOT / "ops",
        PROJECT_ROOT / "tests",
        PROJECT_ROOT / "scripts",
        PROJECT_ROOT / "docs",
    ]
    skip_patterns = {".pyc", ".json", ".jsonl", ".db", ".faa", ".fna", ".gff", ".gbk"}

    # Load actual secret values for matching
    env_path = PROJECT_ROOT / ".env"
    secret_values = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                v = v.strip()
                if v and len(v) > 8:
                    secret_values[k.strip()] = v

    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for f in scan_dir.rglob("*"):
            if f.is_dir() or f.suffix in skip_patterns:
                continue
            # Skip self
            if f.name == "secrets_contract.py":
                continue
            try:
                content = f.read_text(errors="ignore")
            except Exception:
                continue

            # Check for actual secret values
            for key_name, key_val in secret_values.items():
                if key_val in content:
                    violations.append({
                        "file": str(f.relative_to(PROJECT_ROOT)),
                        "secret": key_name,
                        "severity": "CRITICAL",
                        "detail": f"raw {key_name} value found in source",
                    })

            # Check for common patterns that shouldn't be in code
            for secret_name, info in SECRETS_REGISTRY.items():
                # Skip broad patterns that match too much
                if secret_name == "AZURE_API_KEY":
                    continue
                pattern = info["pattern"]
                matches = re.findall(pattern, content)
                for match in matches:
                    # Exclude the redaction patterns themselves
                    if "REDACTED" in content[max(0, content.index(match)-20):content.index(match)+len(match)+20]:
                        continue
                    # Exclude pattern definitions (regex in source)
                    line_start = content.rfind("\n", 0, content.index(match)) + 1
                    line = content[line_start:content.index(match)+len(match)+50].split("\n")[0]
                    if "re.compile" in line or "pattern" in line.lower() or "r'" in line or 'r"' in line:
                        continue
                    violations.append({
                        "file": str(f.relative_to(PROJECT_ROOT)),
                        "secret": secret_name,
                        "severity": "HIGH",
                        "detail": f"pattern match for {secret_name}: {match[:20]}...",
                    })

    return violations


def rotation_status() -> list[dict]:
    """Check secret rotation status."""
    rot_file = PROJECT_ROOT / "ops" / "virtual-office" / "secrets_rotation.json"
    rotation_data = {}
    if rot_file.exists():
        rotation_data = json.loads(rot_file.read_text())

    results = []
    now = datetime.now(timezone.utc)

    for name, info in SECRETS_REGISTRY.items():
        env_val = os.environ.get(info["env_var"], "")
        is_set = bool(env_val)
        last_rotated = rotation_data.get(name, {}).get("last_rotated")
        if last_rotated:
            try:
                rot_date = datetime.fromisoformat(last_rotated)
                age_days = (now - rot_date).days
            except ValueError:
                age_days = -1
        else:
            age_days = -1  # unknown

        threshold = info["rotation_interval_days"]
        overdue = age_days > threshold if age_days >= 0 else None

        results.append({
            "name": name,
            "is_set": is_set,
            "scope": info["scope"],
            "used_by": info["used_by"],
            "last_rotated": last_rotated or "unknown",
            "age_days": age_days if age_days >= 0 else "unknown",
            "threshold_days": threshold,
            "overdue": overdue,
        })

    return results


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def display_audit():
    """Full audit report."""
    print("SECRETS AUDIT")
    print("=" * 60)

    # 1. Gitignore check
    ok, msg = check_gitignore()
    print(f"\n  [{'OK' if ok else 'FAIL'}] {msg}")

    # 2. Codebase scan
    violations = scan_codebase()
    if violations:
        print(f"\n  VIOLATIONS FOUND ({len(violations)}):")
        for v in violations:
            print(f"    [{v['severity']}] {v['file']}: {v['detail']}")
    else:
        print(f"\n  [OK] No secret leaks found in codebase scan")

    # 3. Redaction check
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from rhea_bridge import redact_secrets
        test = "key=sk-proj-testvalue123456789012 and AIzaSyTestValue1234567890123456789012345"
        redacted = redact_secrets(test)
        redaction_works = "sk-proj" not in redacted and "AIzaSy" not in redacted
        print(f"  [{'OK' if redaction_works else 'FAIL'}] Redaction function {'working' if redaction_works else 'BROKEN'}")
    except ImportError:
        print(f"  [WARN] Could not import redact_secrets")

    # 4. Env var presence
    print(f"\n  Secret presence:")
    for name, info in SECRETS_REGISTRY.items():
        val = os.environ.get(info["env_var"], "")
        status = "SET" if val else "MISSING"
        print(f"    [{status}] {name} ({info['scope']})")

    return violations


def display_status():
    """Rotation status."""
    results = rotation_status()
    print("SECRET ROTATION STATUS")
    print("=" * 60)
    print(f"  {'Name':<25} {'Set':<5} {'Age':<10} {'Threshold':<10} {'Status'}")
    print(f"  {'-'*25} {'-'*5} {'-'*10} {'-'*10} {'-'*10}")
    for r in results:
        age = str(r["age_days"]) + "d" if r["age_days"] != "unknown" else "?"
        status = "OK" if r.get("overdue") is False else ("OVERDUE" if r.get("overdue") else "UNKNOWN")
        print(f"  {r['name']:<25} {'Y' if r['is_set'] else 'N':<5} {age:<10} {r['threshold_days']}d{'':<6} {status}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    # Load .env
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "audit":
        violations = display_audit()
        sys.exit(1 if violations else 0)

    elif cmd == "status":
        display_status()

    elif cmd == "scan":
        violations = scan_codebase()
        if violations:
            print(f"VIOLATIONS ({len(violations)}):")
            for v in violations:
                print(f"  [{v['severity']}] {v['file']}: {v['detail']}")
            sys.exit(1)
        else:
            print("No secret leaks found.")

    elif cmd == "contract":
        print(CONTRACT)

    else:
        print(f"Unknown: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()

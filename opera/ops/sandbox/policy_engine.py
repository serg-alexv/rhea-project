#!/usr/bin/env /usr/bin/python3
"""
policy_engine.py — Default-Deny Policy Engine for Tool Authorization

Every tool call / effect intent / memory write must pass through policy.
Design: deny by default, allow-list per (actor, action, args).

Policy inputs:
  - actor: agent role (LEAD, B2, COWORK, HUMAN)
  - action: tool/effect name (git_push, git_commit, bash, read, write, etc.)
  - args: action arguments (file paths, commands, etc.)
  - risk_score: 0-10 (auto-computed or manual)

Policy outputs:
  - decision: allow | deny | escalate
  - reason: human-readable explanation
  - redactions: list of fields to redact before execution
  - receipt: audit entry for the decision

Usage:
  python3 policy_engine.py check B2 git_push '{"remote":"origin","branch":"main"}'
  python3 policy_engine.py check B2 bash '{"command":"rm -rf /"}'
  python3 policy_engine.py check LEAD git_commit '{"message":"fix"}'
  python3 policy_engine.py rules                    # show all rules
  python3 policy_engine.py audit                    # show decision log
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

AUDIT_FILE = Path(__file__).parent.parent / "virtual-office" / "policy_audit.jsonl"

# ---------------------------------------------------------------------------
# Risk scoring
# ---------------------------------------------------------------------------

# Action risk baseline (0-10)
ACTION_RISK = {
    "read": 0,
    "glob": 0,
    "grep": 0,
    "git_status": 0,
    "git_log": 0,
    "git_diff": 0,
    "git_commit": 3,
    "git_push": 5,
    "git_push_force": 9,
    "git_reset_hard": 9,
    "git_branch_delete": 7,
    "bash": 6,
    "write": 4,
    "edit": 3,
    "delete": 7,
    "rm_rf": 10,
    "firestore_write": 5,
    "http_call": 4,
    "deploy": 8,
    "secret_access": 8,
    "permission_change": 9,
    "lease_acquire": 3,
    "effect_execute": 5,
}

# Actor trust levels
ACTOR_TRUST = {
    "HUMAN": 10,   # full trust
    "LEAD": 8,     # high trust
    "B2": 6,       # medium trust
    "COWORK": 5,   # medium trust
    "OPS": 4,      # limited trust
    "UNKNOWN": 0,  # no trust
}


def compute_risk(action: str, args: dict) -> int:
    """Compute risk score from action + args."""
    base = ACTION_RISK.get(action, 5)

    # Arg-based risk modifiers
    cmd = args.get("command", "")
    path = args.get("path", "") or args.get("file_path", "")
    branch = args.get("branch", "")

    # Dangerous command patterns
    if cmd:
        if re.search(r'rm\s+-rf', cmd):
            return 10
        if re.search(r'dd\s+if=', cmd):
            return 10
        if re.search(r'>(\/dev\/|\/etc\/)', cmd):
            return 9
        if re.search(r'curl.*\|.*sh', cmd):
            return 9
        if re.search(r'chmod\s+777', cmd):
            return 8
        if "sudo" in cmd:
            return 8
        if "--force" in cmd or "--hard" in cmd:
            base = max(base, 8)
        if "--no-verify" in cmd:
            base = max(base, 7)
        # Safe command patterns reduce risk
        safe_cmds = ["ls", "pwd", "echo", "cat", "head", "tail", "wc",
                     "git status", "git log", "git diff", "python3 -c",
                     "python3 tests/", "pytest", "which", "pgrep"]
        if any(cmd.strip().startswith(s) for s in safe_cmds):
            base = min(base, 3)

    # Path-based risk
    if path:
        if ".env" in path or "secret" in path.lower() or "credential" in path.lower():
            base = max(base, 8)
        if "/etc/" in path or "/var/" in path:
            base = max(base, 7)
        if "firebase" in path.lower() and "service-account" in path.lower():
            base = max(base, 9)

    # Branch-based risk
    if branch in ("main", "master", "production"):
        base = max(base, 7)

    return min(base, 10)


# ---------------------------------------------------------------------------
# Policy rules
# ---------------------------------------------------------------------------

# Rules: (actor_pattern, action_pattern, arg_matcher, decision, reason)
# First match wins. Default: deny.
RULES = [
    # HUMAN can do anything
    ("HUMAN", "*", None, "allow", "human override — full trust"),

    # Read-only operations — anyone
    ("*", "read", None, "allow", "read is safe"),
    ("*", "glob", None, "allow", "glob is safe"),
    ("*", "grep", None, "allow", "grep is safe"),
    ("*", "git_status", None, "allow", "read-only git"),
    ("*", "git_log", None, "allow", "read-only git"),
    ("*", "git_diff", None, "allow", "read-only git"),

    # Git write — LEAD and B2 only
    ("LEAD", "git_commit", None, "allow", "LEAD can commit"),
    ("B2", "git_commit", None, "allow", "B2 can commit"),
    ("LEAD", "git_push", lambda a: a.get("branch") not in ("main", "master"),
     "allow", "LEAD can push non-main branches"),
    ("B2", "git_push", lambda a: a.get("branch") not in ("main", "master"),
     "allow", "B2 can push non-main branches"),

    # Push to main — escalate to tribunal
    ("*", "git_push", lambda a: a.get("branch") in ("main", "master"),
     "escalate", "push to main requires tribunal approval"),

    # Force push — always escalate
    ("*", "git_push_force", None, "escalate", "force push requires tribunal"),
    ("*", "git_reset_hard", None, "escalate", "reset --hard requires approval"),
    ("*", "git_branch_delete", None, "escalate", "branch deletion requires approval"),

    # File write — LEAD and B2, restricted paths
    ("LEAD", "write", lambda a: not _is_sensitive_path(a.get("path", "")), "allow", "LEAD can write non-sensitive files"),
    ("B2", "write", lambda a: not _is_sensitive_path(a.get("path", "")), "allow", "B2 can write non-sensitive files"),
    ("LEAD", "edit", lambda a: not _is_sensitive_path(a.get("path", "")), "allow", "LEAD can edit non-sensitive files"),
    ("B2", "edit", lambda a: not _is_sensitive_path(a.get("path", "")), "allow", "B2 can edit non-sensitive files"),

    # Sensitive file writes — escalate
    ("*", "write", lambda a: _is_sensitive_path(a.get("path", "")), "escalate", "sensitive file requires approval"),
    ("*", "edit", lambda a: _is_sensitive_path(a.get("path", "")), "escalate", "sensitive file requires approval"),

    # Delete — always escalate
    ("*", "delete", None, "escalate", "deletion requires approval"),
    ("*", "rm_rf", None, "deny", "rm -rf is always denied"),

    # Bash — LEAD only, with risk check
    ("LEAD", "bash", lambda a: compute_risk("bash", a) < 7, "allow", "LEAD can run low-risk bash"),
    ("B2", "bash", lambda a: compute_risk("bash", a) < 6, "allow", "B2 can run low-risk bash"),

    # High-risk bash — escalate
    ("*", "bash", lambda a: compute_risk("bash", a) >= 7, "escalate", "high-risk bash requires approval"),

    # Lease operations
    ("LEAD", "lease_acquire", None, "allow", "LEAD can acquire leases"),
    ("B2", "lease_acquire", None, "allow", "B2 can acquire leases"),

    # Effect execution
    ("LEAD", "effect_execute", None, "allow", "LEAD can execute effects"),
    ("B2", "effect_execute", lambda a: compute_risk("effect_execute", a) < 7, "allow", "B2 can execute low-risk effects"),

    # Deploy — escalate always
    ("*", "deploy", None, "escalate", "deployment requires tribunal"),

    # Secrets — deny unless HUMAN
    ("*", "secret_access", None, "deny", "secret access denied for non-human actors"),

    # Permission changes — tribunal required (HC-3)
    ("*", "permission_change", None, "escalate", "permission changes require tribunal (HC-3)"),

    # Firebase — LEAD and B2
    ("LEAD", "firestore_write", None, "allow", "LEAD can write Firestore"),
    ("B2", "firestore_write", None, "allow", "B2 can write Firestore"),
]


def _is_sensitive_path(path: str) -> bool:
    """Check if a path points to sensitive files."""
    sensitive = [".env", "secret", "credential", "service-account",
                 "firebase/", ".ssh/", ".gnupg/", "id_rsa", ".claude/settings"]
    path_lower = path.lower()
    return any(s in path_lower for s in sensitive)


def _match_actor(pattern: str, actor: str) -> bool:
    return pattern == "*" or pattern == actor


def _match_action(pattern: str, action: str) -> bool:
    return pattern == "*" or pattern == action


# ---------------------------------------------------------------------------
# Policy evaluation
# ---------------------------------------------------------------------------

def evaluate(actor: str, action: str, args: dict = None) -> dict:
    """Evaluate a policy request. Returns decision dict."""
    args = args or {}
    risk = compute_risk(action, args)
    trust = ACTOR_TRUST.get(actor, 0)

    # Walk rules (first match wins)
    for rule_actor, rule_action, arg_matcher, decision, reason in RULES:
        if not _match_actor(rule_actor, actor):
            continue
        if not _match_action(rule_action, action):
            continue
        if arg_matcher and not arg_matcher(args):
            continue

        # Match found
        result = {
            "decision": decision,
            "reason": reason,
            "actor": actor,
            "action": action,
            "risk_score": risk,
            "trust_level": trust,
            "redactions": _compute_redactions(action, args),
        }
        _log_decision(result)
        return result

    # Default: deny
    result = {
        "decision": "deny",
        "reason": f"no matching rule for {actor}/{action} (default deny)",
        "actor": actor,
        "action": action,
        "risk_score": risk,
        "trust_level": trust,
        "redactions": [],
    }
    _log_decision(result)
    return result


def _compute_redactions(action: str, args: dict) -> list[str]:
    """Determine which fields should be redacted before execution."""
    redactions = []
    for key, val in args.items():
        if isinstance(val, str):
            if any(s in key.lower() for s in ("key", "secret", "token", "password", "credential")):
                redactions.append(key)
            if re.search(r'(sk-|AIzaSy|hf_|gsk_|dsk-)', val):
                redactions.append(key)
    return redactions


def _log_decision(result: dict):
    """Append decision to audit log."""
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": result["actor"],
        "action": result["action"],
        "decision": result["decision"],
        "reason": result["reason"],
        "risk_score": result["risk_score"],
    }
    with open(AUDIT_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def display_rules():
    """Show all policy rules."""
    print(f"POLICY RULES ({len(RULES)} rules)")
    print(f"{'=' * 70}")
    print(f"  {'#':<3} {'Actor':<8} {'Action':<20} {'Decision':<10} {'Reason'}")
    print(f"  {'-'*3} {'-'*8} {'-'*20} {'-'*10} {'-'*30}")
    for i, (actor, action, matcher, decision, reason) in enumerate(RULES, 1):
        cond = "+" if matcher else ""
        print(f"  {i:<3} {actor:<8} {action:<20} {decision:<10} {reason}")
    print(f"\n  Default: DENY (if no rule matches)")


def display_audit():
    """Show recent policy decisions."""
    if not AUDIT_FILE.exists():
        print("No policy decisions logged.")
        return
    entries = []
    for line in AUDIT_FILE.read_text().strip().split("\n"):
        if line.strip():
            entries.append(json.loads(line))
    print(f"POLICY AUDIT ({len(entries)} decisions)")
    print(f"{'=' * 70}")
    for e in entries[-20:]:
        ts = e["timestamp"][:19]
        icon = {"allow": "+", "deny": "X", "escalate": "?"}[e["decision"]]
        print(f"  [{icon}] {ts} {e['actor']:<8} {e['action']:<20} {e['decision']:<10} risk={e['risk_score']} — {e['reason']}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "check":
        if len(sys.argv) < 4:
            print("Usage: policy_engine.py check <actor> <action> [args_json]")
            sys.exit(1)
        actor = sys.argv[2]
        action = sys.argv[3]
        args = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
        result = evaluate(actor, action, args)
        icon = {"allow": "ALLOW", "deny": "DENY", "escalate": "ESCALATE"}[result["decision"]]
        print(f"[{icon}] {actor}/{action}")
        print(f"  Reason: {result['reason']}")
        print(f"  Risk: {result['risk_score']}/10  Trust: {result['trust_level']}/10")
        if result["redactions"]:
            print(f"  Redact: {result['redactions']}")
        sys.exit(0 if result["decision"] == "allow" else 1)

    elif cmd == "rules":
        display_rules()

    elif cmd == "audit":
        display_audit()

    elif cmd == "test":
        # Run built-in test scenarios
        print("Policy Engine Test Scenarios\n")
        tests = [
            ("B2", "read", {}, "allow"),
            ("B2", "git_commit", {"message": "fix"}, "allow"),
            ("B2", "git_push", {"branch": "feat/test"}, "allow"),
            ("B2", "git_push", {"branch": "main"}, "escalate"),
            ("B2", "git_push_force", {}, "escalate"),
            ("B2", "bash", {"command": "ls -la"}, "allow"),
            ("B2", "bash", {"command": "rm -rf /"}, "escalate"),
            ("B2", "rm_rf", {}, "deny"),
            ("B2", "write", {"path": "src/test.py"}, "allow"),
            ("B2", "write", {"path": ".env"}, "escalate"),
            ("B2", "secret_access", {}, "deny"),
            ("UNKNOWN", "git_commit", {}, "deny"),
            ("HUMAN", "deploy", {}, "allow"),
            ("B2", "deploy", {}, "escalate"),
            ("B2", "permission_change", {}, "escalate"),
        ]
        passed = 0
        for actor, action, args, expected in tests:
            result = evaluate(actor, action, args)
            ok = result["decision"] == expected
            passed += ok
            icon = "PASS" if ok else "FAIL"
            print(f"  [{icon}] {actor}/{action} -> {result['decision']} (expected {expected})")
        print(f"\n{passed}/{len(tests)} passed")
        sys.exit(0 if passed == len(tests) else 1)

    else:
        print(f"Unknown: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()

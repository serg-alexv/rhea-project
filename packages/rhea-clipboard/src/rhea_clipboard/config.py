"""Configuration management for Rhea Clipboard.

Stores settings in ~/.rhea/clipboard.json. Auto-generates device ID on first run.
"""

import json
import os
import platform
import uuid
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".rhea"
CONFIG_FILE = CONFIG_DIR / "clipboard.json"

_DEFAULTS: dict[str, Any] = {
    "server_url": "https://rhea-tribunal.fly.dev",
    "auth_token": "",
    "device_id": "",
    "device_name": "",
    "poll_interval_ms": 500,
    "history_limit": 50,
    "auto_classify": True,
    "sync_enabled": True,
    "sensitive_ttl_seconds": 300,
}

# Patterns for sensitive content auto-classification
SENSITIVE_PATTERNS: list[tuple[str, str]] = [
    # (regex_pattern, label)
    (r"(?:sk|pk|ak|rk|token)[_-][A-Za-z0-9]{20,}", "api_key"),
    (r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}", "github_token"),
    (r"(?:AKIA|ASIA)[A-Z0-9]{16}", "aws_key"),
    (r"(?:eyJ)[A-Za-z0-9_-]{20,}\.(?:eyJ)[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]+", "jwt"),
    (r"\b(?:password|passwd|pwd)\s*[:=]\s*\S+", "password"),
    (r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", "credit_card"),
    (r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----", "private_key"),
    (r"(?:ssh-rsa|ssh-ed25519|ecdsa-sha2)\s+[A-Za-z0-9+/=]{40,}", "ssh_key"),
]


def get_config() -> dict[str, Any]:
    """Load config from disk, creating defaults if needed."""
    cfg = dict(_DEFAULTS)

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                saved = json.load(f)
            cfg.update(saved)
        except (json.JSONDecodeError, OSError):
            pass

    # Auto-generate device identity if missing
    if not cfg["device_id"]:
        cfg["device_id"] = str(uuid.uuid4())
    if not cfg["device_name"]:
        cfg["device_name"] = platform.node() or f"device-{cfg['device_id'][:8]}"

    save_config(cfg)
    return cfg


def save_config(cfg: dict[str, Any]) -> None:
    """Persist config to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
    # Restrict permissions — config may contain auth token
    try:
        os.chmod(CONFIG_FILE, 0o600)
    except OSError:
        pass


def classify_content(text: str) -> str | None:
    """Return sensitivity label if text matches a known sensitive pattern, else None."""
    import re
    for pattern, label in SENSITIVE_PATTERNS:
        if re.search(pattern, text):
            return label
    return None

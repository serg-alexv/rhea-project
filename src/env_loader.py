"""
env_loader.py — Native .env file loader (replaces python-dotenv)
ADR-016: Zero external dependencies for env loading.

Usage:
    from env_loader import load_env
    load_env()                          # loads .env from project root
    load_env("/path/to/.env")           # loads specific file
    load_env(override=True)             # overwrite existing env vars
"""

import os
from pathlib import Path


def load_env(path=None, override=False):
    """Parse .env file and inject into os.environ."""
    if path is None:
        path = Path(__file__).parent.parent / ".env"
    else:
        path = Path(path)

    if not path.exists():
        return

    with open(path) as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            # Handle export prefix
            if line.startswith("export "):
                line = line[7:]
            # Split on first =
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # Strip surrounding quotes
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            # Only set if not already present (unless override)
            if override or key not in os.environ:
                os.environ[key] = value

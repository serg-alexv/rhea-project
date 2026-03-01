"""
rhea-memory — Open memory layer for AI agents.

5-layer persistent context system:
  Layer 1: MEMORY.md (auto-saved facts, free context)
  Layer 2: context-bridge.md (cross-session context transfer)
  Layer 3: Git checkpoints (commit-backed snapshots)
  Layer 4: SQL history (tribunal/dialog/radio persistence)
  Layer 5: Cloud sync (Firestore/S3, optional)

Usage:
    from rhea_memory import MemoryFeed, MemoryStore

    store = MemoryStore("./data")
    store.remember("api_base", "https://example.com/api")

    feed = MemoryFeed(project_root=".")
    compact = feed.generate()  # <4KB AI-compact summary
"""

__version__ = "0.1.0"

from rhea_memory.feed import MemoryFeed
from rhea_memory.store import MemoryStore

__all__ = ["MemoryFeed", "MemoryStore", "__version__"]

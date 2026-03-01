# rhea-memory

Persistent memory for AI agents. Zero dependencies, SQLite-backed, works anywhere Python runs.

```
pip install rhea-memory
```

## What it does

Two primitives: **key-value facts** and an **append-only timeline**. Plus a **feed generator** that compresses project state into <4KB summaries for LLM context windows.

```python
from rhea_memory import MemoryStore, MemoryFeed

# Key-value: remember facts across agent restarts
store = MemoryStore("./data")
store.remember("api_base", "https://example.com/api")
store.remember("last_deploy", {"commit": "abc123", "status": "ok"})

print(store.recall("api_base"))       # "https://example.com/api"
print(store.recall("last_deploy"))    # {"commit": "abc123", "status": "ok"}
print(store.facts())                  # all stored facts as dict

# Timeline: append-only event log
store.log("deploy", {"env": "prod", "commit": "abc123"})
store.log("error", {"msg": "timeout", "endpoint": "/api/health"})

for entry in store.timeline(limit=10):
    print(f"[{entry['ts'][:19]}] {entry['event']}")

# Feed: compress project state for LLM context
feed = MemoryFeed(project_root=".")
compact = feed.generate()  # git log, tasks, proofs — all under 4KB
```

## CLI

```bash
# Store and retrieve facts
rhea-memory remember api_base "https://example.com"
rhea-memory recall api_base
rhea-memory facts

# Event timeline
rhea-memory log deploy --data '{"env": "prod"}'
rhea-memory timeline --limit 20 --event deploy

# Generate compact feed
rhea-memory feed --root /path/to/project
rhea-memory feed -o memory_feed.md
```

## Architecture

```
┌──────────────────────────────────┐
│         rhea-memory              │
├──────────────────────────────────┤
│  MemoryStore (SQLite)            │
│  ├── kv table     (facts)        │
│  └── timeline table (events)     │
├──────────────────────────────────┤
│  MemoryFeed (read-only scanner)  │
│  ├── git log                     │
│  ├── task queue                  │
│  ├── governor stats              │
│  └── proof store                 │
└──────────────────────────────────┘
```

- **Zero external dependencies** — only Python stdlib (`sqlite3`, `json`, `pathlib`, `subprocess`)
- **Thread-safe** — WAL mode SQLite with locking
- **Portable** — single `memory.db` file, works on any OS
- **Compact feeds** — generates AI-optimized summaries under 4KB for LLM context windows

## The 5-layer model

| Layer | Backing | Persistence |
|-------|---------|-------------|
| 1. MEMORY.md | Markdown file | Auto-loaded into LLM context |
| 2. Context bridge | Markdown file | Cross-session state transfer |
| 3. Git checkpoints | Git commits | Immutable history |
| 4. SQL store | SQLite (this package) | Structured key-value + timeline |
| 5. Cloud sync | Firestore/S3 | Optional remote backup |

## Requirements

- Python 3.10+
- No other dependencies

## License

MIT

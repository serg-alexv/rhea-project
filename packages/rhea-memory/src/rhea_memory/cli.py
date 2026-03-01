"""CLI entry point for rhea-memory."""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        prog="rhea-memory",
        description="Open memory layer for AI agents"
    )
    sub = parser.add_subparsers(dest="command")

    # Feed
    feed_p = sub.add_parser("feed", help="Generate compact memory feed")
    feed_p.add_argument("--root", default=".", help="Project root")
    feed_p.add_argument("-o", "--output", help="Output file path")

    # Store
    store_p = sub.add_parser("remember", help="Store a fact")
    store_p.add_argument("key", help="Fact key")
    store_p.add_argument("value", help="Fact value")
    store_p.add_argument("--dir", default="./data", help="Data directory")

    recall_p = sub.add_parser("recall", help="Retrieve a fact")
    recall_p.add_argument("key", help="Fact key")
    recall_p.add_argument("--dir", default="./data", help="Data directory")

    facts_p = sub.add_parser("facts", help="List all stored facts")
    facts_p.add_argument("--dir", default="./data", help="Data directory")

    log_p = sub.add_parser("log", help="Append to timeline")
    log_p.add_argument("event", help="Event name")
    log_p.add_argument("--data", help="JSON data payload")
    log_p.add_argument("--dir", default="./data", help="Data directory")

    tl_p = sub.add_parser("timeline", help="Show timeline")
    tl_p.add_argument("--limit", type=int, default=20, help="Max entries")
    tl_p.add_argument("--event", help="Filter by event type")
    tl_p.add_argument("--dir", default="./data", help="Data directory")

    args = parser.parse_args()

    if args.command == "feed":
        from rhea_memory.feed import MemoryFeed
        feed = MemoryFeed(args.root)
        if args.output:
            path = feed.write(args.output)
            print(f"Written to {path}")
        else:
            print(feed.generate())

    elif args.command == "remember":
        from rhea_memory.store import MemoryStore
        store = MemoryStore(args.dir)
        store.remember(args.key, args.value)
        print(f"Stored: {args.key}")

    elif args.command == "recall":
        from rhea_memory.store import MemoryStore
        store = MemoryStore(args.dir)
        val = store.recall(args.key)
        if val is None:
            print(f"Not found: {args.key}")
            sys.exit(1)
        print(val)

    elif args.command == "facts":
        from rhea_memory.store import MemoryStore
        store = MemoryStore(args.dir)
        import json
        print(json.dumps(store.facts(), indent=2))

    elif args.command == "log":
        import json
        from rhea_memory.store import MemoryStore
        store = MemoryStore(args.dir)
        data = json.loads(args.data) if args.data else None
        entry_id = store.log(args.event, data)
        print(f"Logged: #{entry_id}")

    elif args.command == "timeline":
        import json
        from rhea_memory.store import MemoryStore
        store = MemoryStore(args.dir)
        entries = store.timeline(limit=args.limit, event=args.event)
        for e in entries:
            print(f"  [{e['ts'][:19]}] {e['event']}" +
                  (f" → {e.get('data', '')}" if e.get('data') else ""))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

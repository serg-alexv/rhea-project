#!/usr/bin/env python3
"""Generate wrap tasks for ⚠️ SwiftUI views listed in docs/rheakit-view-mapping.md."""
import re
from src.task_db_mongo import TaskDBMongo

doc = Path(__file__).resolve().parents[1] / "docs" / "rheakit-view-mapping.md"

pattern = re.compile(r"\| `([^`]+)` \| ⚠️ \| (.+) \|")
with doc.open() as f:
    lines = f.readlines()
tasks = []
for line in lines:
    match = pattern.search(line)
    if match:
        view, desc = match.groups()
        tasks.append((view.strip(), desc.strip()))

if not tasks:
    print("No ⚠️ views found")
    sys.exit(0)

db = TaskDBMongo()
for view, desc in tasks:
    title = f"Wrap {view} in RheaKit"
    detail = f"{desc} (from rheakit-view-mapping)"
    task = db.add(title, priority="P2", agent="any", tags=["view-wrap"], depends_on=[])
    print(f"Created task {task['id']} for {view}")

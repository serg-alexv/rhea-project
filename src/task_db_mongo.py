#!/usr/bin/env python3
"""MongoDB-backed task queue for Rhea."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pymongo import MongoClient, ReturnDocument
from pymongo.collection import Collection

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_URI = "mongodb://localhost:27017"
DEFAULT_DB = "rhea"

PRIORITIES = ["P0", "P1", "P2", "P3"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskDBMongo:
    def __init__(self, uri: str = DEFAULT_URI, db_name: str = DEFAULT_DB):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.tasks: Collection = self.db["tasks"]
        self.log: Collection = self.db["task_log"]
        self.tasks.create_index("status")
        self.tasks.create_index("agent")
        self.tasks.create_index("priority")

    def _normalize(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        if not doc:
            return {}
        doc = dict(doc)
        doc["depends_on"] = doc.get("depends_on", [])
        doc["tags"] = doc.get("tags", [])
        doc["created"] = doc.get("created") or _now()
        doc["updated"] = doc.get("updated") or _now()
        doc.pop("_id", None)
        return doc

    def _log(self, action: str, task_id: str = "", agent: str = "", detail: str = "") -> None:
        self.log.insert_one({"ts": _now(), "action": action, "task_id": task_id, "agent": agent, "detail": detail})

    def add(self, title: str, priority: str = "P1", agent: str = "any",
            depends_on: Optional[List[str]] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        task_id = f"T-{uuid.uuid4().hex[:8]}"
        payload = {
            "id": task_id,
            "title": title,
            "priority": priority if priority in PRIORITIES else "P1",
            "status": "open",
            "agent": agent,
            "claimed_by": "",
            "depends_on": depends_on or [],
            "result": "",
            "tags": tags or [],
            "created": _now(),
            "updated": _now(),
        }
        self.tasks.insert_one(payload)
        self._log("add", task_id, agent, title)
        return self._normalize(payload)

    def claim(self, agent: str) -> Optional[Dict[str, Any]]:
        filters = {"status": "open", "$or": [{"agent": agent}, {"agent": "any"}]}
        order = [
            ("agent", -1),
            ("priority", 1),
            ("created", 1),
        ]
        doc = self.tasks.find_one_and_update(
            filters,
            {"$set": {"status": "claimed", "claimed_by": agent, "updated": _now()}},
            sort=[("agent", -1), ("priority", 1), ("created", 1)],
            return_document=ReturnDocument.AFTER,
        )
        if not doc:
            return None
        self._log("claim", doc["id"], agent)
        return self._normalize(doc)

    def complete(self, task_id: str, result: str = "") -> Dict[str, Any]:
        doc = self.tasks.find_one_and_update(
            {"id": task_id},
            {"$set": {"status": "done", "result": result, "updated": _now()}},
            return_document=ReturnDocument.AFTER,
        )
        self._log("complete", task_id, detail=result[:200])
        return self._normalize(doc)

    def list_tasks(self, status: str = None, agent: str = None, priority: str = None) -> List[Dict[str, Any]]:
        query = {}
        if status:
            query["status"] = status
        if agent:
            query["$or"] = [{"agent": agent}, {"claimed_by": agent}]
        if priority:
            query["priority"] = priority
        cursor = self.tasks.find(query).sort([("priority", 1), ("created", 1)])
        return [self._normalize(doc) for doc in cursor]


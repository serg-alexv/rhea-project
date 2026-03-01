"""
MemoryFeed — generates AI-compact memory summaries from project state.

Scans git history, file trees, and SQL stores to produce a <4KB
context feed optimized for LLM consumption. Deduplicates repeated
patterns and compresses multi-source data into single-pass readable format.
"""

import json
import re
import subprocess
import sqlite3
from collections import Counter
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Any


class MemoryFeed:
    """Generate compact memory feeds from project state.

    Scans:
      - Git log (commits = decisions)
      - File tree (outbox/inbox messages)
      - SQLite databases (proofs, tasks, governor)
      - Session metadata
    """

    def __init__(self, project_root: str | Path = "."):
        self.root = Path(project_root).resolve()

    def generate(self, identity: dict[str, str] | None = None,
                 git_days: int = 7, git_limit: int = 20) -> str:
        """Generate the compact memory feed.

        Args:
            identity: Agent identity map, e.g. {"rex": "Opus 4.6 | Core Coordinator"}
            git_days: How many days of git history to include.
            git_limit: Max commits to include.

        Returns:
            AI-compact feed string, typically <4KB.
        """
        now = datetime.now(timezone.utc)
        commits = self._git_log(days=git_days, limit=git_limit)
        outbox = self._outbox_digest()
        tasks = self._task_snapshot()
        proofs = self._proof_count()

        lines = [
            "# MEMORY FEED [compact]",
            f"# Generated: {now.isoformat()[:19]}Z",
            "",
        ]

        if identity:
            lines.append("## Identity")
            for name, desc in identity.items():
                lines.append(f"  @{name} = {desc}")
            lines.append("")

        lines += [
            "## Tasks",
            f"  total={tasks.get('total', 0)} "
            f"open={tasks.get('open', 0)} "
            f"done={tasks.get('done', 0)} "
            f"blocked={tasks.get('blocked', 0)}",
            "",
        ]

        if proofs > 0:
            lines.append(f"## Proofs: {proofs}")
            lines.append("")

        lines.append("## Git (recent)")
        for c in commits[:15]:
            lines.append(f"  {c}")
        lines.append("")

        if outbox:
            lines.append("## Messages (recent)")
            for o in outbox[:8]:
                lines.append(f"  {o}")
            lines.append("")

        byte_est = len("\n".join(lines))
        lines.append(f"# [{byte_est} bytes, ~{byte_est // 4} tokens]")
        return "\n".join(lines)

    def write(self, output_path: str | Path | None = None, **kwargs) -> Path:
        """Generate and write feed to file."""
        feed = self.generate(**kwargs)
        if output_path is None:
            output_path = self.root / "memory" / "FEED.compact"
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(feed)
        return path

    # --- Scanners ---

    def _git_log(self, days: int = 7, limit: int = 20) -> list[str]:
        try:
            result = subprocess.run(
                ["git", "log", f"--since={days} days ago", f"-{limit}",
                 "--format=%h %ai %s"],
                cwd=self.root, capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return []
        except Exception:
            return []
        return self._dedup(result.stdout.strip().splitlines())

    def _outbox_digest(self, limit: int = 20) -> list[str]:
        outbox = self.root / "opera" / "ops" / "virtual-office" / "outbox"
        if not outbox.exists():
            return []
        files = sorted(outbox.glob("*.md"), key=lambda f: f.name, reverse=True)[:limit]
        digest = []
        for f in files:
            parts = f.stem.split("_", 3)
            sender = parts[0] if parts else "?"
            topic = parts[3].replace("_", " ").lower() if len(parts) > 3 else "?"
            digest.append(f"@{sender.lower()} → {topic}")
        return digest

    def _proof_count(self) -> int:
        db_path = self.root / "data" / "proof.db"
        if not db_path.exists():
            return 0
        try:
            conn = sqlite3.connect(str(db_path))
            count = conn.execute("SELECT COUNT(*) FROM proofs").fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0

    def _task_snapshot(self) -> dict[str, int]:
        state_path = self.root / "opera" / "tasks" / "state.json"
        if not state_path.exists():
            return {"total": 0}
        try:
            state = json.loads(state_path.read_text())
            tasks = state.get("tasks", {})
            counts = Counter(t["status"] for t in tasks.values())
            return {"total": len(tasks), **dict(counts)}
        except Exception:
            return {"total": 0}

    @staticmethod
    def _dedup(lines: list[str]) -> list[str]:
        """Deduplicate lines by normalized content."""
        seen: dict[str, list[str]] = {}
        order: list[str] = []
        for line in lines:
            parts = line.split(None, 3)
            subject = parts[3] if len(parts) > 3 else line
            norm = re.sub(r'\b[0-9a-f]{7,40}\b', '', subject.lower())
            norm = re.sub(r'[^\w\s]', ' ', norm)
            norm = re.sub(r'\s+', ' ', norm).strip()
            if len(norm) < 3:
                continue
            if norm not in seen:
                seen[norm] = []
                order.append(norm)
            seen[norm].append(line)
        output = []
        for norm in order:
            entries = seen[norm]
            if len(entries) == 1:
                output.append(entries[0])
            else:
                output.append(f"({len(entries)}x) {entries[0]}")
        return output

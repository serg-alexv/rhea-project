"""
rhea_supervisor.py — Agent Process Supervisor

Manages real CLI sessions (claude, codex, gemini bridge) as PTY-backed
subprocesses. Exposes control via functions that tribunal_api.py calls.

Each session = one PTY process with a ring buffer capturing output.
The TUI (or any API client) can: spawn, kill, list, read output, send input.
"""

from __future__ import annotations

import os
import pty
import select
import signal
import subprocess
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Agent CLI configurations
AGENT_CMDS = {
    "rex":      {"cmd": ["claude", "--dangerously-skip-permissions"], "env": {}},
    "orion":    {"cmd": ["codex", "--full-auto"], "env": {}},
    "gemini":   {"cmd": ["python3", str(PROJECT_ROOT / "src/rhea_bridge.py"), "repl", "gemini/gemini-2.5-flash"], "env": {}},
    "shared":   {"cmd": ["claude", "--dangerously-skip-permissions", "--model", "sonnet"], "env": {}},
    "hyperion": {"cmd": ["claude", "--dangerously-skip-permissions", "--model", "sonnet"], "env": {}},
    "custom":   {"cmd": [], "env": {}},  # user-specified
}

MAX_OUTPUT_LINES = 500  # ring buffer size per session


@dataclass
class Session:
    id: str
    agent: str
    pid: int
    fd: int  # PTY master fd
    started_at: str
    status: str = "running"  # running, stopped, crashed
    exit_code: Optional[int] = None
    output: deque = field(default_factory=lambda: deque(maxlen=MAX_OUTPUT_LINES))
    _partial_line: str = ""
    label: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent": self.agent,
            "pid": self.pid,
            "started_at": self.started_at,
            "status": self.status,
            "exit_code": self.exit_code,
            "output_lines": len(self.output),
            "label": self.label,
        }


class Supervisor:
    """Manages agent CLI sessions with PTY I/O."""

    def __init__(self):
        self.sessions: dict[str, Session] = {}
        self._lock = threading.Lock()
        self._readers: dict[str, threading.Thread] = {}

    def spawn(self, agent: str, label: str = "", cmd: list[str] = None, prompt: str = None) -> Session:
        """Spawn a new agent session. Returns Session."""
        cfg = AGENT_CMDS.get(agent, AGENT_CMDS["custom"])
        run_cmd = cmd if cmd else list(cfg["cmd"])
        if not run_cmd:
            raise ValueError(f"No command configured for agent '{agent}' and no custom cmd provided")

        if prompt:
            run_cmd.append(prompt)

        env = {**os.environ, **cfg.get("env", {}), "TERM": "xterm-256color"}

        master_fd, slave_fd = pty.openpty()

        proc = subprocess.Popen(
            run_cmd,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=str(PROJECT_ROOT),
            env=env,
            preexec_fn=os.setsid,
        )
        os.close(slave_fd)

        session = Session(
            id=uuid.uuid4().hex[:12],
            agent=agent,
            pid=proc.pid,
            fd=master_fd,
            started_at=datetime.now(timezone.utc).isoformat(),
            label=label or f"{agent}-{proc.pid}",
        )

        with self._lock:
            self.sessions[session.id] = session

        # Start reader thread
        reader = threading.Thread(
            target=self._read_loop,
            args=(session, proc),
            daemon=True,
            name=f"sv-read-{session.id}",
        )
        self._readers[session.id] = reader
        reader.start()

        return session

    def _read_loop(self, session: Session, proc: subprocess.Popen):
        """Read PTY output into ring buffer until process exits."""
        fd = session.fd
        try:
            while True:
                ready, _, _ = select.select([fd], [], [], 1.0)
                if ready:
                    try:
                        data = os.read(fd, 4096)
                        if not data:
                            break
                        text = data.decode("utf-8", errors="replace")
                        # Split into lines, handle partial
                        parts = (session._partial_line + text).split("\n")
                        session._partial_line = parts[-1]
                        for line in parts[:-1]:
                            session.output.append(line)
                    except OSError:
                        break

                # Check if process is still alive
                ret = proc.poll()
                if ret is not None:
                    # Flush partial
                    if session._partial_line:
                        session.output.append(session._partial_line)
                        session._partial_line = ""
                    session.exit_code = ret
                    session.status = "stopped" if ret == 0 else "crashed"
                    break
        except Exception:
            session.status = "crashed"
        finally:
            try:
                os.close(fd)
            except OSError:
                pass

    def send_input(self, session_id: str, text: str) -> bool:
        """Send text to a session's stdin. Returns success."""
        with self._lock:
            session = self.sessions.get(session_id)
        if not session or session.status != "running":
            return False
        try:
            os.write(session.fd, (text + "\n").encode())
            return True
        except OSError:
            return False

    def kill(self, session_id: str) -> bool:
        """Kill a session. Returns success."""
        with self._lock:
            session = self.sessions.get(session_id)
        if not session:
            return False
        try:
            os.killpg(os.getpgid(session.pid), signal.SIGTERM)
            time.sleep(0.5)
            try:
                os.killpg(os.getpgid(session.pid), signal.SIGKILL)
            except (ProcessLookupError, OSError):
                pass
            session.status = "stopped"
            return True
        except (ProcessLookupError, OSError):
            session.status = "stopped"
            return True

    def get_output(self, session_id: str, last_n: int = 50) -> list[str]:
        """Get last N lines of output from a session."""
        with self._lock:
            session = self.sessions.get(session_id)
        if not session:
            return []
        lines = list(session.output)
        return lines[-last_n:]

    def list_sessions(self) -> list[dict]:
        """List all sessions."""
        with self._lock:
            return [s.to_dict() for s in self.sessions.values()]

    def get_session(self, session_id: str) -> Optional[dict]:
        """Get a single session."""
        with self._lock:
            s = self.sessions.get(session_id)
        return s.to_dict() if s else None

    def cleanup_dead(self) -> int:
        """Remove sessions that have been stopped/crashed for > 5 min. Returns count removed."""
        count = 0
        with self._lock:
            to_remove = []
            for sid, s in self.sessions.items():
                if s.status in ("stopped", "crashed"):
                    to_remove.append(sid)
            for sid in to_remove:
                del self.sessions[sid]
                count += 1
        return count


# Singleton
supervisor = Supervisor()

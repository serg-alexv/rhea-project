"""Clipboard change detection — cross-platform via pyperclip with SHA256 dedup."""

import hashlib
import logging
import threading
import time
from collections.abc import Callable
from typing import Any

import pyperclip

log = logging.getLogger(__name__)


class ClipboardMonitor:
    """Polls system clipboard for changes and fires a callback on new content.

    Uses pyperclip for cross-platform support (macOS pbcopy/pbpaste,
    Linux xclip/xsel, Windows win32).  On Windows, attempts win32clipboard
    for richer format detection, falling back gracefully to pyperclip.
    """

    def __init__(
        self,
        on_change: Callable[[str], Any],
        poll_interval_ms: int = 500,
    ) -> None:
        self._on_change = on_change
        self._interval = poll_interval_ms / 1000.0
        self._last_hash: str = ""
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._paused = False

        # Seed with current clipboard so we don't fire on startup
        try:
            current = pyperclip.paste() or ""
            self._last_hash = self._hash(current)
        except Exception:
            self._last_hash = ""

    @staticmethod
    def _hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()

    def _read_clipboard(self) -> str | None:
        """Read clipboard text. Returns None on failure."""
        # Try win32clipboard first on Windows for richer support
        try:
            import sys
            if sys.platform == "win32":
                try:
                    import win32clipboard  # type: ignore[import-untyped]
                    win32clipboard.OpenClipboard()
                    try:
                        data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                        return data or ""
                    except Exception:
                        pass
                    finally:
                        win32clipboard.CloseClipboard()
                except ImportError:
                    pass
        except Exception:
            pass

        # Cross-platform fallback
        try:
            return pyperclip.paste() or ""
        except Exception as exc:
            log.debug("clipboard read failed: %s", exc)
            return None

    def _poll_loop(self) -> None:
        while self._running:
            time.sleep(self._interval)
            if self._paused or not self._running:
                continue
            content = self._read_clipboard()
            if content is None:
                continue
            h = self._hash(content)
            with self._lock:
                if h != self._last_hash and content.strip():
                    self._last_hash = h
                    try:
                        self._on_change(content)
                    except Exception:
                        log.exception("clipboard change callback failed")

    def start(self) -> None:
        """Start monitoring in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True, name="clip-monitor")
        self._thread.start()
        log.info("clipboard monitor started (poll every %dms)", int(self._interval * 1000))

    def stop(self) -> None:
        """Stop monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        log.info("clipboard monitor stopped")

    def pause(self) -> None:
        """Temporarily pause monitoring (e.g. while writing to clipboard ourselves)."""
        self._paused = True

    def resume(self) -> None:
        """Resume monitoring after pause. Re-seed hash to avoid echo."""
        content = self._read_clipboard()
        if content is not None:
            with self._lock:
                self._last_hash = self._hash(content)
        self._paused = False

    @property
    def is_running(self) -> bool:
        return self._running and not self._paused

"""REST + SSE client for Rhea clipboard sync."""

import json
import logging
import threading
import time
from collections.abc import Callable
from typing import Any

import requests

from .config import classify_content

log = logging.getLogger(__name__)

_TIMEOUT = 10
_SSE_RECONNECT_DELAY = 5


class ClipboardClient:
    """Talks to the Rhea clipboard API.

    Endpoints assumed (relative to server_url):
        POST   /clipboard              — push a clip
        GET    /clipboard/latest       — get most recent clip
        GET    /clipboard              — list clips (paginated)
        DELETE /clipboard/{clip_id}    — delete a clip
        POST   /clipboard/{clip_id}/pin   — pin/unpin
        GET    /clipboard/stream       — SSE event stream
    """

    def __init__(
        self,
        server_url: str,
        auth_token: str,
        device_id: str,
        device_name: str,
    ) -> None:
        self.server_url = server_url.rstrip("/")
        self.auth_token = auth_token
        self.device_id = device_id
        self.device_name = device_name
        self._history: list[dict[str, Any]] = []
        self._history_lock = threading.Lock()

    # -- internal ---------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {"Content-Type": "application/json"}
        if self.auth_token:
            h["Authorization"] = f"Bearer {self.auth_token}"
            h["X-API-Key"] = self.auth_token  # fallback header
        return h

    def _url(self, path: str) -> str:
        return f"{self.server_url}{path}"

    def _request(
        self,
        method: str,
        path: str,
        json_body: dict | None = None,
        params: dict | None = None,
    ) -> dict[str, Any] | None:
        """Fire an HTTP request, return parsed JSON or None on failure."""
        try:
            resp = requests.request(
                method,
                self._url(path),
                headers=self._headers(),
                json=json_body,
                params=params,
                timeout=_TIMEOUT,
            )
            if resp.status_code == 401:
                log.warning("auth failed (401) — check token")
                return None
            if resp.status_code == 404:
                log.debug("endpoint not found: %s %s", method, path)
                return None
            resp.raise_for_status()
            if resp.content:
                return resp.json()  # type: ignore[no-any-return]
            return {}
        except requests.ConnectionError:
            log.debug("connection failed to %s", self.server_url)
            return None
        except requests.Timeout:
            log.debug("request timed out: %s %s", method, path)
            return None
        except requests.RequestException as exc:
            log.debug("request error: %s", exc)
            return None

    # -- public API -------------------------------------------------------

    def push(self, content: str, content_type: str = "text", source_app: str = "") -> dict[str, Any] | None:
        """Push clipboard content to the server."""
        if not content or not content.strip():
            return None

        sensitivity = classify_content(content)
        ttl = None
        if sensitivity:
            ttl = 300  # 5 min for sensitive content
            log.info("sensitive content detected (%s), TTL=%ds", sensitivity, ttl)

        body: dict[str, Any] = {
            "content": content,
            "content_type": content_type,
            "device_id": self.device_id,
            "device_name": self.device_name,
        }
        if source_app:
            body["source_app"] = source_app
        if sensitivity:
            body["sensitivity"] = sensitivity
            body["ttl_seconds"] = ttl

        result = self._request("POST", "/clipboard", json_body=body)
        if result:
            log.info("pushed clip (%d chars)%s", len(content), f" [{sensitivity}]" if sensitivity else "")
            self._add_to_history(content, sensitivity)
        return result

    def pull_latest(self) -> dict[str, Any] | None:
        """Get the most recent clipboard entry from server."""
        return self._request("GET", "/clipboard/latest")

    def history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Fetch clipboard history from server."""
        result = self._request("GET", "/clipboard", params={"limit": limit})
        if result and isinstance(result, dict) and "clips" in result:
            return result["clips"]  # type: ignore[no-any-return]
        if isinstance(result, list):
            return result
        return []

    def delete(self, clip_id: str) -> bool:
        """Delete a clipboard entry."""
        result = self._request("DELETE", f"/clipboard/{clip_id}")
        return result is not None

    def pin(self, clip_id: str) -> bool:
        """Pin a clipboard entry."""
        result = self._request("POST", f"/clipboard/{clip_id}/pin", json_body={"pinned": True})
        return result is not None

    def unpin(self, clip_id: str) -> bool:
        """Unpin a clipboard entry."""
        result = self._request("POST", f"/clipboard/{clip_id}/pin", json_body={"pinned": False})
        return result is not None

    def stream(self, on_event: Callable[[dict[str, Any]], None]) -> None:
        """Connect to SSE stream. Blocks forever, reconnects on failure.

        Should be run in a daemon thread.
        """
        while True:
            try:
                log.info("connecting to SSE stream...")
                resp = requests.get(
                    self._url("/clipboard/stream"),
                    headers=self._headers(),
                    stream=True,
                    timeout=None,
                )
                if resp.status_code != 200:
                    log.warning("SSE stream returned %d", resp.status_code)
                    time.sleep(_SSE_RECONNECT_DELAY)
                    continue

                try:
                    import sseclient
                    client = sseclient.SSEClient(resp)
                    for event in client.events():
                        try:
                            data = json.loads(event.data) if event.data else {}
                            if event.event:
                                data["type"] = event.event
                            on_event(data)
                        except json.JSONDecodeError:
                            on_event({"type": event.event or "message", "data": event.data})
                except Exception as exc:
                    log.debug("SSE stream error: %s", exc)

            except requests.ConnectionError:
                log.debug("SSE connection failed, retrying in %ds", _SSE_RECONNECT_DELAY)
            except Exception as exc:
                log.debug("SSE unexpected error: %s", exc)

            time.sleep(_SSE_RECONNECT_DELAY)

    # -- local history cache -----------------------------------------------

    def _add_to_history(self, content: str, sensitivity: str | None = None) -> None:
        with self._history_lock:
            entry = {
                "content": content,
                "preview": self._preview(content),
                "sensitivity": sensitivity,
                "timestamp": time.time(),
            }
            self._history.insert(0, entry)
            self._history = self._history[:50]

    def get_local_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return recent clips from local cache (no network)."""
        with self._history_lock:
            return list(self._history[:limit])

    @staticmethod
    def _preview(text: str, max_len: int = 40) -> str:
        """Generate a short preview for menu display."""
        line = text.replace("\n", " ").replace("\r", "").strip()
        if len(line) > max_len:
            return line[:max_len - 1] + "\u2026"
        return line

"""System tray icon and menu for Rhea Clipboard."""

import logging
import threading
from typing import Any

import pyperclip
from PIL import Image, ImageDraw

log = logging.getLogger(__name__)


def _create_icon_image(size: int = 64) -> Image.Image:
    """Generate a clipboard icon programmatically using Pillow.

    Dark background, white clipboard shape with a clip at the top.
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle
    margin = 2
    draw.ellipse([margin, margin, size - margin, size - margin], fill=(45, 45, 55, 240))

    # Clipboard body (rounded rectangle)
    bx1, by1 = int(size * 0.22), int(size * 0.22)
    bx2, by2 = int(size * 0.78), int(size * 0.85)
    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=4, fill=(220, 220, 230, 255))

    # Inner area (paper)
    ix1, iy1 = bx1 + 4, by1 + 10
    ix2, iy2 = bx2 - 4, by2 - 4
    draw.rectangle([ix1, iy1, ix2, iy2], fill=(250, 250, 255, 255))

    # Clip at top center
    clip_w = int(size * 0.24)
    cx1 = (size - clip_w) // 2
    cx2 = cx1 + clip_w
    cy1 = int(size * 0.14)
    cy2 = int(size * 0.32)
    draw.rounded_rectangle([cx1, cy1, cx2, cy2], radius=3, fill=(100, 110, 140, 255))
    # Inner clip cutout
    draw.rounded_rectangle([cx1 + 3, cy1 + 3, cx2 - 3, cy2 - 4], radius=2, fill=(220, 220, 230, 255))

    # Text lines on the paper
    line_color = (160, 165, 180, 200)
    for i in range(3):
        ly = iy1 + 6 + i * 8
        lx2 = ix2 - 4 - (i * 6)  # progressively shorter lines
        if ly + 2 < iy2:
            draw.rectangle([ix1 + 4, ly, lx2, ly + 2], fill=line_color)

    return img


class ClipboardTray:
    """System tray application for Rhea Clipboard.

    Shows a tray icon with a menu of recent clips, sync toggle, and settings.
    """

    def __init__(self, client: Any, monitor: Any) -> None:
        self._client = client
        self._monitor = monitor
        self._sync_enabled = True
        self._auto_classify = True
        self._icon: Any = None
        self._lock = threading.Lock()

    def _build_menu(self) -> Any:
        """Build the tray menu dynamically."""
        import pystray

        items: list[Any] = []

        # Latest clip preview
        history = self._client.get_local_history(limit=10)
        if history:
            latest = history[0]
            preview = latest.get("preview", "(empty)")
            sensitivity = latest.get("sensitivity")
            label = f"Latest: {preview}"
            if sensitivity:
                label = f"Latest: [{sensitivity}] {preview}"
            items.append(pystray.MenuItem(label, None, enabled=False))
        else:
            items.append(pystray.MenuItem("Latest: (no clips yet)", None, enabled=False))

        items.append(pystray.Menu.SEPARATOR)

        # History entries — click to copy back
        if history:
            for i, entry in enumerate(history):
                preview = entry.get("preview", "(empty)")
                sensitivity = entry.get("sensitivity")
                if sensitivity:
                    preview = f"[{sensitivity}] {preview}"
                content = entry.get("content", "")
                # Capture content in closure
                items.append(pystray.MenuItem(
                    preview,
                    self._make_copy_action(content),
                ))
        else:
            items.append(pystray.MenuItem("(no history)", None, enabled=False))

        items.append(pystray.Menu.SEPARATOR)

        # Sync toggle
        items.append(pystray.MenuItem(
            lambda _item: f"Sync: {'ON' if self._sync_enabled else 'OFF'}",
            self._toggle_sync,
            checked=lambda _item: self._sync_enabled,
        ))

        # Auto-classify toggle
        items.append(pystray.MenuItem(
            "Privacy: Auto-classify",
            self._toggle_classify,
            checked=lambda _item: self._auto_classify,
        ))

        items.append(pystray.Menu.SEPARATOR)

        # Actions
        items.append(pystray.MenuItem("Clear History", self._clear_history))
        items.append(pystray.MenuItem("Settings...", self._show_settings))
        items.append(pystray.MenuItem("Quit", self._quit))

        return pystray.Menu(*items)

    def _make_copy_action(self, content: str):
        """Create a menu action that copies text to clipboard."""
        def action(_icon: Any, _item: Any) -> None:
            self._monitor.pause()
            try:
                pyperclip.copy(content)
                log.info("copied clip from history (%d chars)", len(content))
            finally:
                self._monitor.resume()
        return action

    def _toggle_sync(self, _icon: Any, _item: Any) -> None:
        self._sync_enabled = not self._sync_enabled
        if self._sync_enabled:
            self._monitor.resume()
            log.info("sync enabled")
        else:
            self._monitor.pause()
            log.info("sync paused")
        self.update_menu()

    def _toggle_classify(self, _icon: Any, _item: Any) -> None:
        self._auto_classify = not self._auto_classify
        log.info("auto-classify %s", "enabled" if self._auto_classify else "disabled")
        self.update_menu()

    def _clear_history(self, _icon: Any, _item: Any) -> None:
        with self._client._history_lock:
            self._client._history.clear()
        log.info("history cleared")
        self.update_menu()

    def _show_settings(self, _icon: Any, _item: Any) -> None:
        from .config import CONFIG_FILE
        print(f"Config: {CONFIG_FILE}")
        log.info("config at %s", CONFIG_FILE)

    def _quit(self, _icon: Any, _item: Any) -> None:
        log.info("quitting")
        self._monitor.stop()
        if self._icon:
            self._icon.stop()

    def update_menu(self) -> None:
        """Rebuild and apply updated menu (called when new clips arrive)."""
        if self._icon:
            self._icon.menu = self._build_menu()
            try:
                self._icon.update_menu()
            except Exception:
                pass  # Some backends don't support dynamic update

    def on_remote_clip(self, content: str) -> None:
        """Handle an incoming remote clipboard update."""
        self._monitor.pause()
        try:
            pyperclip.copy(content)
        finally:
            self._monitor.resume()
        self.update_menu()

    def run(self) -> None:
        """Start the tray icon. Blocks until quit."""
        import pystray

        icon_image = _create_icon_image()
        self._icon = pystray.Icon(
            name="rhea-clipboard",
            icon=icon_image,
            title="Rhea Clipboard",
            menu=self._build_menu(),
        )
        log.info("tray icon started")
        self._icon.run()

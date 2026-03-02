"""Entry point for rhea-clipboard: python -m rhea_clipboard."""

import argparse
import getpass
import logging
import sys
import threading

import requests

from . import __version__
from .config import get_config, save_config
from .monitor import ClipboardMonitor
from .sync import ClipboardClient

log = logging.getLogger("rhea_clipboard")


def _login(server_url: str) -> str | None:
    """Interactive login — prompt for email/password, return JWT token."""
    print(f"Login to {server_url}")
    email = input("Email: ").strip()
    if not email:
        print("Aborted.")
        return None
    password = getpass.getpass("Password: ")
    if not password:
        print("Aborted.")
        return None

    try:
        resp = requests.post(
            f"{server_url.rstrip('/')}/auth/login",
            json={"email": email, "password": password},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("token") or data.get("access_token") or ""
            if token:
                print("Login successful.")
                return token
            print("Login response missing token.")
            return None
        elif resp.status_code == 401:
            print("Invalid credentials.")
            return None
        else:
            print(f"Login failed: HTTP {resp.status_code}")
            return None
    except requests.ConnectionError:
        print(f"Cannot connect to {server_url}")
        return None
    except Exception as exc:
        print(f"Login error: {exc}")
        return None


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="rhea-clip",
        description="Rhea Clipboard Sync — cross-device clipboard with privacy controls",
    )
    parser.add_argument("--server", help="Server URL")
    parser.add_argument("--token", help="Auth token")
    parser.add_argument("--no-tray", action="store_true", help="Run without tray icon (CLI mode)")
    parser.add_argument("--login", action="store_true", help="Interactive login")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    # Logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    cfg = get_config()

    # Apply CLI overrides
    if args.server:
        cfg["server_url"] = args.server
        save_config(cfg)
    if args.token:
        cfg["auth_token"] = args.token
        save_config(cfg)

    # Interactive login
    if args.login:
        token = _login(cfg["server_url"])
        if token:
            cfg["auth_token"] = token
            save_config(cfg)
        else:
            sys.exit(1)

    print(f"Rhea Clipboard v{__version__} \u2014 syncing to {cfg['server_url']}")

    if not cfg["auth_token"]:
        log.warning("no auth token configured \u2014 run with --login or --token to authenticate")

    client = ClipboardClient(
        server_url=cfg["server_url"],
        auth_token=cfg["auth_token"],
        device_id=cfg["device_id"],
        device_name=cfg["device_name"],
    )

    def on_clipboard_change(content: str) -> None:
        client.push(content)

    monitor = ClipboardMonitor(
        on_change=on_clipboard_change,
        poll_interval_ms=cfg.get("poll_interval_ms", 500),
    )
    monitor.start()

    if args.no_tray:
        # CLI mode — monitor only, no GUI
        print(f"Device: {cfg['device_name']} ({cfg['device_id'][:8]})")
        print("Clipboard sync active. Press Ctrl+C to stop.")
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            print("\nStopping...")
            monitor.stop()
    else:
        from .tray import ClipboardTray

        tray = ClipboardTray(client, monitor)

        # SSE listener for incoming remote clips
        def sse_listener() -> None:
            def on_remote_event(event: dict) -> None:
                event_type = event.get("type", "")
                event_device = event.get("device") or event.get("device_name", "")
                if event_type == "clipboard_push" and event_device != cfg["device_name"]:
                    latest = client.pull_latest()
                    if latest and latest.get("clip"):
                        content = latest["clip"].get("content", "")
                        if content:
                            tray.on_remote_clip(content)
                            log.info("received remote clip from %s", event_device)

            client.stream(on_remote_event)

        sse_thread = threading.Thread(target=sse_listener, daemon=True, name="sse-listener")
        sse_thread.start()

        tray.run()  # Blocks until quit


if __name__ == "__main__":
    main()

"""
NDI Bridge — Python FFI to libndi.dylib (NewTek NDI SDK v5+).
Runtime-only linking: no NDI code is shipped or redistributed.

Capabilities:
  - NDI source discovery (find all sources on the network)
  - NDI Send (broadcast frames as an NDI source)
  - NDI version/status reporting

Requires: libndi.dylib installed on the system.
  macOS:  /usr/local/lib/libndi.dylib
  Linux:  /usr/local/lib/libndi.so.6
  Windows: Processing.NDI.Lib.x64.dll
"""

from __future__ import annotations

import ctypes
import ctypes.util
import os
import sys
import time
import struct
import platform
from pathlib import Path
from typing import Optional

# ─── Library Loading ──────────────────────────────────────────────────

_lib = None
_initialized = False

def _find_ndi_library() -> str | None:
    """Locate libndi on the system."""
    if sys.platform == "darwin":
        candidates = [
            "/usr/local/lib/libndi.dylib",
            os.environ.get("NDI_RUNTIME_DIR_V6", "") + "/libndi.dylib",
        ]
    elif sys.platform == "linux":
        candidates = [
            "/usr/local/lib/libndi.so.6",
            "/usr/lib/libndi.so.6",
            os.environ.get("NDI_RUNTIME_DIR_V6", "") + "/libndi.so.6",
        ]
    elif sys.platform == "win32":
        runtime = os.environ.get("NDI_RUNTIME_DIR_V6", "")
        candidates = [
            os.path.join(runtime, "Processing.NDI.Lib.x64.dll") if runtime else "",
        ]
    else:
        candidates = []

    for path in candidates:
        if path and os.path.isfile(path):
            return path
    # Fallback to system search
    return ctypes.util.find_library("ndi")


def _load_ndi():
    """Load libndi and set up function signatures."""
    global _lib, _initialized
    if _lib is not None:
        return _lib

    path = _find_ndi_library()
    if not path:
        raise RuntimeError(
            "NDI runtime not found. Install NDI Tools from https://ndi.video/tools/"
        )

    _lib = ctypes.cdll.LoadLibrary(path)

    # ── Core functions ──
    _lib.NDIlib_initialize.restype = ctypes.c_bool
    _lib.NDIlib_initialize.argtypes = []

    _lib.NDIlib_destroy.restype = None
    _lib.NDIlib_destroy.argtypes = []

    _lib.NDIlib_version.restype = ctypes.c_char_p
    _lib.NDIlib_version.argtypes = []

    _lib.NDIlib_is_supported_CPU.restype = ctypes.c_bool
    _lib.NDIlib_is_supported_CPU.argtypes = []

    # ── Find (discovery) ──
    _lib.NDIlib_find_create_v2.restype = ctypes.c_void_p
    _lib.NDIlib_find_create_v2.argtypes = [ctypes.c_void_p]

    _lib.NDIlib_find_destroy.restype = None
    _lib.NDIlib_find_destroy.argtypes = [ctypes.c_void_p]

    _lib.NDIlib_find_wait_for_sources.restype = ctypes.c_bool
    _lib.NDIlib_find_wait_for_sources.argtypes = [ctypes.c_void_p, ctypes.c_uint32]

    _lib.NDIlib_find_get_current_sources.restype = ctypes.POINTER(NDIlib_source_t)
    _lib.NDIlib_find_get_current_sources.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_uint32),
    ]

    # ── Send ──
    _lib.NDIlib_send_create.restype = ctypes.c_void_p
    _lib.NDIlib_send_create.argtypes = [ctypes.POINTER(NDIlib_send_create_t)]

    _lib.NDIlib_send_destroy.restype = None
    _lib.NDIlib_send_destroy.argtypes = [ctypes.c_void_p]

    _lib.NDIlib_send_send_video_v2.restype = None
    _lib.NDIlib_send_send_video_v2.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(NDIlib_video_frame_v2_t),
    ]

    _lib.NDIlib_send_get_no_connections.restype = ctypes.c_int
    _lib.NDIlib_send_get_no_connections.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint32,
    ]

    # Initialize the library
    if not _lib.NDIlib_initialize():
        raise RuntimeError("NDIlib_initialize() failed — CPU not supported?")
    _initialized = True
    return _lib


# ─── C Struct Definitions ─────────────────────────────────────────────

class NDIlib_source_t(ctypes.Structure):
    """NDI source descriptor returned by find."""
    _fields_ = [
        ("p_ndi_name", ctypes.c_char_p),
        ("p_url_address", ctypes.c_char_p),
    ]


class NDIlib_send_create_t(ctypes.Structure):
    """Configuration for creating an NDI sender."""
    _fields_ = [
        ("p_ndi_name", ctypes.c_char_p),
        ("p_groups", ctypes.c_char_p),
        ("clock_video", ctypes.c_bool),
        ("clock_audio", ctypes.c_bool),
    ]


# NDI FourCC pixel formats
FOURCC_UYVY = 0x59565955  # 'UYVY'
FOURCC_BGRA = 0x41524742  # 'BGRA'
FOURCC_BGRX = 0x58524742  # 'BGRX'
FOURCC_RGBA = 0x41424752  # 'RGBA'
FOURCC_RGBX = 0x58424752  # 'RGBX'

class NDIlib_video_frame_v2_t(ctypes.Structure):
    """Video frame for NDI send."""
    _fields_ = [
        ("xres", ctypes.c_int),
        ("yres", ctypes.c_int),
        ("FourCC", ctypes.c_uint32),
        ("frame_rate_N", ctypes.c_int),
        ("frame_rate_D", ctypes.c_int),
        ("picture_aspect_ratio", ctypes.c_float),
        ("frame_format_type", ctypes.c_int),  # 0 = progressive
        ("timecode", ctypes.c_int64),
        ("p_data", ctypes.c_void_p),
        ("line_stride_in_bytes", ctypes.c_int),
        ("p_metadata", ctypes.c_char_p),
        ("timestamp", ctypes.c_int64),
    ]


# ─── High-Level API ──────────────────────────────────────────────────

def version() -> str:
    """Get NDI SDK version string."""
    lib = _load_ndi()
    return lib.NDIlib_version().decode("utf-8")


def discover_sources(timeout_ms: int = 2000) -> list[dict]:
    """
    Discover all NDI sources on the local network.
    Returns list of {name, url} dicts.
    """
    lib = _load_ndi()

    finder = lib.NDIlib_find_create_v2(None)
    if not finder:
        return []

    try:
        # Wait for sources to appear
        lib.NDIlib_find_wait_for_sources(finder, timeout_ms)

        num_sources = ctypes.c_uint32(0)
        sources = lib.NDIlib_find_get_current_sources(
            finder, ctypes.byref(num_sources)
        )

        result = []
        for i in range(num_sources.value):
            name = sources[i].p_ndi_name
            url = sources[i].p_url_address
            result.append({
                "name": name.decode("utf-8") if name else "unknown",
                "url": url.decode("utf-8") if url else "",
            })
        return result
    finally:
        lib.NDIlib_find_destroy(finder)


def status() -> dict:
    """Get NDI runtime status."""
    try:
        lib = _load_ndi()
        ver = lib.NDIlib_version().decode("utf-8")
        cpu_ok = lib.NDIlib_is_supported_CPU()
        sources = discover_sources(timeout_ms=1500)
        return {
            "available": True,
            "version": ver,
            "cpu_supported": cpu_ok,
            "library_path": _find_ndi_library(),
            "sources_on_network": len(sources),
            "sources": sources,
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
            "library_path": _find_ndi_library(),
        }


# ─── NDI Sender ──────────────────────────────────────────────────────

class NDISender:
    """
    Broadcast RGBA frames as an NDI source.
    Visible to any NDI receiver on the network (including iPhone NDI Monitor).
    """

    def __init__(self, name: str = "Rhea Command Centre", groups: str = None):
        self._lib = _load_ndi()
        self._name = name.encode("utf-8")

        create_desc = NDIlib_send_create_t()
        create_desc.p_ndi_name = self._name
        create_desc.p_groups = groups.encode("utf-8") if groups else None
        create_desc.clock_video = True
        create_desc.clock_audio = False

        self._sender = self._lib.NDIlib_send_create(ctypes.byref(create_desc))
        if not self._sender:
            raise RuntimeError("Failed to create NDI sender")

        self._frame = NDIlib_video_frame_v2_t()
        self._frame.frame_format_type = 0  # progressive

    def send_rgba(self, data: bytes, width: int, height: int, fps: int = 30):
        """Send a single RGBA frame."""
        self._frame.xres = width
        self._frame.yres = height
        self._frame.FourCC = FOURCC_RGBA
        self._frame.frame_rate_N = fps * 1000
        self._frame.frame_rate_D = 1000
        self._frame.picture_aspect_ratio = width / height
        self._frame.timecode = int(time.time() * 10_000_000)  # 100ns units
        self._frame.line_stride_in_bytes = width * 4
        self._frame.p_metadata = None
        self._frame.timestamp = 0  # synthesized

        # Pin data in memory for the send call
        buf = ctypes.create_string_buffer(data)
        self._frame.p_data = ctypes.cast(buf, ctypes.c_void_p)
        self._lib.NDIlib_send_send_video_v2(
            self._sender, ctypes.byref(self._frame)
        )

    def send_test_pattern(self, width: int = 1920, height: int = 1080):
        """Send a single color-bar test frame (useful for verifying connectivity)."""
        # Simple 8-color bar pattern (RGBA)
        colors = [
            (255, 255, 255, 255),  # White
            (255, 255, 0, 255),    # Yellow
            (0, 255, 255, 255),    # Cyan
            (0, 255, 0, 255),      # Green
            (255, 0, 255, 255),    # Magenta
            (255, 0, 0, 255),      # Red
            (0, 0, 255, 255),      # Blue
            (0, 0, 0, 255),        # Black
        ]
        bar_width = width // len(colors)
        row = b""
        for c in colors:
            row += bytes(c) * bar_width
        # Pad remainder
        row += bytes(colors[-1]) * (width - bar_width * len(colors))
        frame_data = row * height
        self.send_rgba(frame_data, width, height)

    @property
    def num_connections(self) -> int:
        """How many receivers are connected to this sender."""
        return self._lib.NDIlib_send_get_no_connections(self._sender, 0)

    def destroy(self):
        if self._sender:
            self._lib.NDIlib_send_destroy(self._sender)
            self._sender = None

    def __del__(self):
        self.destroy()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.destroy()


# ─── CLI ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "status":
        print(json.dumps(status(), indent=2))

    elif cmd == "discover":
        timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
        sources = discover_sources(timeout)
        print(json.dumps(sources, indent=2))

    elif cmd == "version":
        print(version())

    elif cmd == "test-send":
        # Send test pattern for 10 seconds (visible in NDI Monitor)
        name = sys.argv[2] if len(sys.argv) > 2 else "Rhea CC Test"
        duration = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        print(f"Sending NDI test pattern as '{name}' for {duration}s...")
        with NDISender(name) as sender:
            start = time.time()
            frames = 0
            while time.time() - start < duration:
                sender.send_test_pattern(1920, 1080)
                frames += 1
                time.sleep(1 / 30)
            print(f"Sent {frames} frames, {sender.num_connections} receivers connected")

    else:
        print(f"Usage: python3 {sys.argv[0]} [status|discover|version|test-send [name] [seconds]]")

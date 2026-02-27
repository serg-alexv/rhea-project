#!/usr/bin/env python3
"""rhea_compress.py — Semantic image compression for Rhea.
Vision model sees blob + recipient → returns tailored text summary.
Image stored locally; only summary is transmitted.

Usage:
    python3 src/rhea_compress.py <image_path> <recipient> [--relay]
    from src.rhea_compress import compress
"""
import os, sys, json, shutil
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rhea_bridge import RheaBridge

ORIGINALS_DIR = Path(__file__).parent.parent / "data" / "compress" / "originals"

RECIPIENT_PROMPTS = {
    "REX": (
        "Summarizing for REX (backend coordinator). Focus on: API status, errors, metrics, "
        "system state, logs, stack traces. Ignore aesthetics. Flag anomalies."
    ),
    "ORION": (
        "Summarizing for ORION (frontend engineer). Focus on: layout, UI components, colors, "
        "spacing, typography, responsiveness. Note broken layouts or misaligned elements."
    ),
    "HYPERION": (
        "Summarizing for HYPERION (security auditor). Focus on: security warnings, permission "
        "errors, invariant violations, provenance issues, suspicious patterns."
    ),
    "MIKA": (
        "Summarizing for MIKA (executive reader). Exactly 2 sentences: what is shown, "
        "and what is broken or notable. No technical jargon."
    ),
}

DEFAULT_PROMPT = (
    "Summarizing for a technical team. Describe content, structure, visible text, "
    "errors, and notable elements factually."
)


def _store_original(image_path: str) -> str:
    ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)
    src = Path(image_path)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    dest = ORIGINALS_DIR / f"{ts}_{src.name}"
    shutil.copy2(src, dest)
    return str(dest)


def _build_prompt(recipient: str) -> str:
    system = RECIPIENT_PROMPTS.get(recipient.upper().strip(), DEFAULT_PROMPT)
    return f"{system}\n\nSummarize the image. Max 300 tokens. No pleasantries."


def compress(image_path: str, recipient: str) -> dict:
    """Return recipient-tailored text summary of an image.

    Returns:
        summary, tokens_used, tokens_saved, compression_ratio, model_used, original_ref
    """
    image_path = str(Path(image_path).resolve())
    if not Path(image_path).exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    file_size = Path(image_path).stat().st_size
    original_ref = _store_original(image_path)

    bridge = RheaBridge()
    response = bridge.ask_vision(
        image_path=image_path,
        prompt=_build_prompt(recipient),
        tier="cheap",
        max_tokens=300,
    )

    if response.error:
        raise RuntimeError(f"Vision model error: {response.error}")

    tokens_used = response.tokens_used or 0
    raw_estimate = max(1, file_size // 4)          # 1 token ≈ 4 bytes for images
    tokens_saved = raw_estimate - tokens_used
    compression_ratio = round(raw_estimate / max(1, tokens_used), 2)

    return {
        "summary": response.text.strip(),
        "tokens_used": tokens_used,
        "tokens_saved": tokens_saved,
        "compression_ratio": compression_ratio,
        "model_used": f"{response.provider}/{response.model}",
        "original_ref": original_ref,
    }


def _relay(result: dict, image_path: str, recipient: str) -> None:
    firebase_script = Path(__file__).parent.parent / "opera" / "ops" / "rhea_firebase.py"
    if not firebase_script.exists():
        print("[compress] Firebase relay script not found, skipping.", file=sys.stderr)
        return
    message = json.dumps({
        "job": "image_compress", "recipient": recipient,
        "source": image_path, **result,
    })
    sys.path.insert(0, str(firebase_script.parent))
    from rhea_firebase import cmd_send
    cmd_send("COMPRESS", recipient, message)
    print(f"[compress] Relayed to Firebase → {recipient}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 src/rhea_compress.py <image_path> <recipient> [--relay]")
        sys.exit(1)
    result = compress(sys.argv[1], sys.argv[2])
    print(json.dumps(result, indent=2))
    if "--relay" in sys.argv:
        _relay(result, sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()

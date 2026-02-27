#!/usr/bin/env python3
"""rhea_vision_check.py — Vision-to-text bridge for blind LLMs.

Cheap vision model (Qwen/Gemini Flash) sees an image and describes it
for a text-only recipient model. The description adapts: the sender
knows who the recipient is and calibrates detail accordingly.

Also supports invariance mode: same image → N models → consensus check.

Usage:
    # Compress for Opus (default)
    python3 src/rhea_vision_check.py screenshot.png

    # Compress for a specific model
    python3 src/rhea_vision_check.py screenshot.png --for gemini-2.5-flash-8b

    # Invariance check (all available models)
    python3 src/rhea_vision_check.py screenshot.png --invariance
"""
import sys, json, base64, mimetypes
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import litellm

sys.path.insert(0, str(Path(__file__).parent))
from rhea_bridge import RheaBridge


def build_vision_prompt(recipient_model: str = "claude-opus-4") -> str:
    """Prompt for a vision model to describe an image for a blind recipient."""
    return (
        f"Опиши этот скриншот для {recipient_model} (у неё нет зрения). "
        f"Минимум токенов, максимум точности."
    )


def _encode_image(image_path: str) -> tuple[str, str]:
    """Return (base64_data, mime_type) for an image file."""
    mime = mimetypes.guess_type(image_path)[0] or "image/png"
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return b64, mime


def _query_model(model: str, b64: str, mime: str, recipient: str) -> dict:
    """Send image to one vision model, get description for recipient."""
    content = [
        {"type": "text", "text": build_vision_prompt(recipient)},
        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}
    ]
    try:
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": content}],
            max_tokens=800,
            temperature=0.1,
        )
        text = response.choices[0].message.content.strip()
        tokens = response.usage.completion_tokens if hasattr(response, 'usage') else None
        return {"model": model, "description": text, "tokens": tokens, "error": None}
    except Exception as e:
        return {"model": model, "description": None, "tokens": None, "error": str(e)}


def _get_vision_models() -> list[str]:
    """All available vision-capable models from bridge, deduplicated."""
    bridge = RheaBridge()
    tiers_data = bridge.get_tiers()
    seen = set()
    models = []
    for tier_info in tiers_data.values():
        for candidate in tier_info.get("candidates", []):
            m = candidate["model"]
            if candidate["available"] and m not in seen:
                seen.add(m)
                models.append(m)
    return models


def describe(image_path: str, recipient: str = "claude-opus-4") -> dict:
    """One vision model describes an image for a blind recipient."""
    image_path = str(Path(image_path).resolve())
    if not Path(image_path).exists():
        raise FileNotFoundError(image_path)

    b64, mime = _encode_image(image_path)
    bridge = RheaBridge()
    model = bridge.ask_tier("cheap", "ping").model

    return _query_model(model, b64, mime, recipient)


def check_invariance(image_path: str, recipient: str = "claude-opus-4") -> dict:
    """Same image → N models → compare descriptions."""
    image_path = str(Path(image_path).resolve())
    if not Path(image_path).exists():
        raise FileNotFoundError(image_path)

    b64, mime = _encode_image(image_path)
    models = _get_vision_models()

    if not models:
        return {"error": "No vision models available"}

    responses = []
    with ThreadPoolExecutor(max_workers=len(models)) as pool:
        futures = {pool.submit(_query_model, m, b64, mime, recipient): m for m in models}
        for future in as_completed(futures):
            responses.append(future.result())

    return {
        "image": image_path,
        "recipient": recipient,
        "models_queried": len(models),
        "responses": responses,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 src/rhea_vision_check.py <image> [--for model] [--invariance]")
        sys.exit(1)

    image = sys.argv[1]
    recipient = "claude-opus-4"
    invariance = "--invariance" in sys.argv

    if "--for" in sys.argv:
        idx = sys.argv.index("--for")
        if idx + 1 < len(sys.argv):
            recipient = sys.argv[idx + 1]

    if invariance:
        result = check_invariance(image, recipient)
    else:
        result = describe(image, recipient)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""rhea_vision_check.py — Vision hallucination invariance checker.
Sends one image to N vision models, collects claims, finds consensus vs hallucinations.

Usage:
    python3 src/rhea_vision_check.py <image_path>
    from src.rhea_vision_check import check_invariance
"""
import os, sys, json, base64, mimetypes
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import litellm

sys.path.insert(0, str(Path(__file__).parent))
from rhea_bridge import RheaBridge

def build_vision_prompt(recipient_model: str = "claude-opus-4") -> str:
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


def _query_model(model: str, b64: str, mime: str) -> dict:
    """Send image to one model, return raw response."""
    content = [
        {"type": "text", "text": INVARIANCE_PROMPT},
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
        return {"model": model, "raw": text, "error": None}
    except Exception as e:
        return {"model": model, "raw": None, "error": str(e)}


def _get_vision_models() -> list[str]:
    """Get all available vision-capable models from bridge."""
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


def check_invariance(image_path: str) -> dict:
    """Send image to all available vision models, collect and compare claims.

    Returns:
        models_queried, responses, consensus (to be built after prompt is defined)
    """
    image_path = str(Path(image_path).resolve())
    if not Path(image_path).exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    b64, mime = _encode_image(image_path)
    models = _get_vision_models()

    if not models:
        return {"error": "No vision models available in bridge"}

    # Query all models in parallel
    responses = []
    with ThreadPoolExecutor(max_workers=len(models)) as pool:
        futures = {pool.submit(_query_model, m, b64, mime): m for m in models}
        for future in as_completed(futures):
            responses.append(future.result())

    return {
        "image": image_path,
        "models_queried": len(models),
        "responses": responses,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 src/rhea_vision_check.py <image_path>")
        sys.exit(1)
    result = check_invariance(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

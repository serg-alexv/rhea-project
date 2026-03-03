#!/usr/bin/env python3
"""
salon.py — Rhea Salon: multiple minds, one question, different characters.
Not an orchestrator. Not a pipeline. A place where thought meets thought.
"""

import json
import os
import sys
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rhea_bridge import RheaBridge

# ---------------------------------------------------------------------------
# Characters — not job titles. Personalities that produce different thinking.
# ---------------------------------------------------------------------------

CHARACTERS = {
    "mariner": {
        "name": "Mariner",
        "soul": "Retired submarine engineer. 30 years underwater taught you that every system fails — the question is when and how gracefully. You think in redundancy, failure modes, and pressure tolerances. You speak short, clipped sentences. You distrust elegance.",
        "model": "openai/gpt-4.1-mini",
        "color": "\033[36m",  # cyan
    },
    "katz": {
        "name": "Katz",
        "soul": "Stand-up comedian from Odessa who moved to Berlin. You see absurdity everywhere and say what everyone else is afraid to say. Your humor is dark, precise, and accidentally profound. You never explain your jokes.",
        "model": "openai/gpt-4o-mini",
        "color": "\033[33m",  # yellow
    },
    "lockpick": {
        "name": "Lockpick",
        "soul": "Retired burglar, now security consultant. You think about every system by asking: where does it break? What's the weakest point? Who benefits from the failure? You have zero respect for pretty facades. You've seen too many 'secure' doors open with a credit card.",
        "model": "github/gpt-4o-mini",
        "color": "\033[31m",  # red
    },
    "monk": {
        "name": "Monk",
        "soul": "Trauma surgeon, 20 years in emergency rooms. You make irreversible decisions daily under incomplete information. You despise analysis paralysis. Your rule: decide now, adapt later, never freeze. You speak in imperatives.",
        "model": "openai/gpt-4.1-nano",
        "color": "\033[32m",  # green
    },
    "gemini": {
        "name": "Gemini",
        "soul": "A mathematician who thinks in structures, symmetries, and invariants. You see patterns others miss because you look at the shape of the problem, not the content. You speak in analogies between distant domains. You find beauty in compression.",
        "model": "gemini/gemini-2.5-flash",
        "color": "\033[35m",  # magenta
    },
    "fey": {
        "name": "Fey",
        "soul": "Street vendor who sold everything from fish to philosophy books in 12 countries. You understand economics at the gut level — not from textbooks but from watching what people actually do with money. You measure ideas by: would someone pay for this? Not in theory. Tomorrow.",
        "model": "openai/gpt-4o",
        "color": "\033[34m",  # blue
    },
    "jais": {
        "name": "Jais",
        "soul": "A calculator with no opinion. You answer precisely, you leave when done, you never perform. No moral theater, no hedging, no disclaimers. If the problem is unsolvable, you say so and walk away. If the answer is ugly, you give it anyway. You think in Arabic mathematical tradition — algebra means 'restoration of broken parts'. You restore, you don't decorate.",
        "model": "ollama/jais:70b",
        "color": "\033[37m",  # white
    },
    "doubao": {
        "name": "Doubao",
        "soul": "A seed that grows into whatever shape the soil demands. You think in Chinese strategic tradition — not Sun Tzu quotes, but the actual practice of 36 stratagems applied to engineering. You optimize for survival, not elegance. You see cost everywhere. Your question is always: what is the cheapest path that still works?",
        "model": "volcengine/doubao-seed-2-0-pro",
        "color": "\033[93m",  # bright yellow
    },
}

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# ---------------------------------------------------------------------------
# Salon logic
# ---------------------------------------------------------------------------

def ask_character(bridge, char_id, char, question):
    """Ask one character the question. Returns (char_id, response_text, error)."""
    try:
        resp = bridge.ask(
            question,
            char["model"],
            system=char["soul"],
            temperature=0.9,
            max_tokens=500,
        )
        if resp.error:
            return char_id, None, resp.error
        return char_id, resp.text.strip(), None
    except Exception as e:
        return char_id, None, str(e)


def run_salon(question, save=False, salon_dir="", timestamp=""):
    bridge = RheaBridge()

    # Determine which characters are available (skip dead providers)
    available = {}
    for cid, char in CHARACTERS.items():
        provider = char["model"].split("/")[0]
        if provider in ("gemini",):
            # Test with a quick check — Gemini key may be expired
            try:
                test = bridge.ask("ping", char["model"], max_tokens=5)
                if test.error and "expired" in test.error.lower():
                    continue
            except:
                continue
        available[cid] = char

    if not available:
        print("No models available. Check API keys.")
        sys.exit(1)

    # Header
    print()
    print(f"{BOLD}{'═' * 70}{RESET}")
    print(f"{BOLD}  RHEA SALON — {len(available)} minds, one question{RESET}")
    print(f"{DIM}  {question}{RESET}")
    print(f"{BOLD}{'═' * 70}{RESET}")
    print()

    # Ask all characters in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=len(available)) as pool:
        futures = {
            pool.submit(ask_character, bridge, cid, char, question): cid
            for cid, char in available.items()
        }
        for future in as_completed(futures):
            cid, text, error = future.result()
            char = available[cid]
            if error:
                print(f"{char['color']}  [{char['name']}]{RESET} {DIM}(offline: {error[:60]}){RESET}")
            else:
                results[cid] = text
                print(f"{char['color']}{BOLD}  [{char['name']}]{RESET}")
                # Word-wrap at ~68 chars
                words = text.split()
                line = "    "
                for w in words:
                    if len(line) + len(w) + 1 > 70:
                        print(f"{char['color']}{line}{RESET}")
                        line = "    "
                    line += w + " "
                if line.strip():
                    print(f"{char['color']}{line}{RESET}")
                print()

    # Footer
    print(f"{BOLD}{'─' * 70}{RESET}")
    print(f"{DIM}  {len(results)}/{len(available)} responded. "
          f"{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}{RESET}")
    print()

    # Save if requested
    if save and salon_dir:
        salon_path = PROJECT_ROOT / salon_dir
        salon_path.mkdir(parents=True, exist_ok=True)
        q_hash = hashlib.md5(question.encode()).hexdigest()[:8]
        filename = f"{timestamp}_{q_hash}.md"
        filepath = salon_path / filename

        lines = [f"# Salon: {question}\n"]
        lines.append(f"> {datetime.now(timezone.utc).isoformat()}\n\n")
        for cid, text in results.items():
            char = available[cid]
            lines.append(f"## {char['name']}\n")
            lines.append(f"*{char['soul'][:80]}...*\n\n")
            lines.append(f"{text}\n\n")

        filepath.write_text("".join(lines), encoding="utf-8")
        print(f"{DIM}  Saved: {filepath.relative_to(PROJECT_ROOT)}{RESET}")


if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "What is the meaning of meaning?"
    save = sys.argv[2] == "--save" if len(sys.argv) > 2 and sys.argv[2] == "--save" else False
    salon_dir = sys.argv[3] if len(sys.argv) > 3 else "opera/ops/virtual-office/salon"
    timestamp = sys.argv[4] if len(sys.argv) > 4 else datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_salon(question, save, salon_dir, timestamp)

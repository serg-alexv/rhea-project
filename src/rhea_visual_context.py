# Rhea Visual Context Store
# Holds the latest shared visual state and context health metrics.

import time
import math

_state = {
    "url": "none",
    "title": "none",
    "elements": []
}

# Historical health pulses for the MRI heatmap
_history = []

def update_state(new_state: dict):
    global _state
    _state.update(new_state)
    # Add a health pulse on every sync
    _pulse_health()

def get_state() -> dict:
    return _state

def _pulse_health():
    """Generates a health pulse based on current state and last response."""
    global _history
    pulse = {
        "timestamp": time.time(),
        "fact_density": 0.8, # Placeholder: will be calculated from receipts
        "drift": math.sin(time.time() / 100) * 0.2 + 0.5, # Placeholder: semantic distance
        "logic_depth": 0.7,
        "mode": "stable"
    }
    _history.append(pulse)
    # Keep last 50 pulses
    if len(_history) > 50:
        _history.pop(0)

def get_health_history():
    return _history

def get_context_block() -> str:
    """Generates a text block for LLM context based on the current UI."""
    s = get_state()
    if s["url"] == "none":
        return ""
        
    lines = ["\n=== CURRENT BROWSER CONTEXT (HUMAN-LIKE VISION) ==="]
    lines.append(f"URL: {s['url']}")
    lines.append(f"PAGE TITLE: {s['title']}")
    
    if s["elements"]:
        lines.append("VISIBLE INTERACTIVE ELEMENTS:")
        # Limit to top 15 elements to avoid bloat
        for el in s["elements"][:15]:
            # Use single quotes inside f-string to avoid quote collision
            lines.append(f"- [{el['id']}] {el['tag']} (role: {el['role']}): '{el['text']}'")
            
    lines.append("====================================================\n")
    return "\n".join(lines)

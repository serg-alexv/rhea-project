# Rhea Visual Context Store
# Holds the latest shared visual state from the browser extension.

_state = {
    "url": "none",
    "title": "none",
    "elements": []
}

def update_state(new_state: dict):
    global _state
    _state.update(new_state)

def get_state() -> dict:
    return _state

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

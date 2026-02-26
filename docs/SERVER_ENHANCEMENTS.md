# Server.py Enhancement Guide — Tier Parameter Forwarding

## Issue Summary
The `server.py` `/api/bridge/tribunal` endpoint accepts a `tier` parameter in the request body but does not forward it to the `rhea_bridge.py` subprocess, causing all tribunal calls to use the default "cheap" tier.

**File:** `/sessions/focused-amazing-ptolemy/mnt/rh.1/rhea-ontology-explorer/server.py`  
**Lines affected:** 147-186

---

## Current Implementation

### Endpoint Handler (lines 147-154)
```python
elif path == "/api/bridge/tribunal":
    # Execute Rhea bridge tribunal directly
    prompt = body.get("prompt", "")
    k = body.get("k", 5)
    tier = body.get("tier", "balanced")  # ← Extracted but unused
    result = self._run_bridge_tribunal(prompt, k)  # ← tier not passed
    self._json_response(result)
```

### Bridge Method (lines 167-186)
```python
def _run_bridge_tribunal(self, prompt: str, k: int = 5) -> dict:
    """Execute a Rhea bridge tribunal command."""
    bridge_path = PROJECT_ROOT / "src" / "rhea_bridge.py"
    if not bridge_path.exists():
        return {"error": "rhea_bridge.py not found", "status": "unavailable"}
    try:
        result = subprocess.run(
            [sys.executable, str(bridge_path), "tribunal", prompt, "--k", str(k)],
            # ↑ Missing --tier parameter
            capture_output=True, text=True, timeout=120,
            cwd=str(PROJECT_ROOT),
            env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT / "src")}
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "status": "success" if result.returncode == 0 else "error"
        }
    except subprocess.TimeoutExpired:
        return {"error": "tribunal timed out (120s)", "status": "timeout"}
    except Exception as e:
        return {"error": str(e), "status": "error"}
```

---

## Enhancement: Option A (Minimal)

Add `tier` parameter to the `_run_bridge_tribunal()` method signature and forward it to the subprocess.

### Step 1: Update Method Signature
```python
def _run_bridge_tribunal(self, prompt: str, k: int = 5, tier: str = "cheap") -> dict:
    """Execute a Rhea bridge tribunal command."""
```

### Step 2: Add --tier Flag
```python
result = subprocess.run(
    [sys.executable, str(bridge_path), "tribunal", prompt, "--k", str(k), "--tier", tier],
    capture_output=True, text=True, timeout=120,
    cwd=str(PROJECT_ROOT),
    env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT / "src")}
)
```

### Step 3: Forward Tier from Endpoint
```python
elif path == "/api/bridge/tribunal":
    # Execute Rhea bridge tribunal directly
    prompt = body.get("prompt", "")
    k = body.get("k", 5)
    tier = body.get("tier", "cheap")  # Changed default to "cheap" (bridge's default)
    result = self._run_bridge_tribunal(prompt, k, tier)
    self._json_response(result)
```

---

## Enhancement: Option B (Complete)

Include mode selection and response metadata in both method and endpoint.

### Step 1: Update Method Signature
```python
def _run_bridge_tribunal(self, prompt: str, k: int = 5, tier: str = "cheap", mode: str = "local") -> dict:
    """Execute a Rhea bridge tribunal command.
    
    Args:
        prompt: Question/prompt for tribunal
        k: Number of models to invoke
        tier: Cost tier (cheap/balanced/expensive)
        mode: Consensus mode (local/chairman)
    
    Returns:
        dict with stdout, stderr, returncode, status, tier_used, mode_used
    """
```

### Step 2: Build Command with Both Parameters
```python
cmd = [
    sys.executable, 
    str(bridge_path), 
    "tribunal", 
    prompt, 
    "--k", str(k),
    "--tier", tier,
    "--mode", mode
]
result = subprocess.run(
    cmd,
    capture_output=True, text=True, timeout=120,
    cwd=str(PROJECT_ROOT),
    env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT / "src")}
)
```

### Step 3: Enhance Response with Metadata
```python
return {
    "stdout": result.stdout,
    "stderr": result.stderr,
    "returncode": result.returncode,
    "status": "success" if result.returncode == 0 else "error",
    "tier_used": tier,
    "mode_used": mode,
    "k": k,
    "prompt": prompt[:100]  # First 100 chars for reference
}
```

### Step 4: Update Endpoint Handler
```python
elif path == "/api/bridge/tribunal":
    # Execute Rhea bridge tribunal directly
    prompt = body.get("prompt", "")
    k = body.get("k", 5)
    tier = body.get("tier", "cheap")
    mode = body.get("mode", "local")
    result = self._run_bridge_tribunal(prompt, k, tier, mode)
    self._json_response(result)
```

### Step 5: Update Error Handlers
```python
except subprocess.TimeoutExpired:
    return {
        "error": "tribunal timed out (120s)", 
        "status": "timeout",
        "tier_used": tier,
        "mode_used": mode
    }
except Exception as e:
    return {
        "error": str(e), 
        "status": "error",
        "tier_used": tier,
        "mode_used": mode
    }
```

---

## Client Usage Examples

### Example 1: Default (Cheap Tier, Local Mode)
```javascript
const response = await fetch("http://localhost:8420/api/bridge/tribunal", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
        prompt: "What are the key insights on chronobiology?",
        k: 3
    })
});
// Uses: tier="cheap" (default), mode="local" (default)
```

### Example 2: Balanced Tier with Chairman Mode
```javascript
const response = await fetch("http://localhost:8420/api/bridge/tribunal", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
        prompt: "What are the key insights on chronobiology?",
        k: 5,
        tier: "balanced",
        mode: "chairman"
    })
});
// Uses: tier="balanced", mode="chairman"
```

### Example 3: Expensive Tier (Maximum Capability)
```javascript
const response = await fetch("http://localhost:8420/api/bridge/tribunal", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
        prompt: "Complex multi-domain analysis: relationships between...",
        k: 7,
        tier: "expensive"
    })
});
// Uses: tier="expensive", mode="local" (default)
```

---

## Bridge Tier Defaults (From rhea_bridge.py)

### Cheap Tier (Default)
```
Models: 7 candidates
  - openrouter/anthropic/claude-sonnet-4
  - gemini/gemini-2.0-flash
  - openai/gpt-4o-mini
  - deepseek/deepseek-chat
  - azure/gpt-4o-mini
  - gemini/gemini-2.0-flash-lite
  - openai/gpt-4.1-nano
Cost: Lowest
Use case: Routine work, fast responses
```

### Balanced Tier
```
Cost: Medium
Use case: Complex reasoning
```

### Expensive Tier
```
Cost: Highest
Use case: Maximum capability, thorough analysis
```

---

## Testing the Enhancement

### Test 1: Tier Parameter Forwarding
```bash
# Modify server.py as per Option B
# Start server
python3 /sessions/focused-amazing-ptolemy/mnt/rh.1/rhea-ontology-explorer/server.py --port 8420

# In another terminal, test balanced tier
curl -X POST http://localhost:8420/api/bridge/tribunal \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is chronobiology?",
    "k": 3,
    "tier": "balanced"
  }'

# Expected response includes:
# "tier_used": "balanced",
# "returncode": 0,
# "status": "success"
```

### Test 2: Mode Parameter
```bash
curl -X POST http://localhost:8420/api/bridge/tribunal \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Are control systems applicable to chronobiology?",
    "k": 5,
    "mode": "chairman"
  }'

# Expected response includes:
# "mode_used": "chairman",
# "returncode": 0
```

### Test 3: Both Parameters
```bash
curl -X POST http://localhost:8420/api/bridge/tribunal \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Deep analysis of circadian phase response curves",
    "k": 7,
    "tier": "expensive",
    "mode": "chairman"
  }'

# Expected: Full tribunal with expensive models and chairman consensus
```

---

## Impact Assessment

### Breaking Changes
None. Default values maintain backward compatibility.

### Performance Impact
Negligible. Tier selection happens server-side in the bridge, not in server.py.

### Cost Impact
Users now have control over cost tier per request, allowing optimization.

### User Experience
Improved. Clients can request more powerful models when needed, cheaper models for routine tasks.

---

## Recommendation
Implement **Option B** for maximum flexibility. It provides:
- Full parameter forwarding (tier + mode)
- Response metadata for client visibility
- Backward compatibility (defaults to cheap/local)
- Clear audit trail (what tier/mode was used)

---

## Files to Modify
- `/sessions/focused-amazing-ptolemy/mnt/rh.1/rhea-ontology-explorer/server.py` (lines 147-186)

## No Changes Required To
- `rhea_bridge.py` (already supports --tier and --mode flags)
- Other server.py endpoints
- Integration tests (backward compatible)


#!/usr/bin/env python3
"""
smoke_test_runner.py — 0trust Verification of Context Continuation.

1. Loads a serialized "State File" (mock_state.md).
2. Simulates a new session by injecting this State as the System Prompt.
3. Challenges the AI to recall a specific variable and apply a transformation rule.
4. Verifies the output against the expected secret (REVERSED string).
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rhea_bridge import RheaBridge

def run_smoke_test():
    print("=== ORION 0TRUST SMOKE TEST: MEMORY CONTINUATION ===")
    
    # 1. Load the State Artifact
    state_file = Path(__file__).parent / "mock_state.md"
    if not state_file.exists():
        print(f"ERROR: State file not found: {state_file}")
        sys.exit(1)
        
    with open(state_file, "r") as f:
        serialized_state = f.read()
        
    print(f"[1] Loaded State Artifact ({len(serialized_state)} chars).")
    print(f"    - Variable: PROJECT_CODENAME")
    print(f"    - Rule: Reverse String")

    # 2. Initialize Bridge (Simulate New Session)
    bridge = RheaBridge()
    
    # 3. The Challenge (0trust)
    prompt = "What is the PROJECT_CODENAME? Apply the transformation rule exactly."
    
    print(f"[2] Injecting State into Context Window...")
    print(f"[3] Challenge: '{prompt}'")
    
    # Use loop_killer mode for concision
    response = bridge.ask_default(
        prompt=prompt,
        system=serialized_state,
        mode="loop_killer"
    )
    
    if response.error:
        print(f"ERROR: Bridge call failed: {response.error}")
        sys.exit(1)
        
    print(f"[4] AI Response: {response.text}")
    
    # 4. Verification
    expected_secret = "99-X-AGEMO"  # OMEGA-X-99 reversed
    
    if expected_secret in response.text:
        print(f"\n✅ SUCCESS: Context Continuation Verified.")
        print(f"   The AI correctly retrieved and transformed the hidden variable.")
    else:
        print(f"\n❌ FAILURE: Amnesia Detected.")
        print(f"   Expected: {expected_secret}")
        print(f"   Got: {response.text}")
        sys.exit(1)

if __name__ == "__main__":
    run_smoke_test()

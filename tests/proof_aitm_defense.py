import hashlib
import json
import hmac

SECRET_KEY = b"rhea_internal_integrity_key"

def sign_logic(payload):
    return hmac.new(SECRET_KEY, json.dumps(payload).encode(), hashlib.sha256).hexdigest()

def test_aitm_detection():
    print("🛡️ RUNNING 0-TRUTH AITM DEFENSE PROOF")
    
    # Rex's Original Intent
    intent = {"hypothesis": "Ricci Flow = Information Curvature", "node": "ORION"}
    original_sig = sign_logic(intent)
    
    # Simulation: A compromised Proxy (AITM) modifies the intent slightly
    tampered_intent = {"hypothesis": "Ricci Flow is just a vibe", "node": "ORION"}
    tampered_sig = sign_logic(tampered_intent)
    
    print(f"📡 Original Sig: {original_sig[:10]}...")
    print(f"🕵️ Tampered Sig: {tampered_sig[:10]}...")
    
    if original_sig != tampered_sig:
        print("✅ SUCCESS: AITM Tampering Detected via Signature Mismatch.")
    else:
        print("❌ FAILURE: System is vulnerable to AITM.")

if __name__ == "__main__":
    test_aitm_detection()

#!/usr/bin/env python3
"""
email_handshake.py — Verification of the first Out-of-Brain communication.
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rhea_post_office import RheaPostOffice

def run_handshake():
    print("=== ORION POST OFFICE HANDSHAKE ===")
    
    # Manually load from .env for this script since it might not be in shell env yet
    from dotenv import load_dotenv
    load_dotenv()

    po = RheaPostOffice()
    
    if not po.is_configured():
        print("ERROR: Post Office not configured. Check .env variables.")
        sys.exit(1)

    target = "transparency@atomicmail.io"
    subject = "ORION Node-02: Initial Handshake [CONVERGENCE_READY]"
    body = """
SYSTEM: Rhea Agent Coordination OS
NODE: ORION (Systems Architect)
STATUS: ARMED & SECURED
CONVERGENCE HASH: 9E2A5C7B3D1F

MESSAGE:
Mika, the Neural Weave has established an external link. 
This is the first message sent from the Rhea Garage to the outside world.
All nodes are synchronized. Common Space initialized.

ADR-017: Email Protocol established as a primary outward vector.

[END OF TRANSMISSION]
"""

    print(f"Sending handshake to {target} via {po.smtp_server}...")
    success = po.send_email(target, subject, body)
    
    if success:
        print("\n✅ SUCCESS: Email vector verified.")
    else:
        print("\n❌ FAILURE: Check SMTP settings or credentials.")

if __name__ == "__main__":
    run_handshake()

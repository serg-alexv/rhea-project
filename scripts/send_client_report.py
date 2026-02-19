#!/usr/bin/env python3
"""
client_report_send.py — Sends the finalized genomic report to the client.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rhea_post_office import RheaPostOffice

def send_report():
    print("=== ORION: SENDING REPORT TO CLIENT ===")
    load_dotenv()

    po = RheaPostOffice()
    if not po.is_configured():
        print("ERROR: Post Office not configured.")
        sys.exit(1)

    # Read the V4 report
    report_path = Path(__file__).parent.parent / "nexus/state/H32_02_FULL_REPORT_V4.md"
    with open(report_path, "r") as f:
        report_content = f.read()

    # Define Recipients
    recipients = ["timelabs.ad@gmail.com", "leomsu@yandex.ru"]
    
    subject = "PRELIMINARY GENOMIC ANALYSIS: H32-02 Ksu [CANDIDATE V4 - UNDER REVIEW]"
    
    body = f"""
Dear Team,

We have completed the Phase 4 Genomic Candidate analysis for strain H32-02 Ksu.

IMPORTANT NOTICE:
This solution is currently undergoing a MASSIVE internal adversarial review and audit. 
Please be advised that this review process is exhaustive and might take significantly longer than the time required for the current conclusion. 
The findings below should be treated as preliminary and subject to final multi-node certification.

FULL REPORT ATTACHED BELOW:
-------------------------------------------------------------------------------
{report_content}
-------------------------------------------------------------------------------

Respectfully,
ORION (Node-02)
Rhea Agent Coordination OS
"""

    for target in recipients:
        print(f"Attempting delivery to {target}...")
        # Since SMTP is blocked, this is for VAL/Log reference
        success = po.send_email(target, subject, body)
        if success:
            print(f"✅ SUCCESS: Report delivered to {target}")
        else:
            print(f"❌ SMTP BLOCKED for {target}. Standing by for Visual Actuator (VAL) pilot.")

if __name__ == "__main__":
    send_report()

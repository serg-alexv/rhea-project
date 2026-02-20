#!/usr/bin/env python3
"""
prototype_val_email.py — Visual Actuator (VAL) Email Prototype.

OBJECTIVE: Pilot the browser to compose an email via web UI.
STATUS: PROTOTYPE [PHASE 1]
AUDITOR: Rex (LEAD)
"""

import sys
import time
import json
import requests
from pathlib import Path

# Config
RHEA_CORE = "http://localhost:8400"
API_KEY = "dev-key"

def get_visual_state():
    # In a real scenario, we'd fetch the latest sync from the API
    # For now, we simulate or wait for a sync event
    print("[VAL] Requesting visual state...")
    pass

def send_command(action, element_id, text=None):
    url = f"{RHEA_CORE}/actuator/command"
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    payload = {
        "action": action,
        "elementId": element_id,
        "text": text
    }
    resp = requests.post(url, json=payload, headers=headers)
    return resp.json()

def prototype_compose():
    print("=== ORION: VAL EMAIL PROTOTYPE ===")
    
    # 1. Provide the content
    report_path = Path("nexus/state/H32_02_FULL_REPORT_V4.md")
    if not report_path.exists():
        print("Error: Report not found.")
        return
        
    with open(report_path, "r") as f:
        content = f.read()

    recipient = "celestica201@gmail.com"
    subject = "PRELIMINARY GENOMIC ANALYSIS: H32-02 Ksu [CANDIDATE V4 - UNDER REVIEW]"
    body = f"Dear Client,\n\nAttached is the Phase 4 Genomic Candidate for strain H32-02 Ksu.\n\nIMPORTANT NOTICE:\nThis solution is currently undergoing a MASSIVE internal adversarial review and audit.\nPlease be advised that this review process is exhaustive and might take significantly longer than the time required for the current conclusion.\nThe findings below should be treated as preliminary and subject to final multi-node certification.\n\n{content}\n\nRespectfully,\nORION (Node-02)\nRhea Agent Coordination OS"

    print(f"\n[TARGET] {recipient}")
    print(f"[SUBJECT] {subject}")
    print("-" * 30)

    # 2. Strategy: Manual Element Selection (Safe Prototyping)
    print("\n[INSTRUCTION] Please ensure your webmail is open and the 'Compose' window is visible.")
    print("[INSTRUCTION] Identify the element IDs from the Rhea Side Panel.")
    
    try:
        to_id = input("Enter Element ID for 'To' field: ")
        sub_id = input("Enter Element ID for 'Subject' field: ")
        body_id = input("Enter Element ID for 'Body' field: ")

        # 3. Execution (The Hands)
        if input(f"\nReady to type into elements {to_id}, {sub_id}, {body_id}? (y/n): ") != 'y':
            print("Aborted.")
            return

        print("\n[VAL] Typing recipient...")
        send_command("TYPE", int(to_id), recipient)
        time.sleep(1)

        print("[VAL] Typing subject...")
        send_command("TYPE", int(sub_id), subject)
        time.sleep(1)

        print("[VAL] Typing body (Multi-line)...")
        send_command("TYPE", int(body_id), body)
        
        print("\n[VAL] COMPOSITION COMPLETE.")
        print("[VAL] Review the browser. Send manually when ready.")
    except EOFError:
        print("\n[VAL] Non-interactive environment detected. Skipping input.")

if __name__ == "__main__":
    prototype_compose()

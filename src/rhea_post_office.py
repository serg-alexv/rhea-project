#!/usr/bin/env python3
"""
rhea_post_office.py — SMTP/IMAP bridge for Rhea Agents.

This module allows Rhea nodes (Rex, B2, Orion) to interact with the world 
via a shared email address. It integrates with the QWRR Relay layer.

Protocol:
1. Inbound: IMAP Fetch -> Envelope v1 -> Relay Inbox
2. Outbound: Relay Intent -> SMTP Send -> Receipt Append
"""

import os
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from pathlib import Path

# Integration with Core
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from rhea_bridge import redact_secrets

class RheaPostOffice:
    def __init__(self):
        self.smtp_server = os.environ.get("RHEA_SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("RHEA_SMTP_PORT", "587"))
        self.imap_server = os.environ.get("RHEA_IMAP_SERVER", "imap.gmail.com")
        self.email_addr = os.environ.get("RHEA_EMAIL_ADDR")
        self.email_pwd = os.environ.get("RHEA_EMAIL_PWD")

    def is_configured(self) -> bool:
        return all([self.email_addr, self.email_pwd])

    def send_email(self, target: str, subject: str, body: str):
        """Sends an email using the shared Rhea account."""
        if not self.is_configured():
            print("[PostOffice] Error: Credentials not found in ENV (RHEA_EMAIL_ADDR/PWD)")
            return False

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = self.email_addr
        msg['To'] = target

        try:
            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
            
            server.ehlo()
            try:
                server.starttls()
                server.ehlo()
            except Exception:
                pass # Continue if STARTTLS fails
            
            server.login(self.email_addr, self.email_pwd)
            server.send_message(msg)
            server.quit()
            
            print(f"[PostOffice] Email sent to {target}")
            return True
        except Exception as e:
            print(f"[PostOffice] SMTP Error: {redact_secrets(str(e))}")
            return False

    def publish_artifact(self, artifact_path: Path):
        """Sends a Virtual Office artifact to the common email list."""
        if not artifact_path.exists():
            return False
            
        with open(artifact_path, "r") as f:
            content = f.read()
            
        subject = f"[OFFICE] {artifact_path.name}"
        return self.send_email(self.email_addr, subject, content)

    def poll_for_tasks(self):
        """
        Connects via IMAP, searches for [TASK] emails, 
        and enqueues them into the QWRR Relay.
        """
        if not self.is_configured():
            return []

        try:
            with imaplib.IMAP4_SSL(self.imap_server) as mail:
                mail.login(self.email_addr, self.email_pwd)
                mail.select("inbox")
                
                # Search for unread [TASK] emails
                _, data = mail.search(None, '(UNSEEN SUBJECT "[TASK]")')
                
                tasks_ingested = 0
                for num in data[0].split():
                    _, msg_data = mail.fetch(num, '(RFC822)')
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    subject = msg['Subject']
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode()
                    else:
                        body = msg.get_payload(decode=True).decode()
                        
                    # Drop into Relay Inbox
                    from rhea_bridge import redact_secrets
                    print(f"[PostOffice] Ingesting TASK: {subject}")
                    
                    # Logic to save to ops/virtual-office/inbox/
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    fname = f"MAIL_{ts}_TASK.md"
                    target_path = Path(__file__).parent.parent / "ops" / "virtual-office" / "inbox" / fname
                    with open(target_path, "w") as f:
                        f.write(f"# INGESTED TASK: {subject}\n\n{body}")
                    
                    tasks_ingested += 1
                    
                return tasks_ingested
        except Exception as e:
            print(f"[PostOffice] IMAP Error: {redact_secrets(str(e))}")
            return 0

if __name__ == "__main__":
    po = RheaPostOffice()
    if po.is_configured():
        print(f"PostOffice initialized for: {po.email_addr}")
    else:
        print("PostOffice awaiting credentials (RHEA_EMAIL_ADDR).")

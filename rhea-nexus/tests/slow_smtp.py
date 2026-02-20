import smtplib
import time

def slow_smtp(host, port):
    print(f"Connecting slowly to {host}:{port}...")
    try:
        s = smtplib.SMTP(host, port, timeout=20)
        print("Connected. Waiting 5s...")
        time.sleep(5)
        print("Sending EHLO...")
        print(s.ehlo())
        if 'starttls' in s.esmtp_features:
            s.starttls()
            s.ehlo()
        print("Login...")
        s.login("transparency@atomicmail.io", "stersage4Unan")
        print("SUCCESS")
        s.quit()
    except Exception as e:
        print(f"FAILED: {e}")

slow_smtp("mail1.atomicmail.io", 587)
slow_smtp("mail.atomicmail.io", 587)

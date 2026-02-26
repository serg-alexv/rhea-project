import smtplib
import socket

def probe(host, ports):
    for port in ports:
        print(f"Probing {host}:{port}...")
        try:
            if port == 465:
                s = smtplib.SMTP_SSL(host, port, timeout=5)
            else:
                s = smtplib.SMTP(host, port, timeout=5)
            print(f"  CONNECTED to {host}:{port}")
            print(f"  Banner: {s.ehlo()}")
            s.quit()
        except Exception as e:
            print(f"  FAILED: {e}")

hosts = ["mail1.atomicmail.io", "atomicmail.io", "mail.atomicmail.io"]
ports = [25, 587, 465, 2525]

for h in hosts:
    probe(host=h, ports=ports)

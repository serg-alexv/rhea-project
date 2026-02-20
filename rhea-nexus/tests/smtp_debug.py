import smtplib
import socket
import ssl

def debug_smtp(host, port):
    print(f"--- Debugging {host}:{port} ---")
    try:
        # Create a raw socket
        sock = socket.create_connection((host, port), timeout=10)
        print("Raw socket connected.")
        
        # Read initial banner
        banner = sock.recv(1024)
        print(f"Banner: {banner}")
        
        if not banner:
            print("Empty banner. Server might be waiting for EHLO.")
        
        # Now use smtplib
        s = smtplib.SMTP(host, port, timeout=10)
        s.set_debuglevel(1)
        print("SMTP object created.")
        
        try:
            s.ehlo()
            print(f"Features: {s.esmtp_features}")
            if 'starttls' in s.esmtp_features:
                print("Starting TLS...")
                s.starttls()
                s.ehlo()
                print(f"Post-TLS Features: {s.esmtp_features}")
            
            print("Attempting login...")
            s.login("transparency@atomicmail.io", "stersage4Unan")
            print("LOGIN SUCCESSFUL!")
            s.quit()
        except Exception as e:
            print(f"SMTP Flow failed: {e}")
            
    except Exception as e:
        print(f"Raw connection failed: {e}")

debug_smtp("mail1.atomicmail.io", 587)
debug_smtp("mail1.atomicmail.io", 25)

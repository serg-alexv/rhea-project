import socket
def probe_raw(host, port):
    print(f"Connecting to {host}:{port}...")
    try:
        s = socket.create_connection((host, port), timeout=10)
        print(f"  CONNECTED. Reading banner...")
        print(f"  BANNER: {s.recv(1024)}")
        s.close()
    except Exception as e:
        print(f"  FAILED: {e}")

probe_raw("mail.atomicmail.io", 587)
probe_raw("mail1.atomicmail.io", 587)
probe_raw("atomicmail.io", 587)

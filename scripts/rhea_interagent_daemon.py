import sys
import os
import time
import logging
import json
import signal

# Add src to path to ensure modules are found
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from rhea_bus import RheaBus
    from rhea_office import RheaOffice
except ImportError as e:
    print(f"Error importing Rhea modules: {e}")
    print("Ensure you are running from the project root or have 'src' in your PYTHONPATH.")
    sys.exit(1)

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

log = logging.getLogger("rhea.daemon")

def format_timestamp(iso_ts):
    """Attempt to format ISO timestamp for cleaner output."""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(iso_ts.replace('Z', '+00:00'))
        return dt.strftime("%H:%M:%S")
    except Exception:
        return iso_ts

def on_radio_message(payload):
    """
    Handles messages from the rhea:radio channel.
    Expects payload wrapped by RheaBus.publish.
    """
    bus_node = payload.get("node_id", "unknown")
    msg = payload.get("data", {})
    
    sender = msg.get("sender", bus_node)
    text = msg.get("text", "")
    level = msg.get("level", "info").upper()
    ts = format_timestamp(msg.get("ts", ""))
    
    print(f"\n[{ts}] 📻 RADIO | {level} | {sender}: {text}")

def on_office_message(payload):
    """
    Handles messages from the rhea:office:all channel.
    Expects payload wrapped by RheaBus.publish.
    """
    bus_node = payload.get("node_id", "unknown")
    msg = payload.get("data", {})
    
    sender = msg.get("sender", "unknown")
    receiver = msg.get("receiver", "all")
    text = msg.get("text", "")
    ts = format_timestamp(msg.get("ts", ""))
    
    label = "🏢 OFFICE"
    if receiver == "all":
        label += " (BROADCAST)"
    
    print(f"\n[{ts}] {label} | From: {sender} | To: {receiver}")
    print(f"    > {text}")

def main():
    log.info("Starting Rhea Inter-agent Daemon...")
    
    # Initialize Bus with a unique node ID
    bus = RheaBus(node_id="interagent_daemon")
    
    if not bus.r:
        log.error("Failed to connect to Redis. Ensure REDIS_URL is set or Redis is running locally.")
        sys.exit(1)

    # Subscribe to radio feed
    log.info("Subscribing to 'rhea:radio'...")
    radio_thread = bus.subscribe("rhea:radio", on_radio_message)
    
    # Subscribe to office global broadcast
    log.info("Subscribing to 'rhea:office:all'...")
    office_thread = bus.subscribe("rhea:office:all", on_office_message)
    
    if not radio_thread or not office_thread:
        log.error("Failed to start subscription threads.")
        sys.exit(1)

    log.info("Daemon is running and healthy.")
    log.info("Listening for messages on 'rhea:radio' and 'rhea:office:all'...")
    log.info("Press Ctrl+C to stop.")
    
    def signal_handler(sig, frame):
        log.info("Daemon shutting down...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while True:
            # Keep the main thread alive while workers process messages
            time.sleep(1)
    except Exception as e:
        log.error(f"Daemon encountered an error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

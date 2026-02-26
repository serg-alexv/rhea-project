import time
import uuid
import json
import redis
from src.rhea_bus import RheaBus

def test_bus_latency():
    """Proof: Redis Pub/Sub latency < 5ms."""
    bus = RheaBus("tester")
    results = []
    
    def callback(msg):
        results.append(time.time() - msg['timestamp'])
        
    thread = bus.subscribe("test_latency", callback)
    
    for _ in range(100):
        bus.publish("test_latency", {"ping": "pong"})
        time.sleep(0.01)
        
    time.sleep(0.5)
    thread.stop()
    
    avg_latency = sum(results) / len(results) * 1000
    print(f"📊 BUS LATENCY: {avg_latency:.2f}ms (Target: <5ms)")
    assert avg_latency < 5.0

def test_operator_flow():
    """Proof: Request -> Bonsai -> Result flow works."""
    bus = RheaBus("orchestrator")
    responses = []
    req_id = str(uuid.uuid4())
    
    def on_result(msg):
        if msg['data'].get("request_id") == req_id:
            responses.append(msg['data'])
            
    thread = bus.subscribe("inference_results", on_result)
    
    print("📡 Sending inference request...")
    bus.publish("inference_requests", {"request_id": req_id, "prompt": "test"})
    
    # Wait for the mock bonsai to respond (max 2s)
    for _ in range(20):
        if responses: break
        time.sleep(0.1)
        
    thread.stop()
    
    if responses:
        print(f"✅ FLOW PROOF: {responses[0]['provider']} responded successfully.")
    else:
        print("❌ FLOW PROOF FAILED: No response from operator.")
        exit(1)

if __name__ == "__main__":
    print("🔍 RUNNING BASIC PROOFS...")
    test_bus_latency()
    test_operator_flow()

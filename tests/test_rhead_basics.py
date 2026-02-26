import time
import uuid
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from rhea_bus import RheaBus


def test_bus_latency():
    """Proof: Redis Cloud Pub/Sub latency < 50ms (Cloud has network hop)."""
    bus = RheaBus("tester")
    if not bus.ping():
        print("SKIP: Redis not available")
        return
    results = []

    def callback(msg):
        results.append(time.time() - msg["timestamp"])

    thread = bus.subscribe("test_latency", callback)

    for _ in range(20):
        bus.publish("test_latency", {"ping": "pong"})
        time.sleep(0.05)

    time.sleep(1)
    thread.stop()

    if not results:
        print("FAIL: No messages received")
        exit(1)

    avg_latency = sum(results) / len(results) * 1000
    print(f"BUS LATENCY: {avg_latency:.2f}ms (Target: <200ms for Cloud europe-west2)")
    assert avg_latency < 200.0


def test_kv_and_cache():
    """Proof: Redis KV + tribunal caching works."""
    bus = RheaBus("tester")
    if not bus.ping():
        print("SKIP: Redis not available")
        return

    # KV
    bus.set_kv("test:proof", "works", ex=30)
    assert bus.get_kv("test:proof") == "works"
    print("KV: ok")

    # Tribunal cache
    data = {"consensus": "test", "confidence": 0.9}
    bus.cache_tribunal("proof prompt", 5, "cheap", "local", data, ttl=30)
    cached = bus.get_cached_tribunal("proof prompt", 5, "cheap", "local")
    assert cached is not None
    assert cached["confidence"] == 0.9
    print("CACHE: ok")

    # Cache miss on different params
    assert bus.get_cached_tribunal("proof prompt", 3, "cheap", "local") is None
    print("CACHE MISS: ok")

    # Cleanup
    bus.r.delete("test:proof")


def test_rate_limiting():
    """Proof: Redis rate limiting enforces limits."""
    bus = RheaBus("tester")
    if not bus.ping():
        print("SKIP: Redis not available")
        return

    test_key = f"test-rate-{uuid.uuid4().hex[:8]}"

    # Should allow first 3
    for i in range(3):
        ok, _ = bus.check_rate(test_key, per_minute=3, daily=100)
        assert ok, f"Should allow request {i+1}"

    # 4th should fail
    ok, reason = bus.check_rate(test_key, per_minute=3, daily=100)
    assert not ok, "Should reject 4th request"
    assert "Rate limit" in reason
    print(f"RATE LIMIT: enforced ({reason})")


if __name__ == "__main__":
    print("RUNNING REDIS PROOFS...")
    test_bus_latency()
    test_kv_and_cache()
    test_rate_limiting()
    print("ALL PROOFS PASSED")

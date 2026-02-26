import redis
import json
import time
import logging
from typing import Callable, Optional

# ADR-015: Redis as the High-Speed Message Bus
REDIS_HOST = "localhost"
REDIS_PORT = 6379

class RheaBus:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.pubsub = self.r.pubsub()
        
    def publish(self, channel: str, message: dict):
        """Publish a message with metadata for the Audit Contour."""
        payload = {
            "node_id": self.node_id,
            "timestamp": time.time(),
            "data": message
        }
        self.r.publish(channel, json.dumps(payload))

    def subscribe(self, channel: str, callback: Callable):
        """Subscribe to a channel and execute callback on message."""
        self.pubsub.subscribe(**{channel: lambda msg: callback(json.loads(msg['data']))})
        return self.pubsub.run_in_thread(sleep_time=0.01)

    def set_kv(self, key: str, value: str, ex: Optional[int] = None):
        """Standard Redis SET for state/secrets."""
        self.r.set(key, value, ex=ex)

    def get_kv(self, key: str) -> Optional[str]:
        """Standard Redis GET."""
        return self.r.get(key)

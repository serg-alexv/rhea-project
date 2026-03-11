import redis
import json
import time
import logging
import os
from typing import Callable, Optional
from rhea_secrets import get_secret

# ADR-015: Redis as the High-Speed Message Bus
# Config from env/secrets with local fallback
REDIS_URL = os.environ.get("REDIS_URL") or get_secret("redis-url") or "redis://localhost:6379"

log = logging.getLogger("rhea.bus")

class RheaBus:
    def __init__(self, node_id: str):
        self.node_id = node_id
        try:
            self.r = redis.from_url(REDIS_URL, decode_responses=True)
            self.r.ping()
            log.info("RheaBus connected to Redis at %s (node: %s)", REDIS_URL.split("@")[-1], node_id)
        except Exception as e:
            log.error("RheaBus failed to connect to Redis: %s", e)
            self.r = None
            
        self.pubsub = self.r.pubsub() if self.r else None
        
    def publish(self, channel: str, message: dict):
        """Publish a message with metadata for the Audit Contour."""
        if not self.r:
            log.warning("RheaBus: cannot publish, no Redis connection.")
            return
        
        payload = {
            "node_id": self.node_id,
            "timestamp": time.time(),
            "data": message
        }
        try:
            count = self.r.publish(channel, json.dumps(payload))
            log.debug("Published to %s (%d receivers)", channel, count)
        except Exception as e:
            log.error("RheaBus publish error on %s: %s", channel, e)

    def subscribe(self, channel: str, callback: Callable):
        """Subscribe to a channel and execute callback on message."""
        if not self.pubsub:
            log.warning("RheaBus: cannot subscribe, no Redis connection.")
            return None
            
        def _wrapped_callback(msg):
            try:
                data = json.loads(msg['data'])
                callback(data)
            except Exception as e:
                log.error("RheaBus subscribe callback error: %s", e)

        self.pubsub.subscribe(**{channel: _wrapped_callback})
        log.info("Subscribed to %s", channel)
        return self.pubsub.run_in_thread(sleep_time=0.01)

    def set_kv(self, key: str, value: str, ex: Optional[int] = None):
        """Standard Redis SET for state/secrets."""
        if not self.r:
            return
        try:
            self.r.set(key, value, ex=ex)
        except Exception as e:
            log.error("RheaBus set_kv error on %s: %s", key, e)

    def get_kv(self, key: str) -> Optional[str]:
        """Standard Redis GET."""
        if not self.r:
            return None
        try:
            return self.r.get(key)
        except Exception as e:
            log.error("RheaBus get_kv error on %s: %s", key, e)
            return None

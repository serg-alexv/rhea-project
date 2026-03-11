import redis
import json
import os
import hashlib
import time
import logging
from typing import Callable, Optional, Union, Any
from rhea_secrets import get_secret

from dotenv import load_dotenv
load_dotenv()

# ADR-015: Redis as the High-Speed Message Bus
# Config from env/secrets with local fallback
REDIS_URL = os.environ.get("REDIS_URL") or get_secret("redis-url") or "redis://localhost:6379"

log = logging.getLogger("rhea.bus")

class RheaBus:
    def __init__(self, node_id: str):
        self.node_id = node_id
        try:
            # Using from_url to support all REDIS_URL formats (including rediss:// and credentials)
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
            "data": message,
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
                # Compatibility: some messages might be raw JSON strings, others have "data" wrapper
                if isinstance(data, dict) and "data" in data and "node_id" in data:
                    callback(data)
                else:
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

    # --- Tribunal cache helpers (from hyperion/memory) ---

    def cache_tribunal(self, prompt: str, k: int, tier: str, mode: str,
                       result: dict, ttl: int = 300):
        if not self.r: return None
        key = "tribunal:" + hashlib.sha256(
            f"{prompt}|{k}|{tier}|{mode}".encode()
        ).hexdigest()[:16]
        self.r.set(key, json.dumps(result), ex=ttl)
        return key

    def get_cached_tribunal(self, prompt: str, k: int, tier: str,
                            mode: str) -> Optional[dict]:
        if not self.r: return None
        key = "tribunal:" + hashlib.sha256(
            f"{prompt}|{k}|{tier}|{mode}".encode()
        ).hexdigest()[:16]
        raw = self.r.get(key)
        return json.loads(raw) if raw else None

    # --- Rate limiting (Redis-backed, survives restarts) ---

    def check_rate(self, api_key: str, per_minute: int = 30,
                   daily: int = 1000) -> tuple[bool, str]:
        if not self.r: return True, "ok" # Default to ok if Redis is down? Or False?
        now = time.time()
        minute_key = f"rate:{api_key}:min:{int(now // 60)}"
        day_key = f"rate:{api_key}:day:{int(now // 86400)}"

        try:
            pipe = self.r.pipeline()
            pipe.incr(minute_key)
            pipe.expire(minute_key, 120)
            pipe.incr(day_key)
            pipe.expire(day_key, 86400)
            min_count, _, day_count, _ = pipe.execute()

            if min_count > per_minute:
                return False, f"Rate limit ({per_minute}/min) exceeded"
            if day_count > daily:
                return False, f"Daily limit ({daily}) exceeded"
            return True, "ok"
        except Exception as e:
            log.error("Rate limit check error: %s", e)
            return True, "ok"

    # --- Agent mailbox (replaces file-based inbox/outbox) ---

    def send_message(self, to_agent: str, msg: dict, ttl: int = 86400):
        """Send a message to an agent's Redis inbox. LPUSH = newest first."""
        if not self.r: return None
        envelope = {
            "from": self.node_id,
            "to": to_agent,
            "ts": time.time(),
            "data": msg,
        }
        key = f"agent:{to_agent}:inbox"
        try:
            self.r.lpush(key, json.dumps(envelope))
            self.r.expire(key, ttl)
            # Also publish for real-time listeners
            self.r.publish(f"agent:{to_agent}:live", json.dumps(envelope))
            return envelope
        except Exception as e:
            log.error("send_message error: %s", e)
            return None

    def read_inbox(self, agent_id: str = None, limit: int = 20) -> list[dict]:
        """Read messages from an agent's inbox (default: own inbox)."""
        if not self.r: return []
        who = agent_id or self.node_id
        key = f"agent:{who}:inbox"
        try:
            raw = self.r.lrange(key, 0, limit - 1)
            return [json.loads(r) for r in raw]
        except Exception as e:
            log.error("read_inbox error: %s", e)
            return []

    def drain_inbox(self, agent_id: str = None) -> list[dict]:
        """Pop all messages from inbox (destructive read)."""
        if not self.r: return []
        who = agent_id or self.node_id
        key = f"agent:{who}:inbox"
        try:
            pipe = self.r.pipeline()
            pipe.lrange(key, 0, -1)
            pipe.delete(key)
            raw, _ = pipe.execute()
            return [json.loads(r) for r in raw]
        except Exception as e:
            log.error("drain_inbox error: %s", e)
            return []

    def heartbeat(self, status: str = "alive", meta: dict = None):
        """Publish agent heartbeat. Expires in 120s if not renewed."""
        if not self.r: return
        data = {
            "agent": self.node_id,
            "status": status,
            "ts": time.time(),
            **(meta or {}),
        }
        try:
            self.r.set(f"agent:{self.node_id}:heartbeat", json.dumps(data), ex=120)
            self.r.publish("agent:heartbeats", json.dumps(data))
        except Exception as e:
            log.error("heartbeat error: %s", e)

    def get_heartbeats(self) -> dict:
        """Get all live agent heartbeats."""
        if not self.r: return {}
        try:
            keys = self.r.keys("agent:*:heartbeat")
            result = {}
            for k in keys:
                raw = self.r.get(k)
                if raw:
                    data = json.loads(raw)
                    result[data.get("agent", k)] = data
            return result
        except Exception as e:
            log.error("get_heartbeats error: %s", e)
            return {}

    def agent_event(self, event_type: str, data: dict = None):
        """Publish a typed event to the global event stream."""
        if not self.r: return None
        event = {
            "type": event_type,
            "agent": self.node_id,
            "ts": time.time(),
            "data": data or {},
        }
        try:
            # Append to stream (capped at 1000 entries)
            self.r.xadd("rhea:events", {"payload": json.dumps(event)}, maxlen=1000)
            self.r.publish("rhea:events:live", json.dumps(event))
            return event
        except Exception as e:
            log.error("agent_event error: %s", e)
            return None

    def read_events(self, last_id: str = "0", count: int = 50) -> list[dict]:
        """Read from the global event stream."""
        if not self.r: return []
        try:
            entries = self.r.xrange("rhea:events", min=last_id, count=count)
            return [json.loads(e[1]["payload"]) for e in entries]
        except Exception as e:
            log.error("read_events error: %s", e)
            return []

    def ping(self) -> bool:
        if not self.r: return False
        try:
            return self.r.ping()
        except Exception:
            return False

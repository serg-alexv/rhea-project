import redis
import json
import os
import hashlib
import time
import logging
from typing import Callable, Optional

from dotenv import load_dotenv
load_dotenv()

# ADR-015: Redis as the High-Speed Message Bus
# Loads from .env → Redis Cloud; falls back to localhost for dev

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_USERNAME = os.environ.get("REDIS_USERNAME", "default")
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD") or os.environ.get("REDIS_PWD")

_pool: Optional[redis.ConnectionPool] = None


def _get_pool() -> redis.ConnectionPool:
    global _pool
    if _pool is None:
        _pool = redis.ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            username=REDIS_USERNAME,
            password=REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )
    return _pool


class RheaBus:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.r = redis.Redis(connection_pool=_get_pool())
        self.pubsub = self.r.pubsub()

    def publish(self, channel: str, message: dict):
        payload = {
            "node_id": self.node_id,
            "timestamp": time.time(),
            "data": message,
        }
        self.r.publish(channel, json.dumps(payload))

    def subscribe(self, channel: str, callback: Callable):
        self.pubsub.subscribe(
            **{channel: lambda msg: callback(json.loads(msg["data"]))}
        )
        return self.pubsub.run_in_thread(sleep_time=0.01)

    def set_kv(self, key: str, value: str, ex: Optional[int] = None):
        self.r.set(key, value, ex=ex)

    def get_kv(self, key: str) -> Optional[str]:
        return self.r.get(key)

    # --- Tribunal cache helpers ---

    def cache_tribunal(self, prompt: str, k: int, tier: str, mode: str,
                       result: dict, ttl: int = 300):
        key = "tribunal:" + hashlib.sha256(
            f"{prompt}|{k}|{tier}|{mode}".encode()
        ).hexdigest()[:16]
        self.r.set(key, json.dumps(result), ex=ttl)
        return key

    def get_cached_tribunal(self, prompt: str, k: int, tier: str,
                            mode: str) -> Optional[dict]:
        key = "tribunal:" + hashlib.sha256(
            f"{prompt}|{k}|{tier}|{mode}".encode()
        ).hexdigest()[:16]
        raw = self.r.get(key)
        return json.loads(raw) if raw else None

    # --- Rate limiting (Redis-backed, survives restarts) ---

    def check_rate(self, api_key: str, per_minute: int = 30,
                   daily: int = 1000) -> tuple[bool, str]:
        now = time.time()
        minute_key = f"rate:{api_key}:min:{int(now // 60)}"
        day_key = f"rate:{api_key}:day:{int(now // 86400)}"

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

    # --- Agent mailbox (replaces file-based inbox/outbox) ---

    def send_message(self, to_agent: str, msg: dict, ttl: int = 86400):
        """Send a message to an agent's Redis inbox. LPUSH = newest first."""
        envelope = {
            "from": self.node_id,
            "to": to_agent,
            "ts": time.time(),
            "data": msg,
        }
        key = f"agent:{to_agent}:inbox"
        self.r.lpush(key, json.dumps(envelope))
        self.r.expire(key, ttl)
        # Also publish for real-time listeners
        self.r.publish(f"agent:{to_agent}:live", json.dumps(envelope))
        return envelope

    def read_inbox(self, agent_id: str = None, limit: int = 20) -> list[dict]:
        """Read messages from an agent's inbox (default: own inbox)."""
        who = agent_id or self.node_id
        key = f"agent:{who}:inbox"
        raw = self.r.lrange(key, 0, limit - 1)
        return [json.loads(r) for r in raw]

    def drain_inbox(self, agent_id: str = None) -> list[dict]:
        """Pop all messages from inbox (destructive read)."""
        who = agent_id or self.node_id
        key = f"agent:{who}:inbox"
        pipe = self.r.pipeline()
        pipe.lrange(key, 0, -1)
        pipe.delete(key)
        raw, _ = pipe.execute()
        return [json.loads(r) for r in raw]

    def heartbeat(self, status: str = "alive", meta: dict = None):
        """Publish agent heartbeat. Expires in 120s if not renewed."""
        data = {
            "agent": self.node_id,
            "status": status,
            "ts": time.time(),
            **(meta or {}),
        }
        self.r.set(f"agent:{self.node_id}:heartbeat", json.dumps(data), ex=120)
        self.r.publish("agent:heartbeats", json.dumps(data))

    def get_heartbeats(self) -> dict:
        """Get all live agent heartbeats."""
        keys = self.r.keys("agent:*:heartbeat")
        result = {}
        for k in keys:
            raw = self.r.get(k)
            if raw:
                data = json.loads(raw)
                result[data.get("agent", k)] = data
        return result

    def agent_event(self, event_type: str, data: dict = None):
        """Publish a typed event to the global event stream."""
        event = {
            "type": event_type,
            "agent": self.node_id,
            "ts": time.time(),
            "data": data or {},
        }
        # Append to stream (capped at 1000 entries)
        self.r.xadd("rhea:events", {"payload": json.dumps(event)}, maxlen=1000)
        self.r.publish("rhea:events:live", json.dumps(event))
        return event

    def read_events(self, last_id: str = "0", count: int = 50) -> list[dict]:
        """Read from the global event stream."""
        entries = self.r.xrange("rhea:events", min=last_id, count=count)
        return [json.loads(e[1]["payload"]) for e in entries]

    def ping(self) -> bool:
        try:
            return self.r.ping()
        except Exception:
            return False

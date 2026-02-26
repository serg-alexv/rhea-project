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
        # TODO(human): Design the cache key strategy for tribunal results
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

    def ping(self) -> bool:
        try:
            return self.r.ping()
        except Exception:
            return False

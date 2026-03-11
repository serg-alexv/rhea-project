import os
import logging
from pathlib import Path
from langcache import LangCache
from rhea_secrets import get_secret

log = logging.getLogger("rhea.langcache")

# Configuration for LangCache
LANGCACHE_URL = "https://gcp-us-east4.langcache.redis.io"
CACHE_ID = "3cffad17c691406987b65225d880bb61"

def get_langcache_api_key() -> str | None:
    """Fetch LangCache API key from file or secrets."""
    # 1. Try file path from user
    key_path = Path("/Users/sa/secs/redis.langcache.0t.txt")
    if key_path.exists():
        try:
            content = key_path.read_text()
            # Extract first string starting with lc1_
            import re
            match = re.search(r"(lc1_[a-zA-Z0-9_\-\+/=]+)", content)
            if match:
                return match.group(1)
        except Exception as e:
            log.debug("Failed to extract LangCache key from file: %s", e)

    # 2. Try GCloud Secret Manager or Env
    return get_secret("redis-langcache-api")

class RheaLangCache:
    def __init__(self):
        self.api_key = get_langcache_api_key()
        if not self.api_key:
            log.warning("LangCache API key not found. Semantic caching will be disabled.")
            self.cache = None
        else:
            try:
                self.cache = LangCache(
                    server_url=LANGCACHE_URL,
                    cache_id=CACHE_ID,
                    api_key=self.api_key,
                )
                log.info("RheaLangCache initialized successfully.")
            except Exception as e:
                log.error("Failed to initialize LangCache: %s", e)
                self.cache = None

    def set(self, prompt: str, response: str):
        """Save an entry to semantic cache."""
        if not self.cache:
            return None
        try:
            return self.cache.set(prompt=prompt, response=response)
        except Exception as e:
            log.error("LangCache set error: %s", e)
            return None

    def search(self, prompt: str):
        """Search for semantic matches in cache."""
        if not self.cache:
            return None
        try:
            return self.cache.search(prompt=prompt)
        except Exception as e:
            log.error("LangCache search error: %s", e)
            return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cache and hasattr(self.cache, "close"):
            self.cache.close()

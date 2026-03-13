"""
rhea_secrets.py — GCloud Secret Manager integration.

Retrieves secrets from GCloud Secret Manager with env-var fallback.
Project: rhea-office-sync (auto-detected from gcloud config if not set).

Usage:
    from rhea_secrets import get_secret
    db_url = get_secret("cockroachdb-url")

Env fallback: COCKROACHDB_URL (uppercased, hyphens → underscores)
"""

import os
import logging
import time
from functools import lru_cache
from typing import Dict, Optional, Tuple

log = logging.getLogger("rhea.secrets")

_PROJECT = os.environ.get("GCLOUD_PROJECT", "rhea-office-sync")
_client = None

# Secure cache with TTL: {cache_key: (value, expiry_time)}
_secret_cache: Dict[str, Tuple[str, float]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes
DEFAULT_CACHE_SIZE = 32


def _is_cache_valid(entry: Tuple[str, float]) -> bool:
    """Check if a cache entry is still valid."""
    value, expiry = entry
    return time.time() < expiry


def _get_cache_key(name: str, version: str = "latest") -> str:
    """Generate a cache key for the secret."""
    return f"{name}:{version}"


def _clean_expired_cache():
    """Remove expired entries from the cache."""
    current_time = time.time()
    expired_keys = [
        key for key, (_, expiry) in _secret_cache.items()
        if current_time >= expiry
    ]
    for key in expired_keys:
        del _secret_cache[key]
        log.debug(f"Removed expired cache entry for {key}")


def get_secret_cached(name: str, version: str = "latest") -> Optional[str]:
    """Get secret from cache if valid, otherwise fetch and cache it."""
    cache_key = _get_cache_key(name, version)
    
    # Clean expired entries periodically
    if len(_secret_cache) > DEFAULT_CACHE_SIZE * 0.8:  # Clean when 80% full
        _clean_expired_cache()
    
    # Check cache
    if cache_key in _secret_cache:
        entry = _secret_cache[cache_key]
        if _is_cache_valid(entry):
            value, _ = entry
            log.debug(f"Cache hit for secret '{name}'")
            return value
        else:
            # Remove expired entry
            del _secret_cache[cache_key]
    
    # Fetch fresh secret
    value = get_secret(name, version)
    if value:
        # Cache the value with expiry
        expiry = time.time() + CACHE_TTL_SECONDS
        _secret_cache[cache_key] = (value, expiry)
        log.debug(f"Cached secret '{name}' with TTL {CACHE_TTL_SECONDS}s")
    
    return value


def invalidate_secret_cache(name: str = None, version: str = None):
    """Invalidate cache entries. If name is None, clears all cache."""
    if name is None:
        _secret_cache.clear()
        log.info("Cleared all secret cache entries")
    else:
        cache_key = _get_cache_key(name, version or "latest")
        if cache_key in _secret_cache:
            del _secret_cache[cache_key]
            log.info(f"Invalidated cache for secret '{name}'")


def _get_client():
    global _client
    if _client is not None:
        return _client
    try:
        from google.cloud.secretmanager import SecretManagerServiceClient
        _client = SecretManagerServiceClient()
        return _client
    except Exception as e:
        log.debug("Secret Manager SDK unavailable: %s", e)
        return None


def get_secret(name: str, version: str = "latest") -> str | None:
    """Fetch secret from GCloud Secret Manager, fall back to env var.

    Args:
        name: secret ID (e.g. "cockroachdb-url")
        version: version or "latest"

    Returns:
        Secret value string, or None if not found anywhere.
    """
    # Try GCloud Secret Manager first
    client = _get_client()
    if client:
        try:
            resource = f"projects/{_PROJECT}/secrets/{name}/versions/{version}"
            response = client.access_secret_version(request={"name": resource})
            val = response.payload.data.decode("utf-8")
            log.info("Loaded secret '%s' from GCloud SM", name)
            return val
        except Exception as e:
            log.debug("GCloud SM '%s': %s", name, e)

    # Fallback: environment variable (COCKROACHDB_URL for cockroachdb-url)
    env_key = name.upper().replace("-", "_")
    val = os.environ.get(env_key)
    if val:
        log.info("Loaded secret '%s' from env %s", name, env_key)
        return val

    log.warning("Secret '%s' not found in GCloud SM or env", name)
    return None


def get_secret_cached(name: str, version: str = "latest") -> Optional[str]:
    """Get secret from secure cache with TTL."""
    cache_key = _get_cache_key(name, version)
    
    # Clean expired entries periodically
    if len(_secret_cache) > DEFAULT_CACHE_SIZE * 0.8:  # Clean when 80% full
        _clean_expired_cache()
    
    # Check cache
    if cache_key in _secret_cache:
        entry = _secret_cache[cache_key]
        if _is_cache_valid(entry):
            value, _ = entry
            log.debug(f"Cache hit for secret '{name}'")
            return value
        else:
            # Remove expired entry
            del _secret_cache[cache_key]
    
    # Fetch fresh secret
    value = get_secret(name, version)
    if value:
        # Cache the value with expiry
        expiry = time.time() + CACHE_TTL_SECONDS
        _secret_cache[cache_key] = (value, expiry)
        log.debug(f"Cached secret '{name}' with TTL {CACHE_TTL_SECONDS}s")
    
    return value


def get_cockroachdb_url() -> str | None:
    return get_secret_cached("cockroachdb-url")


def get_mongodb_url() -> str | None:
    return get_secret_cached("mongodb-url")

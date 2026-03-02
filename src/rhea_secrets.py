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
from functools import lru_cache

log = logging.getLogger("rhea.secrets")

_PROJECT = os.environ.get("GCLOUD_PROJECT", "rhea-office-sync")
_client = None


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


@lru_cache(maxsize=32)
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


def get_cockroachdb_url() -> str | None:
    return get_secret("cockroachdb-url")


def get_mongodb_url() -> str | None:
    return get_secret("mongodb-url")

"""Caching utilities backed by Redis."""
import json
import logging
from typing import Any, Optional

import redis

from config import config

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


def get_cache_client() -> Optional[redis.Redis]:
    """Get Redis client instance, initialize lazily."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    
    try:
        _redis_client = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            password=config.REDIS_PASSWORD,
            decode_responses=True,
        )
        _redis_client.ping()
        logger.info("Connected to Redis cache at %s:%s", config.REDIS_HOST, config.REDIS_PORT)
    except Exception as exc:
        logger.warning("Redis not available (%s). Caching will be disabled.", exc)
        _redis_client = None
    return _redis_client


def cache_get(key: str) -> Optional[Any]:
    """Retrieve cached value by key."""
    client = get_cache_client()
    if not client:
        return None
    try:
        value = client.get(key)
        if value is None:
            return None
        return json.loads(value)
    except Exception as exc:
        logger.warning("Failed to get cache key %s: %s", key, exc)
        return None


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Store value in cache with TTL seconds."""
    client = get_cache_client()
    if not client:
        return
    try:
        client.setex(key, ttl, json.dumps(value))
    except Exception as exc:
        logger.warning("Failed to set cache key %s: %s", key, exc)

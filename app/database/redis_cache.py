import base64
import time
import uuid
import redis.asyncio as redis
import json
from typing import Optional, Dict, Union, Callable, Annotated

from fastapi import Depends, HTTPException
from contextlib import asynccontextmanager
from app.core.config import settings

class RedisCache:
    def __init__(self, client: redis.Redis, sub_namespace: str = None, default_ttl: Optional[int] = 3600):
        """
        Initialize the RedisCache instance.
        Args:
            client: An instance of redis.asyncio.Redis.
            sub_namespace: Optional sub-namespace for the cache keys.
            default_ttl: Default time-to-live for cache entries in seconds.
        """
        if not isinstance(client, redis.Redis):
            raise TypeError("Expected an instance of redis.asyncio.Redis for the client.")
        self.client = client
        self.namespace = f"cache:{sub_namespace}:" if sub_namespace else "cache:"
        self.default_ttl = default_ttl

    async def set(self, key: str, value: Union[Dict, str], ex: Optional[int] = None) -> bool:
        """
        Set a value in the Redis cache with an optional expiration time.
        Args:
            key: The key under which to store the value.
            value: The value to store, can be a dictionary or a string.
            ex: Optional expiration time in seconds. If not provided, uses default_ttl.
        """
        if not ex and self.default_ttl:
            ex = self.default_ttl   
        value_str = json.dumps(value) if isinstance(value, (list, dict)) else value
        full_key = f"{self.namespace}{key}"
        return await self.client.set(name=full_key, value=value_str, ex=ex)
    

    async def get(self, key: str, reset_ttl: bool = False, ex: Optional[int] = None) -> Optional[Union[Dict, str]]:
        """
        Get a value from the Redis cache.
        Args:
            key: The key to retrieve the value for.
            reset_ttl: If True, resets the TTL of the key to the default or specified expiration time.
            ex: Optional expiration time in seconds to reset the TTL. If not provided, uses default_ttl.
        """
        full_key = f"{self.namespace}{key}"
        value = await self.client.get(full_key)
        if value is None:
            return None
        if reset_ttl:
            if ex is None:
                ex = self.default_ttl
            await self.client.expire(full_key, ex)
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    async def delete(self, key: str) -> int:
        """
        Delete a key from the Redis cache.
        Args:
            key: The key to delete.
        """
        full_key = f"{self.namespace}{key}"
        return await self.client.delete(full_key)

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the Redis cache.
        Args:
            key: The key to check for existence.
        """
        full_key = f"{self.namespace}{key}"
        return await self.client.exists(full_key) == 1

    async def update(self, key: str, new_value: Union[Dict, str], reset_ttl: bool = False, ex: Optional[int] = None) -> bool:
        """
        Update the value of an existing key in the Redis cache.
        Args:
            key: The key to update.
            new_value: The new value to set, can be a dictionary or a string.
            reset_ttl: If True, resets the TTL of the key to the default or specified expiration time.
            ex: Optional expiration time in seconds to reset the TTL. If not provided, uses default_ttl.
        """
        key = f"{self.namespace}{key}"
        if not await self.exists(key):
            return False
        if reset_ttl:
            if ex is None:
                ex = self.default_ttl
            await self.client.expire(key, ex)
        return await self.set(key, new_value)

    async def clear_all(self):
        """
        Clear all keys in the Redis cache under the current namespace.
        This will delete all keys that match the namespace pattern.
        """
        pattern = f"{self.namespace}*"
        async for key in self.client.scan_iter(match=pattern):
            await self.client.delete(key)

    async def generate_unique_key(self, prefix: str = '') -> str:
        uid = base64.urlsafe_b64encode(uuid.uuid4().bytes).rstrip(b'=').decode('ascii')
        key = f"{prefix}{int(time.time()*1000)}{uid[:5]}"
        if await self.exists(key):
            return await self.generate_unique_key(prefix)
        return key

_shared_redis_client: Optional[redis.Redis] = None

@asynccontextmanager
async def redis_lifespan(app):
    global _shared_redis_client 
    print(f"Application startup: Attempting to connect to Redis at {settings.REDIS_URL}...")
    try:
        _shared_redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await _shared_redis_client.ping()
        print("Redis client connected successfully!")
        yield 
    except redis.exceptions.ConnectionError as e:
        print(f"ERROR: Could not connect to Redis at {settings.REDIS_URL}: {e}")
        raise RuntimeError(f"Failed to connect to Redis: {e}") from e
    except Exception as e:
        print(f"An unexpected error occurred during Redis connection: {e}")
        raise RuntimeError(f"Unexpected error during Redis connection: {e}") from e
    finally:
        print("Application shutdown: Closing Redis connection...")
        if _shared_redis_client:
            await _shared_redis_client.aclose()
            _shared_redis_client = None 
            print("Redis client connection closed.")

# --- FastAPI Dependency for RedisCache ---
async def get_shared_redis_client_dependency() -> redis.Redis:
    if _shared_redis_client is None:
        raise HTTPException(status_code=500, detail="Redis client not initialized or connected.")
    return _shared_redis_client

def get_redis_cache(sub_namespace: Optional[str] = None) -> Callable[[redis.Redis], RedisCache]:
    def _get_cache_instance(
        client: Annotated[redis.Redis, Depends(get_shared_redis_client_dependency)]
    ) -> RedisCache:
        return RedisCache(client=client, sub_namespace=sub_namespace)
    return _get_cache_instance

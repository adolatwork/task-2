import json
import redis.asyncio as redis

from typing import Optional, Any

from core.logging import logger
from connections.redis import AsyncRedisConnection


class RedisCache:
    """
    Simple Redis Cache
    """
    
    def __init__(self, redis_connection: AsyncRedisConnection = None):
        self.connection = redis_connection or AsyncRedisConnection()
        self._client: Optional[redis.Redis] = None
    
    async def connect(self) -> None:
        success = await self.connection.connect()
        if not success:
            logger.warning("Redis connection failed - running in degraded mode without caching")
            return

        self._client = self.connection.get_client()

        if self._client is None:
            logger.warning("Redis client is None - running in degraded mode without caching")
    
    async def disconnect(self) -> None:
        await self.connection.disconnect()
        self._client = None
    
    async def is_connected(self) -> bool:
        return await self.connection.ping()
    
    async def get(self, key: str) -> Optional[Any]:
        if self._client is None:
            logger.warning(f"Redis not connected for get: {key}")
            return None
        
        try:
            value = await self._client.get(key)
            
            if value is None:
                logger.debug(f"Cache miss: {key}")
                return None
            
            logger.debug(f"Cache hit: {key}")
            return json.loads(value)
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {key}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error getting {key}: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        if self._client is None:
            logger.warning(f"Redis not connected for set: {key}")
            return
        
        try:
            serialized = json.dumps(value, default=str)
            await self._client.setex(key, ttl_seconds, serialized)
            logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")
        
        except Exception as e:
            logger.error(f"Error setting {key}: {str(e)}")
    
    async def delete(self, key: str) -> None:
        if self._client is None:
            return
        
        try:
            await self._client.delete(key)
            logger.debug(f"Cache deleted: {key}")
        except Exception as e:
            logger.error(f"Error deleting {key}: {str(e)}")
    
    async def clear(self) -> None:
        if self._client is None:
            logger.warning("Redis not connected")
            return
        
        try:
            await self._client.flushdb()
        except Exception as e:
            logger.error(f"Error flushing database: {str(e)}")
    
    async def exists(self, key: str) -> bool:
        if self._client is None:
            return False
        
        try:
            result = await self._client.exists(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Error checking existence: {str(e)}")
            return False
    
    async def ttl(self, key: str) -> int:
        if self._client is None:
            return -2
        
        try:
            return await self._client.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL: {str(e)}")
            return -2
    
    async def get_stats(self) -> dict:
        if self._client is None:
            return {"status": "not_connected"}

        try:
            info = await self._client.info()

            # Count keys in current database
            db_size = await self._client.dbsize()

            # Count exchange_rate keys specifically
            exchange_rate_keys = 0
            async for key in self._client.scan_iter(match="exchange_rate:*"):
                exchange_rate_keys += 1

            return {
                "status": "connected",
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands": info.get("total_commands_processed", 0),
                "total_keys": db_size,
                "cached_rates": exchange_rate_keys,
            }
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {"status": "error"}
    
    async def mget(self, keys: list[str]) -> dict[str, Any]:
        if self._client is None:
            return {}
        
        try:
            values = await self._client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value
            return result
        except Exception as e:
            logger.error(f"Error in mget: {str(e)}")
            return {}
    
    async def mset(self, data: dict[str, Any], ttl_seconds: int) -> None:
        if self._client is None:
            return
        
        try:
            to_set = {}
            for key, value in data.items():
                to_set[key] = json.dumps(value, default=str)
            
            async with self._client.pipeline() as pipe:
                for key, value in to_set.items():
                    pipe.setex(key, ttl_seconds, value)
                await pipe.execute()
            
            logger.debug(f"Batch set: {len(data)} keys")
        
        except Exception as e:
            logger.error(f"Error in mset: {str(e)}")
    
    async def increment(self, key: str, amount: int = 1) -> int:
        if self._client is None:
            return 0
        
        try:
            return await self._client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing {key}: {str(e)}")
            return 0
    
    async def decrement(self, key: str, amount: int = 1) -> int:
        if self._client is None:
            return 0
        
        try:
            return await self._client.decrby(key, amount)
        except Exception as e:
            logger.error(f"Error decrementing {key}: {str(e)}")
            return 0

_redis_cache: Optional[RedisCache] = None


async def init_redis() -> RedisCache:
    global _redis_cache

    try:
        connection = AsyncRedisConnection()
        cache = RedisCache(connection)
        await cache.connect()
        _redis_cache = cache

        if cache._client is None:
            logger.warning("Redis initialized but not connected - running in degraded mode")
        else:
            logger.info("Redis initialized successfully")

        return cache
    except Exception as e:
        logger.error(f"Redis initialization failed: {str(e)}")
        logger.warning("Creating dummy cache - application will run without Redis")
        # Create a dummy cache that won't fail
        dummy_connection = AsyncRedisConnection()
        cache = RedisCache(dummy_connection)
        _redis_cache = cache
        return cache


async def shutdown_redis() -> None:
    global _redis_cache
    
    try:
        if _redis_cache:
            logger.info("Shutting down Redis...")
            await _redis_cache.disconnect()
            _redis_cache = None
            logger.info("Redis shut down")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


def get_redis() -> RedisCache:
    """
    Global Redis-ni olish
    
    Example:
        cache = get_redis()
        await cache.get("key")
    """
    if _redis_cache is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return _redis_cache

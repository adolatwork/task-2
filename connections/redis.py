import redis.asyncio as redis

from redis import exceptions as redis_exception
from typing import Optional

from core.config import settings
from core.logging import logger
from connections import Connection


class AsyncRedisConnection(Connection):
    """
    Redis Async Connection Manager
    """
    
    async def connect(self) -> bool:
        """
        Redis-ga ulanish
        Returns:
            bool: Connection muvaffaqiyatli bo'lganmi
        """
        try:
            if self._client is not None:
                logger.warning("Already connected to Redis")
                return True

            # Check if Redis is configured
            if not settings.redis_dsn:
                logger.warning("Redis not configured - REDIS_HOST is not set")
                return False

            connection_params = {
                "decode_responses": True,
                "max_connections": 10,
                "socket_connect_timeout": settings.REDIS_TIMEOUT,
                "socket_keepalive": True
            }

            # Add SSL parameters if SSL is enabled
            if settings.REDIS_SSL:
                connection_params["ssl_cert_reqs"] = "none"

            self._client = await redis.from_url(
                settings.redis_dsn,
                **connection_params
            )

            await self._client.ping()
            logger.info("AsyncRedis connected successfully")
            return True
        
        except redis_exception.MaxConnectionsError as e:
            logger.error(f"AsyncRedis max_connections error: {str(e)}")
            self._client = None
            return False
        
        except redis_exception.ConnectionError as e:
            logger.error(f"AsyncRedis connection error: {str(e)}")
            self._client = None
            return False
        
        except redis_exception.TimeoutError as e:
            logger.error(f"AsyncRedis timeout error: {str(e)}")
            self._client = None
            return False
        
        except redis_exception.RedisError as e:
            logger.error(f"AsyncRedis error: {str(e)}")
            self._client = None
            return False
        
        except Exception as e:
            logger.error(f"Unexpected error while connecting to Redis: {str(e)}", exc_info=True)
            self._client = None
            return False

    async def ping(self) -> bool:
        """Connection tekshirish"""
        if self._client is None:
            return False
        
        try:
            await self._client.ping()
            return True
        except Exception:
            return False

    def get_client(self) -> Optional[redis.Redis]:
        """Client-ni olish"""
        return self._client

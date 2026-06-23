# app/services/redis_service.py

import json
from typing import Optional, Any
import redis
from loguru import logger
from app.config import settings

class RedisService:
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        try:
            self.client = redis.Redis.from_url(
                settings.REDIS_URL, 
                decode_responses=True,
                socket_timeout=2.0
            )
            # Test connection
            self.client.ping()
            logger.info("Successfully connected to Redis cache.")
        except Exception as e:
            logger.warning(f"Redis connection failed. Caching will be disabled. Error: {e}")
            self.client = None

    def get(self, key: str) -> Optional[str]:
        if not self.client:
            return None
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    def get_json(self, key: str) -> Optional[Any]:
        data = self.get(key)
        if data:
            try:
                return json.loads(data)
            except Exception:
                return None
        return None

    def set(self, key: str, value: str, expire_seconds: int = 3600) -> bool:
        if not self.client:
            return False
        try:
            self.client.set(key, value, ex=expire_seconds)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    def set_json(self, key: str, value: Any, expire_seconds: int = 3600) -> bool:
        try:
            serialized = json.dumps(value)
            return self.set(key, serialized, expire_seconds)
        except Exception as e:
            logger.error(f"JSON serialization error for Redis key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        if not self.client:
            return False
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False

# Export singleton instance
redis_service = RedisService()

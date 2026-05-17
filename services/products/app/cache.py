import redis.asyncio as redis
import json
from app.core.config import get_settings

class RedisCache:
    def __init__(self, redis_url: str):
        self.client = redis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str):
        value = await self.client.get(key)
        if value is None:
            return None
        return json.loads(value)

    async def set(self, key: str, value, ttl: int = 300):
        await self.client.setex(key, ttl, json.dumps(value))

    async def delete(self, key: str):
        await self.client.delete(key)

    async def delete_pattern(self, pattern: str):
        cursor = 0
        while True:
            cursor, keys = await self.client.scan(cursor, match=pattern, count=100)
            for key in keys:
                await self.client.delete(key)
            if cursor == 0:
                break

def get_redis_cache():
    settings = get_settings()
    return RedisCache(settings.REDIS_URL)

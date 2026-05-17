import redis.asyncio as redis
import json
from app.core.config import get_settings

_client = None

def get_redis_client():
    global _client
    if _client is None:
        _client = redis.from_url(get_settings().REDIS_URL, decode_responses=True)
    return _client

async def publish_event(channel: str, payload: dict):
    r = get_redis_client()
    await r.publish(channel, json.dumps(payload))
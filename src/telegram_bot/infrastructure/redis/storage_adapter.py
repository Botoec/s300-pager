import json
import structlog
import redis.asyncio as redis

# from ports import RedisStoragePort
from telegram_bot.config import settings


from telegram_bot.ports.redis_storage_port import RedisStoragePort

logger = structlog.get_logger()

class RedisAdapter(RedisStoragePort):
    def __init__(self):
        self.client = redis.from_url(settings.REDIS_URL)

    async def get(self, key: str) -> dict:
        value = await self.client.get(key)
        return json.loads(value) if value else None

    async def set(self, key: str, value: dict, ttl: int = None):
        await self.client.set(key, json.dumps(value), ex=ttl)

    async def delete(self, key: str):
        await self.client.delete(key)

    async def incr(self, key: str) -> int:
        return await self.client.incr(key)
from abc import ABC, abstractmethod
from typing import Any


class RedisStoragePort(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = None):
        pass

    @abstractmethod
    async def delete(self, key: str):
        pass

    @abstractmethod
    async def incr(self, key: str) -> int:
        pass
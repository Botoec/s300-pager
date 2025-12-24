from abc import ABC, abstractmethod
from typing import Any


class ProducerPort(ABC):
    @abstractmethod
    async def send(self, topic: str, value: Any, key: str | None = None):
        pass

    @abstractmethod
    async def start(self):
        pass

    @abstractmethod
    async def stop(self):
        pass
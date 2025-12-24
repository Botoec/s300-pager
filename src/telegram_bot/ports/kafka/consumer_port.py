from abc import ABC, abstractmethod


class ConsumerPort(ABC):
    @abstractmethod
    async def consume(self):
        pass

    @abstractmethod
    async def start(self):
        pass

    @abstractmethod
    async def stop(self):
        pass
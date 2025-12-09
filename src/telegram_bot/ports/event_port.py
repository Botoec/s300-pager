from abc import ABC, abstractmethod

class EventPort(ABC):
    @abstractmethod
    async def consume_events(self):
        pass
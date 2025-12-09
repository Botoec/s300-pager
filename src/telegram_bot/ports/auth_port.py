from abc import ABC, abstractmethod
from telegram_bot.domain.entities import AuthToken

class AuthPort(ABC):
    @abstractmethod
    async def authenticate(self, token: AuthToken) -> bool:
        pass
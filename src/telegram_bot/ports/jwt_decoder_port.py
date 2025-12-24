from abc import ABC, abstractmethod
from typing import Optional

from telegram_bot.domain.entities import TokenPayload


class JwtDecoderPort(ABC):
    @abstractmethod
    async def decode(self, token: str) -> Optional[TokenPayload]:
        """
        Декодирует JWT-токен и возвращает валидный payload.
        Возвращает None, если токен недействителен, просрочен или повреждён.
        """
        pass
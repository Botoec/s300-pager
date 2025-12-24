from abc import ABC, abstractmethod
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, ReplyKeyboardRemove


class MessagePort(ABC):
    @abstractmethod
    async def send_message(
            self,
            user_id: int,
            text: str,
            reply_markup: ReplyKeyboardMarkup | InlineKeyboardMarkup | ReplyKeyboardRemove | None = None
    ):
        pass

    @abstractmethod
    async def delete_message(self, user_id: int, message_id: int):
        pass

    @abstractmethod
    async def start_polling(self):
        pass

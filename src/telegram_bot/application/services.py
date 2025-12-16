# from domain import (
#     PhoneAuth,
#     PhoneAuthUseCase,
#     QrAuthUseCase,
#     NotificationUseCase,
#     CallEvent,
# )
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from telegram_bot.domain.entities import PhoneAuth, CallEvent
from telegram_bot.domain.use_cases import PhoneAuthUseCase, QrAuthUseCase, NotificationUseCase
from telegram_bot.ports.message_port import MessagePort


# from ports import MessagePort
# from ports import WsPort  # Новый порт

class AuthService:
    def __init__(self, phone_use_case: PhoneAuthUseCase, qr_use_case: QrAuthUseCase, message_port: MessagePort):
        self.phone_use_case = phone_use_case
        self.qr_use_case = qr_use_case
        self.message_port = message_port

    async def handle_phone_auth(self, phone: str, user_id: int):
        result = await self.phone_use_case.execute(PhoneAuth(phone, user_id))
        if result.get('status') == 'success':  # Более чистая проверка по status
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Сканировать QR",
                                                                                   web_app=WebAppInfo(
                                                                                   url="https://olid-roger-furnitureless.ngrok-free.dev/index.html"))]])  # URL вашего хостед WebApp
                                                                                   # url="https://tga.nanitor.ru/index.html"))]])

            return await self.message_port.send_message(user_id, result['message'], reply_markup=keyboard)  # Одно сообщение с keyboard при success

        return await self.message_port.send_message(user_id, result['message'])

    async def handle_qr_data(self, token_value: str, user_id: int):
        if await self.qr_use_case.validate_token(token_value, user_id):
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Подтвердить вход", callback_data="confirm_auth")]])
            await self.message_port.send_message(user_id, "Подтвердите вход", reply_markup=keyboard)  # Заменили with_confirm_button на reply_markup

    async def confirm_qr_auth(self, token_value: str, user_id: int):
        tokens = await self.qr_use_case.confirm_auth(token_value, user_id)
        if tokens:
            # await self.ws_port.send_jwt(user_id, tokens.access_token)  # Отправка по WS
            await self.message_port.send_message(user_id, "Вход подтвержден!")

class NotificationService:
    def __init__(self, notification_use_case: NotificationUseCase):
        self.notification_use_case = notification_use_case

    async def process_event(self, event: CallEvent):
        await self.notification_use_case.handle_call_event(event)
import structlog
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ContentType,
    ReplyKeyboardRemove,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from telegram_bot.application.services import AuthService
from telegram_bot.ports.message_port import MessagePort
from telegram_bot.config import settings

logger = structlog.get_logger()


class TelegramAdapter(MessagePort):
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.bot = Bot(token=settings.TELEGRAM_TOKEN)
        self.dp = Dispatcher()

        self._register_handlers()

    def _register_handlers(self):
        @self.dp.message(Command("start"))
        async def start_handler(message: types.Message):
            keyboard = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Поделиться номером", request_contact=True)]],
                resize_keyboard=True,
                one_time_keyboard=True,
                selective=True,
                input_field_placeholder=""
            )
            msg = (
                f"Чтобы начать работу, нажмите кнопку «Поделиться номером» и отправьте "
                f"свой телефон — мы используем его, чтобы найти организации, привязанные к "
                f"вашему аккаунту."
            )
            await self.bot.send_message(chat_id=message.chat.id, text=msg, reply_markup=keyboard)

        @self.dp.message(F.content_type == ContentType.CONTACT)
        async def contact_handler(message: types.Message):
            result = await self.auth_service.handle_phone_auth(message.contact.phone_number, message.from_user.id)
            if result.get('status') == 'success':
                keyboard = ReplyKeyboardMarkup(
                    keyboard=[
                        [
                            KeyboardButton(
                                text="Сканировать QR",
                                web_app=WebAppInfo(
                                    url=settings.WEBAPP_URL
                                )
                            )
                        ]
                    ],
                    resize_keyboard=True,
                )
                await self.bot.send_message(
                    message.chat.id, result['message'],
                    reply_markup=keyboard,
                )
            else:
                await self.bot.send_message(message.chat.id, result['message'])

        @self.dp.message(F.web_app_data)  # Обработка data from Web App (aiogram handles web_app_data)
        async def web_app_data_handler(message: types.Message):
            token_value = message.web_app_data.data
            if await self.auth_service.handle_qr_data(token_value, message.from_user.id):
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[[
                        InlineKeyboardButton(text="Подтвердить", callback_data=f"confirm_qr:{token_value}")
                ]])
                await self.bot.send_message(message.chat.id, "Подтвердить вход в систему", reply_markup=keyboard)
            else:
                await self.bot.send_message(message.chat.id, "Неверный или просроченный QR-код.")

        @self.dp.callback_query(lambda query: query.data and query.data.startswith("confirm_qr:"))
        async def confirm_callback(query: types.CallbackQuery):
            qr_token = query.data.split(":", 1)[1]
            if await self.auth_service.confirm_qr_auth(qr_token, query.from_user.id):
                await self.bot.send_message(query.from_user.id, "Вход подтвержден!")
            else:
                await self.bot.send_message(query.from_user.id, "Не удалось подтвердить вход.")

            await query.answer("Подтверждено")

    async def send_message(
            self,
            user_id: int,
            text: str,
            with_confirm_button: bool = False,
            with_delete_button: bool = False,
            reply_markup: ReplyKeyboardMarkup | InlineKeyboardMarkup | ReplyKeyboardRemove | None = None
    ):
        # TODO оставить только await self.bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard)
        if with_confirm_button:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Подтвердить вход", callback_data="confirm_auth")]])
        elif with_delete_button:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Удалить", callback_data="delete_missed")]])
        else:
            keyboard = reply_markup  # Поддержка custom keyboard

        msg = await self.bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard)
        return msg.message_id

    async def delete_message(self, user_id: int, message_id: int):
        await self.bot.delete_message(chat_id=user_id, message_id=message_id)

    async def start_polling(self):
        await self.dp.start_polling(self.bot)

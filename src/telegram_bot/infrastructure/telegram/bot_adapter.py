import structlog
from aiogram import Bot, Dispatcher, types, F  # Импорт F из aiogram
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.enums import ContentType  # Для ContentType.CONTACT

from telegram_bot.ports.message_port import MessagePort
from telegram_bot.config import settings

logger = structlog.get_logger()

class TelegramAdapter(MessagePort):
    def __init__(self):
        self.bot = Bot(token=settings.TELEGRAM_TOKEN)
        self.dp = Dispatcher()

    async def send_message(self, user_id: int, text: str, with_confirm_button: bool = False, with_delete_button: bool = False):
        keyboard = None
        if with_confirm_button:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Подтвердить вход", callback_data="confirm_auth")]])
        elif with_delete_button:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Удалить", callback_data="delete_missed")]])
        msg = await self.bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard)
        return msg.message_id

    async def delete_message(self, user_id: int, message_id: int):
        await self.bot.delete_message(chat_id=user_id, message_id=message_id)

    async def start_polling(self, auth_service, notification_service, storage_port):
        @self.dp.message(Command("start"))
        async def start_handler(message: types.Message):
            keyboard = types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text="Поделиться номером", request_contact=True)]])
            await message.reply("Чтобы начать работу, нажмите кнопку...", reply_markup=keyboard)

        @self.dp.message(F.content_type == ContentType.CONTACT)  # Используйте F для проверки content_type
        async def contact_handler(message: types.Message):
            await auth_service.handle_phone_auth(message.contact.phone_number, message.from_user.id)

        @self.dp.message(Command("scan_qr"))  # Или кнопка в меню
        async def scan_qr_handler(message: types.Message):
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Сканировать QR", web_app=WebAppInfo(url="https://your-webapp-url"))]])
            await message.reply("Запуск Web App для сканирования", reply_markup=keyboard)

        @self.dp.message()  # Обработка data from Web App (aiogram handles web_app_data)
        async def web_app_data_handler(message: types.Message):
            if message.web_app_data:
                token_value = message.web_app_data.data  # auth_token from QR
                await auth_service.handle_qr_data(token_value, message.from_user.id)

        @self.dp.callback_query(lambda query: query.data == "confirm_auth")
        async def confirm_callback(query: types.CallbackQuery):
            # Извлечь token (теперь используем injected storage_port)
            token_value = await storage_port.get(f'pending_auth:{query.from_user.id}')  # Пример
            await auth_service.confirm_qr_auth(token_value, query.from_user.id)
            await query.answer("Подтверждено")

        @self.dp.callback_query(lambda query: query.data == "delete_missed")
        async def delete_callback(query: types.CallbackQuery):
            await self.bot.delete_message(query.message.chat.id, query.message.message_id)
            await query.answer("Удалено")

        await self.dp.start_polling(self.bot)
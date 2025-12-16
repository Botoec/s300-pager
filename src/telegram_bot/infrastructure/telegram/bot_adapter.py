import structlog
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, ContentType, ReplyKeyboardRemove, KeyboardButton, ReplyKeyboardMarkup
from telegram_bot.ports.message_port import MessagePort
from telegram_bot.config import settings

logger = structlog.get_logger()

class TelegramAdapter(MessagePort):
   def __init__(self):
       self.bot = Bot(token=settings.TELEGRAM_TOKEN)
       self.dp = Dispatcher()

   async def send_message(self, user_id: int, text: str, with_confirm_button: bool = False, with_delete_button: bool = False, reply_markup: ReplyKeyboardMarkup | InlineKeyboardMarkup | ReplyKeyboardRemove | None = None):
       if with_confirm_button:
           keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Подтвердить вход", callback_data="confirm_auth")]])
       elif with_delete_button:
           keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Удалить", callback_data="delete_missed")]])
       else:
           keyboard = reply_markup  # Поддержка custom keyboard

       msg = await self.bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard)
       return msg.message_id

   async def delete_message(self, user_id: int, message_id: int):
       await self.bot.delete_message(chat_id=user_id, message_id=message_id)

   async def start_polling(self, auth_service, notification_service, storage_port):
       @self.dp.message(Command("start"))
       async def start_handler(message: types.Message):
           keyboard = ReplyKeyboardMarkup(
               keyboard=[[KeyboardButton(text="Поделиться номером", request_contact=True)]],
               resize_keyboard=True,  # Уменьшает клавиатуру
               one_time_keyboard=True,  # Скрывает клавиатуру после нажатия
               selective=True,  # Показывает клавиатуру только для этого сообщения
               input_field_placeholder=""  # Пустой плейсхолдер для скрытия панели ввода
           )
           msg = (
               f"Чтобы начать работу, нажмите кнопку «Поделиться номером» и отправьте "
               f"свой телефон — мы используем его, чтобы найти организации, привязанные к "
               f"вашему аккаунту."
           )
           await self.bot.send_message(chat_id=message.chat.id, text=msg, reply_markup=keyboard)

       @self.dp.message(F.content_type == ContentType.CONTACT)
       async def contact_handler(message: types.Message):
           await auth_service.handle_phone_auth(message.contact.phone_number, message.from_user.id)

       # @self.dp.message(F.text == "Сканировать QR")  # Вызов логики сканирования по кнопке
       # async def scan_qr_handler(message: types.Message):
       #     keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Сканировать QR", web_app=WebAppInfo(url="https://olid-roger-furnitureless.ngrok-free.dev/index.html"))]])  # URL вашего хостед WebApp
       #     await message.reply("Запуск Web App для сканирования", reply_markup=keyboard)

       @self.dp.message()  # Обработка data from Web App (aiogram handles web_app_data)
       async def web_app_data_handler(message: types.Message):
           logger.warning("Received message from WebApp", message=message)  # Добавлено: Логируем весь message для отладки
           if message.web_app_data:
               token_value = message.web_app_data.data  # auth_token from QR
               logger.info(f"Received QR token: {token_value}")  # Логирование токена
               await auth_service.handle_qr_data(token_value, message.from_user.id)
           else:
               logger.warning("No web_app_data in message")  # Если данные не пришли

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
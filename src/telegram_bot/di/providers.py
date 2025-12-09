from dishka import Provider, Scope, provide
from telegram_bot.infrastructure.telegram.bot_adapter import TelegramAdapter
from telegram_bot.infrastructure.kafka.consumer_adapter import KafkaAdapter
from telegram_bot.infrastructure.auth.http_adapter import HttpAuthAdapter
from telegram_bot.infrastructure.redis.storage_adapter import RedisAdapter
from telegram_bot.domain.use_cases import PhoneAuthUseCase, QrAuthUseCase, NotificationUseCase
from telegram_bot.application.services import AuthService, NotificationService
from telegram_bot.ports.message_port import MessagePort  # Импорт для provides
from telegram_bot.ports.event_port import EventPort
from telegram_bot.ports.auth_port import AuthPort
from telegram_bot.ports.storage_port import StoragePort


class AppProvider(Provider):
    scope = Scope.APP

    message_port = provide(TelegramAdapter, provides=MessagePort)  # Добавлено provides
    event_port = provide(KafkaAdapter, provides=EventPort)  # Добавлено
    auth_port = provide(HttpAuthAdapter, provides=AuthPort)  # Добавлено
    storage_port = provide(RedisAdapter, provides=StoragePort)  # Добавлено

    phone_use_case = provide(PhoneAuthUseCase)
    qr_use_case = provide(QrAuthUseCase)
    notification_use_case = provide(NotificationUseCase)

    auth_service = provide(AuthService)
    notification_service = provide(NotificationService)
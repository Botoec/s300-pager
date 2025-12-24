from dishka import Provider, Scope, provide

from telegram_bot.infrastructure.jwt.jwt_decoder_adapter import JwtDecoderAdapter
from telegram_bot.infrastructure.kafka.producer_adapter import KafkaProducerAdapter
from telegram_bot.infrastructure.telegram.bot_adapter import TelegramAdapter
from telegram_bot.infrastructure.kafka.consumer_adapter import KafkaConsumerAdapter
from telegram_bot.infrastructure.auth.http_adapter import HttpAuthAdapter
from telegram_bot.infrastructure.redis.storage_adapter import RedisAdapter
from telegram_bot.domain.use_cases import PhoneAuthUseCase, QrAuthUseCase, NotificationUseCase
from telegram_bot.application.services import AuthService, NotificationService
from telegram_bot.ports.jwt_decoder_port import JwtDecoderPort
from telegram_bot.ports.kafka.producer_port import ProducerPort
from telegram_bot.ports.message_port import MessagePort
from telegram_bot.ports.kafka.consumer_port import ConsumerPort
from telegram_bot.ports.auth_port import AuthPort
from telegram_bot.ports.redis_storage_port import RedisStoragePort


class AppProvider(Provider):
    scope = Scope.APP

    auth_service = provide(AuthService)
    notification_service = provide(NotificationService)

    message_port = provide(TelegramAdapter, provides=MessagePort)
    kafka_producer_port = provide(KafkaProducerAdapter, provides=ProducerPort)
    kafka_consumer_port = provide(KafkaConsumerAdapter, provides=ConsumerPort)
    auth_port = provide(HttpAuthAdapter, provides=AuthPort)
    redis_storage_port = provide(RedisAdapter, provides=RedisStoragePort)
    token_decoder_port = provide(JwtDecoderAdapter, provides=JwtDecoderPort)

    phone_use_case = provide(PhoneAuthUseCase)
    qr_use_case = provide(QrAuthUseCase)
    notification_use_case = provide(NotificationUseCase)

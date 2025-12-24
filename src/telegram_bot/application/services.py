# from domain import (
#     PhoneAuth,
#     PhoneAuthUseCase,
#     QrAuthUseCase,
#     NotificationUseCase,
#     CallEvent,
# )
from json import loads

import structlog

from telegram_bot.domain.entities import (
    PhoneAuth,
    CallEvent,
    TokenPayload,
)
from telegram_bot.domain.use_cases import (
    PhoneAuthUseCase,
    QrAuthUseCase,
    NotificationUseCase,
)
from telegram_bot.ports import RedisStoragePort
from telegram_bot.ports.jwt_decoder_port import JwtDecoderPort
from telegram_bot.ports.kafka.producer_port import ProducerPort

logger = structlog.get_logger()


class AuthService:
    def __init__(
            self,
            phone_use_case: PhoneAuthUseCase,
            qr_use_case: QrAuthUseCase,
            kafka_producer_port: ProducerPort,
            token_decoder_port: JwtDecoderPort,
            redis_storage_port: RedisStoragePort
    ):
        self.phone_use_case = phone_use_case
        self.qr_use_case = qr_use_case
        self.kafka_producer_port = kafka_producer_port
        self.token_decoder_port = token_decoder_port
        self.redis_storage = redis_storage_port

    async def handle_phone_auth(self, phone: str, user_id: int):
        return await self.phone_use_case.execute(PhoneAuth(phone, user_id))

    async def handle_qr_data(self, token_value: str, user_id: int) -> bool:
        if token_data := await self.qr_use_case.validate_token(token_value, user_id):
            await self.qr_use_case.update_token_status(token_value, token_data, user_id, 'scanned')
            await self.kafka_producer_port.send(
                topic='qr_authentication_stage',
                key=token_value,
                value={
                    'operation': 'qr_authentication_stage',
                    'session_id': token_data['session_id'],
                    'status': 'scanned',
                },
            )
            return True
        return False

    async def confirm_qr_auth(self, token_value: str, user_id: int):
        token_data = await self.qr_use_case.confirm_auth(token_value, user_id)
        if token_data:
            access_token_payload = await self.get_current_token_payload(user_id)

            if access_token_payload is None:
                logger.warning(f'Не найден access_token_payload')
                return False

            await self.kafka_producer_port.send(
                topic='qr_authentication_stage',
                key=token_value,
                value={
                    'operation': 'qr_authentication_stage',
                    'session_id': token_data['session_id'],
                    'user_id': access_token_payload.user_id,
                    'status': 'confirmed',
                },
            )
            return True
        return False

    async def get_current_token_payload(self, user_id: int) -> TokenPayload | None:
        user_org_tokens: dict = await self.redis_storage.get(f"user:{user_id}:tokens")

        if not user_org_tokens:
            return None

        first_users_org_tokens = next(iter(user_org_tokens.values()))

        access_token = first_users_org_tokens.get("access_token")
        if not access_token:
            return None

        return await self.token_decoder_port.decode(access_token)


class NotificationService:
    def __init__(self, notification_use_case: NotificationUseCase):
        self.notification_use_case = notification_use_case

    async def process_event(self, event: CallEvent):
        await self.notification_use_case.handle_call_event(event)

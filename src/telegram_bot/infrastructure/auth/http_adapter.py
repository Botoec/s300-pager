import aiohttp
import structlog
from telegram_bot.domain.entities import CallEvent, AuthToken
from telegram_bot.config import settings
from telegram_bot.ports.auth_port import AuthPort

logger = structlog.get_logger()

class HttpAuthAdapter(AuthPort):
    async def verify_phone(self, phone: str, user_id: int) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            logger.info(f'phone: {phone}, user_id: {user_id}')
            # TODO
            async with session.post(f"{settings.GW_API_URL}/auth/private/telegram/auth/verify_by_phone/", json={"phone": '9633494219', "telegram_user_id": user_id}) as resp:
                return await resp.json()

    async def check_user_for_notifications(self, event: CallEvent) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{settings.GW_API_URL}/check_user/", json=event.__dict__) as resp:
                return await resp.json()  # {authorized: bool, dnd: 'off/on', extension: str}

    async def authenticate(self, profile_number: str, user_id: int) -> dict:
        async with aiohttp.ClientSession() as session:
            # TODO
            async with session.post(f"{settings.GW_API_URL}/auth/private/telegram/auth/authenticate/", json={"profile": profile_number, "telegram_user_id": user_id}) as resp:
                return await resp.json()

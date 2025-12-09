import aiohttp
import structlog
# from ports import AuthPort
from telegram_bot.domain.entities import CallEvent, AuthToken
from telegram_bot.config import settings
from telegram_bot.ports.auth_port import AuthPort

logger = structlog.get_logger()

class HttpAuthAdapter(AuthPort):
    async def verify_phone(self, phone: str, user_id: int) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{settings.AUTH_API_URL}/verify_phone", json={"phone": phone, "user_id": user_id}) as resp:
                return await resp.json()  # {status: 'found/not_found/conflict', orgs: [...]}

    async def check_user_for_notifications(self, event: CallEvent) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{settings.AUTH_API_URL}/check_user", json=event.__dict__) as resp:
                return await resp.json()  # {authorized: bool, dnd: 'off/on', extension: str}

    async def authenticate(self, token: AuthToken) -> bool:
        # Для QR, но в ТЗ - в Redis
        return True  # Симуляция
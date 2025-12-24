from typing import Optional

import jwt
from jwt.exceptions import PyJWTError, ExpiredSignatureError, InvalidTokenError
import structlog

from telegram_bot.domain.entities import TokenPayload
from telegram_bot.ports.jwt_decoder_port import JwtDecoderPort
from telegram_bot.config import settings

logger = structlog.get_logger(__name__)


class JwtDecoderAdapter(JwtDecoderPort):
    def __init__(self):
        # self.public_key = settings.JWT_PUBLIC_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.verify_signature = settings.JWT_VERIFY_SIGNATURE

    async def decode(self, token: str) -> Optional[TokenPayload]:
        try:
            payload = jwt.decode(
                token,
                self.verify_signature,
                # key=self.public_key,
                algorithms=[self.algorithm],
                options={
                    "verify_exp": False,
                },
            )

            return TokenPayload(**payload)
        except (InvalidTokenError, PyJWTError) as e: # TODO
            logger.debug("Failed to decode JWT", error=str(e), token_prefix=token[:10])
            return None
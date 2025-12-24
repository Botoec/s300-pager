from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class PhoneAuth:
    phone_number: str
    user_id: int
    organizations: list[str] = None  # Список организаций

@dataclass(frozen=True)
class AuthToken:
    value: str
    user_id: int
    expires_at: datetime

@dataclass(frozen=True)
class JwtTokens:
    access_token: str
    refresh_token: str

@dataclass(frozen=True)
class CallEvent:
    event_type: str  # dial, answer_call, end_call, finish_call
    caller_type: str  # employee/resident
    caller_name: str
    phone: str
    organization: str = None
    address: str = None
    group_call: bool = False
    status: str = None  # NO_ANSWER для missed


@dataclass(frozen=True)
class TokenPayload:
    token_type: str
    exp: int
    iat: int
    jti: str
    user_id: str
    auth_source: str
    profile: str
    username: str
    type: int
    profile_company: str
    telegram_id: str

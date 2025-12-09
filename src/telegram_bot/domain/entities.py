from dataclasses import dataclass
from datetime import datetime

@dataclass
class PhoneAuth:
    phone_number: str
    user_id: int
    organizations: list[str] = None  # Список организаций

@dataclass
class AuthToken:
    value: str
    user_id: int
    expires_at: datetime

@dataclass
class JwtTokens:
    access_token: str
    refresh_token: str

@dataclass
class CallEvent:
    event_type: str  # dial, answer_call, end_call, finish_call
    caller_type: str  # employee/resident
    caller_name: str
    phone: str
    organization: str = None
    address: str = None
    group_call: bool = False
    status: str = None  # NO_ANSWER для missed
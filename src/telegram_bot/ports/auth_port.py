from abc import ABC, abstractmethod


class AuthPort(ABC):
    @abstractmethod
    async def authenticate(self, profile_number: str, user_id: int) -> bool:
        pass
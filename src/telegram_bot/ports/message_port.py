from abc import ABC, abstractmethod

class MessagePort(ABC):
    @abstractmethod
    async def send_message(self, user_id: int, text: str):
        pass

    @abstractmethod
    async def delete_message(self, user_id: int, message_id: int):
        pass

    @abstractmethod
    async def start_polling(self, auth_service, notification_service, storage_port):
        pass  # Добавлено с параметрами для точности
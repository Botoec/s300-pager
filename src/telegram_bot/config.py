from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TELEGRAM_TOKEN: str = "8273254411:AAE2u4xUrb48FVxZn81dTZseMAA0qYgNu3I" # TODO
    KAFKA_BOOTSTRAP_SERVERS: str = "10.1.1.168:9092"
    KAFKA_TOPIC: list[str] = ["qr_authentication"]
    GW_API_URL: str = "http://192.168.10.251:8084"  # Бэкенд для проверок
    REDIS_URL: str = "redis://redis:6379/0"     # Для auth_token
    WEBAPP_URL: str = "https://mz.nanitor.ru/"
    PHONE_RECHECK_INTERVAL: int = 30  # Дни для перепроверки номера
    PHONE_RECHECK_COUNT: int = 10     # Каждый N вход
    BOT_USERNAME: str = "s300-pager-bot"   # Для QR URL
    JWT_ALGORITHM: str = 'HS256'
    JWT_VERIFY_SIGNATURE: str = 'KEK'

settings = Settings()
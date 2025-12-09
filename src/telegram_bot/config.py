from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TELEGRAM_TOKEN: str = ...
    KAFKA_BOOTSTRAP_SERVERS: str = "10.1.1.168:9092"
    KAFKA_TOPIC: str = "test_c300_topic"
    AUTH_API_URL: str = "http://example.com/auth"  # Бэкенд для проверок
    REDIS_URL: str = "redis://redis:6379/0"     # Для auth_token
    PHONE_RECHECK_INTERVAL: int = 30  # Дни для перепроверки номера
    PHONE_RECHECK_COUNT: int = 10     # Каждый N вход
    BOT_USERNAME: str = "s300-pager-bot"   # Для QR URL

settings = Settings()
from aiokafka import AIOKafkaProducer
import json
import structlog
from telegram_bot.config import settings
from telegram_bot.ports.kafka.producer_port import ProducerPort

logger = structlog.get_logger()


class KafkaProducerAdapter(ProducerPort):
    def __init__(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
        )

    async def start(self):
        await self.producer.start()

    async def stop(self):
        await self.producer.stop()

    async def send(self, topic: str, value: dict | list | str, key: str | None = None):
        try:
            await self.producer.send_and_wait(topic, value=value, key=key)
            logger.info(f"Отправлено в Kafka topic={topic}, key={key}, value={value}")
        except Exception as e:
            logger.error(f"Ошибка при попытке отправки в Kafka: {e}", exc_info=e)
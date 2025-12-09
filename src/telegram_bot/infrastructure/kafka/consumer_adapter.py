import json
from logging import getLogger

import structlog

from aiokafka import AIOKafkaConsumer

from telegram_bot.ports import EventPort
from telegram_bot.config import settings
from telegram_bot.domain.entities import CallEvent
from telegram_bot.application.services import NotificationService

logger = structlog.get_logger()

class KafkaAdapter(EventPort):
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        self.logger = getLogger(__name__)

    async def consume_events(self):
        consumer = AIOKafkaConsumer(
            settings.KAFKA_TOPIC,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="pager-bot-group",
            auto_offset_reset="earliest",
        )
        await consumer.start()
        try:
            async for msg in consumer:
                event_data = json.loads(msg.value.decode('utf-8'))
                if event_data.get('operation') == 'tmp_test': # TODO
                    event = CallEvent(**event_data)  # Парсим в entity
                    await self.notification_service.process_event(event)
                    logger.info("Processed Kafka event", type=event.event_type)
        finally:
            await consumer.stop()

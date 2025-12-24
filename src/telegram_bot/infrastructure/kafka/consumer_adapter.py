import json
from asyncio import CancelledError

import structlog

from aiokafka import AIOKafkaConsumer

from telegram_bot.ports import ConsumerPort, RedisStoragePort
from telegram_bot.config import settings
from telegram_bot.domain.entities import CallEvent
from telegram_bot.application.services import NotificationService

logger = structlog.get_logger()


class KafkaConsumerAdapter(ConsumerPort):
    def __init__(
            self,
            notification_service: NotificationService,
            redis_storage_port: RedisStoragePort
    ):
        self.notification_service = notification_service
        self.redis_storage_port = redis_storage_port
        self.consumer = AIOKafkaConsumer(
            *settings.KAFKA_TOPIC,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="pager-bot-group",
            # auto_offset_reset="earliest",
        )

    async def start(self):
        await self.consumer.start()

    async def stop(self):
        await self.consumer.stop()

    async def consume(self):
        try:
            async for msg in self.consumer:
                event_data = json.loads(msg.value.decode('utf-8'))
                match event_data.get('operation'):
                    case 'qr_token_generated':
                        logger.warning(f'event_data : {event_data}')
                        await self.redis_storage_port.set(
                            key=f"qr_token:{event_data.get('qr_token')}",
                            value={
                                'session_id': event_data.get('session_id'),
                                'status': 'pending',
                            },
                            ttl=900,
                        )
                    case 'tmp_test':  # TODO
                        event = CallEvent(**event_data)
                        await self.notification_service.process_event(event)
                        logger.info("Processed Kafka event", type=event.event_type)
                    case _:
                        break
        except CancelledError:
            logger.info("Kafka consumer cancelled")
            raise
        finally:
            await self.stop()

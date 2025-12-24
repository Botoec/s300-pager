import asyncio

import structlog
from dishka import make_async_container

from telegram_bot.di.providers import AppProvider
from telegram_bot.ports import MessagePort, ConsumerPort
from telegram_bot.ports.kafka.producer_port import ProducerPort

logger = structlog.get_logger()


async def main():
    container = make_async_container(AppProvider())

    async with container() as app_container:
        message_port: MessagePort = await app_container.get(MessagePort)
        kafka_consumer: ConsumerPort = await app_container.get(ConsumerPort)
        kafka_producer: ProducerPort = await app_container.get(ProducerPort)

        await kafka_producer.start()
        await kafka_consumer.start()

        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(kafka_consumer.consume())
                tg.create_task(message_port.start_polling())

            logger.info("Все задачи завершились корректно.")

        except* Exception as eg:
            logger.error(f"Одна или несколько задач завершились с ошибкой: {eg.exceptions}")

        finally:
            await kafka_consumer.stop()
            await kafka_producer.stop()


# def _handle_shutdown(loop: asyncio.AbstractEventLoop):
#     """Обработчик SIGINT/SIGTERM — отменяем все задачи"""
#     tasks = [task for task in asyncio.all_tasks(loop) if task is not asyncio.current_task(loop)]
#     for task in tasks:
#         task.cancel()


if __name__ == "__main__":
    # loop = asyncio.get_event_loop()
    #
    # # Ловим сигналы для graceful shutdown
    # for sig in (signal.SIGINT, signal.SIGTERM):
    #     loop.add_signal_handler(sig, _handle_shutdown, loop)

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.warning("\nБот остановлен пользователем.")
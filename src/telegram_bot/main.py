import asyncio
import signal
import structlog
from dishka import make_async_container

from telegram_bot.di.providers import AppProvider
from telegram_bot.ports.event_port import EventPort
from telegram_bot.ports.message_port import MessagePort
from telegram_bot.application.services import AuthService, NotificationService
from telegram_bot.ports.storage_port import StoragePort

logger = structlog.get_logger()

async def main():
    container = make_async_container(AppProvider())

    # event_port = await container.get(EventPort)
    message_port = await container.get(MessagePort)
    auth_service = await container.get(AuthService)
    notification_service = await container.get(NotificationService)
    storage_port = await container.get(StoragePort)

    # Ожидаем сигнала завершения (graceful shutdown)
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def shutdown(sig, frame):
        logger.info(f"Received signal {sig.name}, shutting down")
        stop_event.set()

    # Правильный lambda с параметрами
    loop.add_signal_handler(signal.SIGINT, shutdown)
    loop.add_signal_handler(signal.SIGTERM, shutdown)

    logger.warning('create_tasks <<<')

    # Запускаем задачи с TaskGroup для structured concurrency
    async with asyncio.TaskGroup() as tg:
        # tg.create_task(event_port.consume_events())
        tg.create_task(message_port.start_polling(auth_service, notification_service, storage_port))

        await stop_event.wait()  # Блокировка до сигнала

    # Cleanup (TaskGroup автоматически отменит при выходе)
    logger.info("Closing container")
    await container.close()

if __name__ == "__main__":
    asyncio.run(main())
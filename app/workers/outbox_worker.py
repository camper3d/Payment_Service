import asyncio
from app.core.database import db_manager
from app.services.outbox_actions import OutboxService
from app.services.event_publisher import event_publisher
from app.core.config import settings


class OutboxWorker:
    def __init__(self):
        self.running = False

    async def process_pending_events(self):
        """Обрабатывает ожидающие события из outbox"""
        async with db_manager.async_session_maker() as session:
            outbox_service = OutboxService(session)

            events = await outbox_service.get_pending_events(
                limit=settings.outbox_batch_size
            )

            if not events:
                return

            await event_publisher.connect()

            for event in events:
                try:
                    if event.event_type == "payment.created":
                        await event_publisher.publish_payment_created(
                            payment_id=str(event.aggregate_id),
                            payment_data=event.payload
                        )

                    await outbox_service.mark_as_processed(event.id)

                except Exception as e:
                    # Отмечаем как failed с ошибкой
                    await outbox_service.mark_as_failed(event.id, str(e))

            await session.commit()

    async def run(self):
        """Запускает бесконечный цикл обработки"""
        self.running = True
        print("Outbox worker started")

        while self.running:
            try:
                await self.process_pending_events()
                await asyncio.sleep(settings.outbox_poll_interval)
            except Exception as e:
                print(f"Error in outbox worker: {e}")
                await asyncio.sleep(5)

        await event_publisher.close()

    def stop(self):
        """Останавливает worker"""
        self.running = False


outbox_worker = OutboxWorker()
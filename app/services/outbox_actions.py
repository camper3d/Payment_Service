from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID, uuid4
from datetime import datetime
import json
from app.models.outbox import OutboxEvent, OutboxStatus
from app.models.payment import Payment


class OutboxService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_event(
            self,
            event_type: str,
            aggregate_id: UUID,
            payload: dict
    ) -> OutboxEvent:
        """Создаёт событие в outbox"""
        event = OutboxEvent(
            event_id=uuid4(),
            event_type=event_type,
            aggregate_id=aggregate_id,
            payload=payload,
            status=OutboxStatus.PENDING
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def mark_as_processed(self, event_id: UUID):
        """Отмечает событие как обработанное"""
        await self.session.execute(
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(
                status=OutboxStatus.PROCESSED,
                processed_at=datetime.utcnow()
            )
        )

    async def mark_as_failed(self, event_id: UUID, error: str):
        """Отмечает событие с ошибкой"""
        await self.session.execute(
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(
                status=OutboxStatus.FAILED,
                last_error=error[:1000],
                retry_count=OutboxEvent.retry_count + 1
            )
        )

    async def get_pending_events(self, limit: int = 100) -> list[OutboxEvent]:
        """Получает список ожидающих обработки событий"""
        result = await self.session.execute(
            select(OutboxEvent)
            .where(OutboxEvent.status == OutboxStatus.PENDING)
            .order_by(OutboxEvent.created_at)
            .limit(limit)
        )
        return result.scalars().all()
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentCreateRequest
from app.services.outbox_actions import OutboxService


class PaymentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.outbox_service = OutboxService(session)

    async def create_payment(
            self,
            idempotency_key: str,
            payment_data: PaymentCreateRequest
    ) -> Payment:
        """Создаёт новый платеж с проверкой идемпотентности"""

        existing_payment = await self.get_payment_by_idempotency_key(idempotency_key)

        if existing_payment:
            return existing_payment

        payment = Payment(
            idempotency_key=idempotency_key,
            amount=payment_data.amount,
            currency=payment_data.currency.value,
            description=payment_data.description,
            meta_data=payment_data.meta_data or {},
            webhook_url=str(payment_data.webhook_url),
            status=PaymentStatus.PENDING
        )

        self.session.add(payment)
        await self.session.flush()  # Чтобы получить payment.id

        # Создаём событие в outbox
        event_payload = {
            "payment_id": str(payment.id),
            "amount": str(payment.amount),
            "currency": payment.currency,
            "description": payment.description,
            "meta_data": payment.meta_data,
            "webhook_url": payment.webhook_url,
            "idempotency_key": payment.idempotency_key,
            "created_at": payment.created_at.isoformat() if payment.created_at else None
        }

        await self.outbox_service.create_event(
            event_type="payment.created",
            aggregate_id=payment.id,
            payload=event_payload
        )

        await self.session.commit()
        await self.session.refresh(payment)

        return payment

    async def get_payment_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        """Ищет платеж по idempotency_key"""
        result = await self.session.execute(
            select(Payment).where(Payment.idempotency_key == idempotency_key)
        )
        return result.scalar_one_or_none()

    async def get_payment_by_id(self, payment_id: UUID) -> Payment | None:
        """Получает платеж по айди"""
        return await self.session.get(Payment, payment_id)
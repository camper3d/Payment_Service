from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentCreateRequest


class PaymentService:
    def __init__(self, session: AsyncSession):
        self.session = session

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
            metadata=payment_data.metadata or {},
            webhook_url=str(payment_data.webhook_url),
            status=PaymentStatus.PENDING
        )

        self.session.add(payment)
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
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Annotated

from app.core.database import db_manager
from app.services.payment_actions import PaymentService
from app.schemas.payment import (
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentDetailsResponse
)

router = APIRouter(prefix="/api/payments", tags=["payments"])


async def get_db() -> AsyncSession:
    async for session in db_manager.get_session():
        yield session


@router.post(
    "/",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=PaymentCreateResponse
)
async def create_payment(
        payment_data: PaymentCreateRequest,
        idempotency_key: Annotated[str, Header(..., description="Ключ идемпотентности")],
        db: AsyncSession = Depends(get_db)
):
    """
    Создание нового платежа

    - idempotency_key: уникальный ключ для защиты от дублей (обязателен в заголовке)
    - amount: сумма платежа (больше 0)
    - currency: валюта (RUB, USD, EUR)
    - description: описание платежа
    - meta_data: дополнительные данные (опционально)
    - webhook_url: URL для уведомления о результате
    """
    payment_service = PaymentService(db)

    try:
        payment = await payment_service.create_payment(idempotency_key, payment_data)

        return PaymentCreateResponse(
            payment_id=payment.id,
            status=payment.status,
            created_at=payment.created_at
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment: {str(e)}"
        )


@router.get(
    "/{payment_id}",
    response_model=PaymentDetailsResponse
)
async def get_payment(
        payment_id: UUID,
        db: AsyncSession = Depends(get_db)
):
    """Получение информации о платеже"""
    payment_service = PaymentService(db)
    payment = await payment_service.get_payment_by_id(payment_id)

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment {payment_id} not found"
        )

    return payment
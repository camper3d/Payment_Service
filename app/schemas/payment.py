from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from enum import Enum


class Currency(str, Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class PaymentCreateRequest(BaseModel):
    """Request схема для создания платежа"""
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Сумма платежа")
    currency: Currency = Field(..., description="Валюта: RUB, USD, EUR")
    description: str = Field(..., min_length=1, max_length=500)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Дополнительные метаданные")
    webhook_url: HttpUrl = Field(..., description="URL для уведомлений")


class PaymentCreateResponse(BaseModel):
    """Request схема после создания платежа"""
    payment_id: UUID
    status: PaymentStatus
    created_at: datetime


class PaymentDetailsResponse(BaseModel):
    """Response схема для получения деталей"""
    id: UUID
    idempotency_key: str
    amount: Decimal
    currency: Currency
    description: str
    meta_data: Optional[Dict[str, Any]]
    status: PaymentStatus
    webhook_url: HttpUrl
    created_at: datetime
    processed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
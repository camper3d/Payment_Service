from sqlalchemy import Column, String, Numeric, DateTime, Enum, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from enum import Enum as PyEnum
from app.core.database import Base


class PaymentStatus(PyEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idempotency_key = Column(String(255), unique=True, nullable=False, index=True)

    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    description = Column(String(500), nullable=False)
    meta_data = Column("metadata", JSON, nullable=True)

    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    webhook_url = Column(String(500), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Payment {self.id} ({self.status.value})>"
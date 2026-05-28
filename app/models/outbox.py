from sqlalchemy import Column, String, DateTime, JSON, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from enum import Enum as PyEnum

from app.core.database import Base


class OutboxStatus(PyEnum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class OutboxEvent(Base):
    __tablename__ = "outbox"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False)
    aggregate_id = Column(UUID(as_uuid=True), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(Enum(OutboxStatus), default=OutboxStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    last_error = Column(String(1000), nullable=True)

    def __repr__(self):
        return f"<OutboxEvent {self.event_type} ({self.status.value})>"
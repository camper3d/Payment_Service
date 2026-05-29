import aio_pika
import json
from typing import Optional
from app.core.config import settings
from datetime import datetime, timezone
from loguru import logger


class EventPublisher:
    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None

    async def connect(self):
        """Подключается к RabbitMQ"""
        self.connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self.channel = await self.connection.channel()

        # Объявляем очередь payments.new
        await self.channel.declare_queue(
            "payments.new",
            durable=True
        )

    async def publish_payment_created(self, payment_id: str, payment_data: dict):
        """Публикует событие о создании платежа в очередь payments.new"""
        if not self.channel:
            await self.connect()

        message = {
            "event_type": "payment.created",
            "payment_id": str(payment_id),
            "data": payment_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                message_id=str(payment_id),
                timestamp=datetime.now(timezone.utc)
            ),
            routing_key="payments.new"
        )
        logger.info(f"Published payment.created event for {payment_id}")

    async def close(self):
        """Закрывает соединение"""
        if self.connection:
            await self.connection.close()


event_publisher = EventPublisher()
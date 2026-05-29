import aio_pika
import json
import asyncio
import logging
from typing import Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy import select, update
from app.core.database import db_manager
from app.models.payment import Payment, PaymentStatus
from app.services.payment_gateway import PaymentGatewayEmulator
from app.services.webhook_sender import WebhookSender

logger = logging.getLogger(__name__)


class PaymentConsumer:
    """Consumer для обработки платежей из очереди"""

    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.webhook_sender = WebhookSender()
        self.is_running = False

    async def connect(self):
        """
        Устанавливает соединение с RabbitMQ и настраивает инфраструктуру очередей.

        Выполняет инициализацию топологии для надежной доставки сообщений:
        1. Подключается к брокеру через `connect_robust` (автоматическое переподключение).
        2. Объявляет основную очередь `payments.new` для новых задач.
        3. Настраивает паттерн DLQ для обработки сбоев:
           - `payments.retry`: очередь с TTL 5 сек для отложенных повторных попыток.
           - `payments.dlx`: обменник для маршрутизации «упавших» сообщений.
           - `payments.dlq`: финальная очередь для сообщений, которые не удалось обработать.
           """
        from app.core.config import settings
        self.connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self.channel = await self.connection.channel()

        await self.channel.declare_queue("payments.new", durable=True)
        await self.channel.declare_queue("payments.dlq", durable=True)

        dlx = await self.channel.declare_exchange(
            "payments.dlx",
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )

        retry_queue = await self.channel.declare_queue(
            "payments.retry",
            durable=True,
            arguments={
                "x-dead-letter-exchange": "payments.dlx",
                "x-dead-letter-routing-key": "payments.new",
                "x-message-ttl": 5000  # 5 секунд до повторной попытки
            }
        )

        logger.info("Payment consumer connected to RabbitMQ")

    async def process_payment_message(self, message: aio_pika.IncomingMessage):
        """Обрабатывает входящее событие о платеже из очереди RabbitMQ.

        Алгоритм обработки:
        1. Десериализует тело сообщения и валидирует наличие `payment_id`.
        2. Проверяет актуальность платежа в БД (защита от дублей/повторной обработки).
        3. Выполняет эмуляцию процессинга через `PaymentGatewayEmulator`.
        4. Обновляет статус платежа (`SUCCEEDED`/`FAILED`) и время обработки в БД.
        5. Отправляет уведомление на `webhook_url` клиента."""
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                payment_id = body.get("payment_id")

                if not payment_id:
                    logger.error("Invalid message: missing payment_id")
                    return

                logger.info(f"Processing payment {payment_id}")

                async with db_manager.async_session_maker() as session:
                    result = await session.execute(
                        select(Payment).where(Payment.id == payment_id)
                    )
                    payment = result.scalar_one_or_none()

                    if not payment:
                        logger.error(f"Payment {payment_id} not found in DB")
                        return

                    if payment.status != PaymentStatus.PENDING:
                        logger.warning(f"Payment {payment_id} already processed: {payment.status}")
                        return

                    success, gateway_message = await PaymentGatewayEmulator.process_payment(
                        payment_id=str(payment.id),
                        amount=payment.amount,
                        currency=payment.currency
                    )

                    new_status = PaymentStatus.SUCCEEDED if success else PaymentStatus.FAILED
                    await session.execute(
                        update(Payment)
                        .where(Payment.id == payment.id)
                        .values(
                            status=new_status,
                            processed_at=datetime.utcnow()
                        )
                    )
                    await session.commit()

                    webhook_success = await self.webhook_sender.send_notification(
                        webhook_url=payment.webhook_url,
                        payment_id=payment.id,
                        status=new_status.value,
                        amount=payment.amount,
                        currency=payment.currency,
                        error_message=None if success else gateway_message
                    )

                    if not webhook_success:
                        logger.warning(f"Webhook failed for payment {payment_id}, but payment status is updated")

                    logger.info(f"Payment {payment_id} processed: {new_status.value}")

            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                raise

    async def consume(self):
        """Запускает consumer для прослушивания очереди"""
        if not self.channel:
            await self.connect()

        queue = await self.channel.get_queue("payments.new")

        await queue.consume(self.process_payment_message)
        logger.info("Payment consumer started, waiting for messages...")

        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            logger.info("Payment consumer stopped")
            await self.webhook_sender.close()

    async def start(self):
        """Запускает consumer"""
        self.is_running = True
        await self.consume()

    async def stop(self):
        """Останавливает consumer"""
        self.is_running = False
        if self.connection:
            await self.connection.close()
        await self.webhook_sender.close()


payment_consumer = PaymentConsumer()
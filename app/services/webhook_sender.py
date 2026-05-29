import httpx
import asyncio
import logging
from typing import Optional
from decimal import Decimal
from uuid import UUID

logger = logging.getLogger(__name__)


class WebhookSender:
    """Отправка webhook уведомлений с retry логикой"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)

    async def send_notification(
            self,
            webhook_url: str,
            payment_id: UUID,
            status: str,
            amount: Decimal,
            currency: str,
            error_message: Optional[str] = None
    ) -> bool:
        """
        Отправляет webhook уведомление с retry логикой
        Retry: 3 попытки с экспоненциальной задержкой (1, 2, 4 секунды)
        """
        payload = {
            "payment_id": str(payment_id),
            "status": status,
            "amount": float(amount),
            "currency": currency,
            "processed_at": None
        }

        if error_message:
            payload["error"] = error_message

        delays = [1, 2, 4]

        for attempt, delay in enumerate(delays, 1):
            try:
                logger.info(f"Sending webhook to {webhook_url}, attempt {attempt}/{len(delays)}")

                response = await self.client.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code in (200, 201, 202):
                    logger.info(f"Webhook sent successfully to {webhook_url}")
                    return True
                else:
                    logger.warning(f"Webhook returned {response.status_code}, attempt {attempt}")

            except Exception as e:
                logger.error(f"Webhook attempt {attempt} failed: {e}")

            if attempt < len(delays):
                await asyncio.sleep(delay)

        logger.error(f"All webhook attempts failed for {webhook_url}")
        return False

    async def close(self):
        await self.client.aclose()
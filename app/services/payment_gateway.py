import random
import asyncio
from typing import Tuple
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class PaymentGatewayEmulator:
    """Эмуляция внешнего платежного шлюза"""

    SUCCESS_RATE = 0.9

    MIN_DELAY = 2
    MAX_DELAY = 5

    @staticmethod
    async def process_payment(
            payment_id: str,
            amount: Decimal,
            currency: str
    ) -> Tuple[bool, str]:
        """
        Эмулирует обработку платежа

        Returns:
            (success: bool, message: str)
        """
        delay = random.uniform(PaymentGatewayEmulator.MIN_DELAY, PaymentGatewayEmulator.MAX_DELAY)
        logger.info(f"Processing payment {payment_id} with delay {delay:.2f}s")
        await asyncio.sleep(delay)

        is_success = random.random() < PaymentGatewayEmulator.SUCCESS_RATE

        if is_success:
            logger.info(f"Payment {payment_id} succeeded")
            return True, "Payment processed successfully"
        else:
            logger.warning(f"Payment {payment_id} failed")
            return False, "Payment gateway error: transaction declined"

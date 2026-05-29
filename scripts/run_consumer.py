import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.consumers.payment_consumer import payment_consumer
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def main():
    try:
        print("Starting payment consumer...")
        await payment_consumer.start()
    except KeyboardInterrupt:
        print("\nStopping payment consumer...")
        await payment_consumer.stop()

if __name__ == "__main__":
    asyncio.run(main())
import asyncio
import sys
from pathlib import Path


sys.path.append(str(Path(__file__).parent.parent))

from app.workers.outbox_worker import outbox_worker


async def main():
    try:
        await outbox_worker.run()
    except KeyboardInterrupt:
        print("\nStopping worker...")
        outbox_worker.stop()

if __name__ == "__main__":
    asyncio.run(main())
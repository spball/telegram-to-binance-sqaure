from __future__ import annotations

import asyncio
import logging

from .binance_client import BinanceSquareClient
from .config import Settings
from .listener import TelegramSquareBridge
from .logging_setup import setup_logging
from .pipeline import MessagePipeline
from .store import MessageStore

LOGGER = logging.getLogger(__name__)


async def main() -> None:
    settings = Settings()
    setup_logging(settings.log_level)
    LOGGER.info(
        "Starting bridge. channels=%s, square_key=%s",
        ",".join(settings.telegram_channels),
        settings.masked_square_key,
    )

    store = MessageStore(settings.sqlite_db_path)
    square_client = BinanceSquareClient(settings)
    pipeline = MessagePipeline(settings, store, square_client)
    bridge = TelegramSquareBridge(settings, pipeline)

    await bridge.run()


if __name__ == "__main__":
    asyncio.run(main())

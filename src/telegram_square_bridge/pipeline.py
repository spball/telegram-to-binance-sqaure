from __future__ import annotations

import asyncio
import logging

from .binance_client import BinanceSquareClient
from .config import Settings
from .models import TelegramMessage
from .store import MessageStore

LOGGER = logging.getLogger(__name__)


class MessagePipeline:
    def __init__(
        self,
        settings: Settings,
        store: MessageStore,
        square_client: BinanceSquareClient,
    ) -> None:
        self.settings = settings
        self.store = store
        self.square_client = square_client

    async def process(self, message: TelegramMessage) -> None:
        correlation_id = f"{message.chat_id}:{message.message_id}"

        if not message.text.strip():
            LOGGER.info("[%s] Skip empty text message", correlation_id)
            return

        if not self.store.try_reserve_message(message.chat_id, message.message_id):
            LOGGER.info("[%s] Skip duplicate message", correlation_id)
            return

        post_text = message.text.strip()
        for attempt in range(1, self.settings.max_retry_attempts + 1):
            result = await self.square_client.post_text(post_text)
            if result.success:
                self.store.mark_posted(
                    message.chat_id,
                    message.message_id,
                    result.content_id,
                    result.post_url,
                    result.code,
                )
                LOGGER.info("[%s] Posted to Square: %s", correlation_id, result.post_url or "url unavailable")
                return

            if attempt < self.settings.max_retry_attempts and result.retryable:
                delay = self.settings.retry_base_seconds ** attempt
                LOGGER.warning(
                    "[%s] Post failed (code=%s), retrying in %ss (%s/%s)",
                    correlation_id,
                    result.code,
                    delay,
                    attempt,
                    self.settings.max_retry_attempts,
                )
                await asyncio.sleep(delay)
                continue

            error_message = result.message or "unknown error"
            self.store.mark_failed(message.chat_id, message.message_id, result.code, error_message)
            LOGGER.error("[%s] Final failure posting to Square: code=%s, message=%s", correlation_id, result.code, error_message)
            return

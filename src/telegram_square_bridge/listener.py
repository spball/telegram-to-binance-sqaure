from __future__ import annotations

import logging
from datetime import datetime

from telethon import TelegramClient, events

from .config import Settings
from .models import TelegramMessage
from .pipeline import MessagePipeline

LOGGER = logging.getLogger(__name__)


class TelegramSquareBridge:
    def __init__(self, settings: Settings, pipeline: MessagePipeline) -> None:
        self.settings = settings
        self.pipeline = pipeline
        self.client = TelegramClient(
            str(settings.telegram_session_path),
            settings.telegram_api_id,
            settings.telegram_api_hash,
        )

    def _register_handlers(self) -> None:
        @self.client.on(events.NewMessage(chats=self.settings.telegram_channel))
        async def on_new_message(event: events.NewMessage.Event) -> None:
            text = event.raw_text or ""
            msg = TelegramMessage(
                chat_id=event.chat_id,
                message_id=event.id,
                date=event.date or datetime.utcnow(),
                text=text,
            )
            await self.pipeline.process(msg)

    async def run(self) -> None:
        self._register_handlers()
        await self.client.start()
        me = await self.client.get_me()
        LOGGER.info(
            "Telegram connected as %s; listening channel=%s",
            getattr(me, "username", None) or getattr(me, "id", "unknown"),
            self.settings.telegram_channel,
        )
        await self.client.run_until_disconnected()

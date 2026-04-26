from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class TelegramMessage:
    channel: str
    chat_id: int
    message_id: int
    date: datetime
    text: str


@dataclass(frozen=True)
class PostResult:
    success: bool
    code: str
    message: Optional[str]
    content_id: Optional[str]
    post_url: Optional[str]
    retryable: bool

from __future__ import annotations

from pathlib import Path
from string import Formatter
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .models import TelegramMessage

ALLOWED_TEMPLATE_FIELDS = {"text", "channel", "chat_id", "message_id", "date"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_api_id: int = Field(alias="TELEGRAM_API_ID")
    telegram_api_hash: str = Field(alias="TELEGRAM_API_HASH")
    telegram_session_path: Path = Field(alias="TELEGRAM_SESSION_PATH")
    telegram_channels_raw: str = Field(default="", alias="TELEGRAM_CHANNELS")
    telegram_channel_legacy: str = Field(default="", alias="TELEGRAM_CHANNEL")
    telegram_default_template: str = Field(default="{text}", alias="TELEGRAM_DEFAULT_TEMPLATE")
    telegram_channel_template_map: dict[str, str] = Field(default_factory=dict, alias="TELEGRAM_CHANNEL_TEMPLATE_MAP")

    binance_square_api_key: str = Field(alias="BINANCE_SQUARE_API_KEY")
    binance_client_type: str = Field(default="binanceSkill", alias="BINANCE_CLIENT_TYPE")
    binance_api_base: str = Field(default="https://www.binance.com", alias="BINANCE_API_BASE")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    sqlite_db_path: Path = Field(default=Path("./data/bridge.db"), alias="SQLITE_DB_PATH")
    max_retry_attempts: int = Field(default=3, alias="MAX_RETRY_ATTEMPTS")
    retry_base_seconds: int = Field(default=2, alias="RETRY_BASE_SECONDS")
    request_timeout_seconds: int = Field(default=15, alias="REQUEST_TIMEOUT_SECONDS")

    @field_validator("binance_square_api_key")
    @classmethod
    def validate_square_key(cls, value: str) -> str:
        if not value or value.strip() in {"", "your_api_key", "your_square_api_key"}:
            raise ValueError("BINANCE_SQUARE_API_KEY is missing or still placeholder.")
        return value.strip()

    @field_validator("telegram_channels_raw", "telegram_channel_legacy")
    @classmethod
    def validate_channel(cls, value: str) -> str:
        return value.strip()

    @field_validator("telegram_session_path", "sqlite_db_path")
    @classmethod
    def create_parent_dirs(cls, value: Path) -> Path:
        value.parent.mkdir(parents=True, exist_ok=True)
        return value

    @field_validator("telegram_default_template")
    @classmethod
    def validate_default_template(cls, value: str) -> str:
        return cls.validate_template(value)

    @field_validator("telegram_channel_template_map")
    @classmethod
    def validate_channel_template_map(cls, value: dict[str, str]) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for channel, template in value.items():
            normalized[cls.normalize_channel_key(channel)] = cls.validate_template(template)
        return normalized

    @property
    def masked_square_key(self) -> str:
        key = self.binance_square_api_key
        if len(key) <= 9:
            return "***"
        return f"{key[:5]}...{key[-4:]}"

    @property
    def telegram_channels(self) -> List[str]:
        source = self.telegram_channels_raw or self.telegram_channel_legacy
        channels = [item.strip() for item in source.split(",") if item.strip()]
        if not channels:
            raise ValueError("TELEGRAM_CHANNELS cannot be empty. Use comma-separated channels, e.g. @a,@b")
        return channels

    @staticmethod
    def normalize_channel_key(channel: str) -> str:
        clean_value = channel.strip()
        if clean_value.startswith("https://t.me/"):
            clean_value = clean_value.removeprefix("https://t.me/")
        if clean_value.startswith("http://t.me/"):
            clean_value = clean_value.removeprefix("http://t.me/")
        if clean_value.startswith("@"):
            clean_value = clean_value[1:]
        return clean_value.lower()

    @classmethod
    def validate_template(cls, template: str) -> str:
        clean_template = template.strip()
        if not clean_template:
            raise ValueError("Template cannot be empty.")
        if "{text}" not in clean_template:
            raise ValueError("Template must include {text}.")
        for _, field_name, _, _ in Formatter().parse(clean_template):
            if field_name and field_name not in ALLOWED_TEMPLATE_FIELDS:
                raise ValueError(f"Unsupported template field: {field_name}")
        return clean_template

    def resolve_post_template(self, channel: str) -> str:
        normalized_channel = self.normalize_channel_key(channel)
        return self.telegram_channel_template_map.get(normalized_channel, self.telegram_default_template)

    def render_post_text(self, message: TelegramMessage) -> str:
        template = self.resolve_post_template(message.channel)
        rendered = template.format(
            text=message.text.strip(),
            channel=message.channel,
            chat_id=message.chat_id,
            message_id=message.message_id,
            date=message.date.isoformat(),
        )
        return rendered.strip()

from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_api_id: int = Field(alias="TELEGRAM_API_ID")
    telegram_api_hash: str = Field(alias="TELEGRAM_API_HASH")
    telegram_session_path: Path = Field(alias="TELEGRAM_SESSION_PATH")
    telegram_channels_raw: str = Field(default="", alias="TELEGRAM_CHANNELS")
    telegram_channel_legacy: str = Field(default="", alias="TELEGRAM_CHANNEL")

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

from __future__ import annotations

import logging
from typing import Any, Dict

import httpx

from .config import Settings
from .models import PostResult

LOGGER = logging.getLogger(__name__)

RETRYABLE_CODES = {"10004"}
NON_RETRYABLE_CODES = {
    "10005",
    "10007",
    "20002",
    "20013",
    "20020",
    "20022",
    "20041",
    "30004",
    "30008",
    "220003",
    "220004",
    "220009",
    "220010",
    "220011",
    "2000001",
    "2000002",
}


class BinanceSquareClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.url = f"{settings.binance_api_base.rstrip('/')}/bapi/composite/v1/public/pgc/openApi/content/add"
        self.headers = {
            "X-Square-OpenAPI-Key": settings.binance_square_api_key,
            "Content-Type": "application/json",
            "clienttype": settings.binance_client_type,
        }

    async def post_text(self, text: str) -> PostResult:
        payload = {"bodyTextOnly": text}
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.post(self.url, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return self._to_result(data)
        except httpx.TimeoutException as exc:
            LOGGER.warning("Binance post timeout: %s", exc)
            return PostResult(False, "TIMEOUT", str(exc), None, None, True)
        except httpx.HTTPStatusError as exc:
            LOGGER.warning("Binance post HTTP error: %s", exc)
            return PostResult(False, "HTTP_ERROR", str(exc), None, None, True)
        except httpx.RequestError as exc:
            LOGGER.warning("Binance post request error: %s", exc)
            return PostResult(False, "NETWORK_ERROR", str(exc), None, None, True)

    def _to_result(self, payload: Dict[str, Any]) -> PostResult:
        code = str(payload.get("code", "UNKNOWN"))
        message = payload.get("message")
        result_data = payload.get("data") or {}
        content_id = result_data.get("id")

        if code == "000000":
            if content_id:
                post_url = f"https://www.binance.com/square/post/{content_id}"
                return PostResult(True, code, message, str(content_id), post_url, False)
            return PostResult(True, code, "Post may have succeeded but no id returned.", None, None, False)

        retryable = code in RETRYABLE_CODES
        if code not in RETRYABLE_CODES and code not in NON_RETRYABLE_CODES:
            retryable = True
        return PostResult(False, code, message, None, None, retryable)

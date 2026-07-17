"""Cliente sobre la API de Chatwoot con pooling y retry."""

import asyncio
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_DELAYS = [0.5, 1.0, 2.0]


class ChatwootClient:
    def __init__(self) -> None:
        self.base_url = settings.chatwoot_base_url.rstrip("/")
        self.account_id = settings.chatwoot_account_id
        self._headers = {
            "api_access_token": settings.chatwoot_bot_token,
            "Content-Type": "application/json",
        }
        self._client: httpx.AsyncClient | None = None

    async def init(self) -> None:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=15.0)

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    @property
    def _account_path(self) -> str:
        return f"{self.base_url}/api/v1/accounts/{self.account_id}"

    async def _request(self, method: str, url: str, **kwargs: object) -> httpx.Response:
        if self._client is None or self._client.is_closed:
            await self.init()
        assert self._client is not None

        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                response = await self._client.request(
                    method, url, headers=self._headers, **kwargs
                )
                if response.status_code >= 500 and attempt < _MAX_RETRIES - 1:
                    logger.warning(
                        "Chatwoot %s %s returned %s, retrying in %.1fs (%d/%d)",
                        method,
                        url,
                        response.status_code,
                        _RETRY_DELAYS[attempt],
                        attempt + 1,
                        _MAX_RETRIES,
                    )
                    await asyncio.sleep(_RETRY_DELAYS[attempt])
                    continue
                if response.status_code >= 400:
                    logger.error(
                        "Chatwoot %s %s error %s: %s",
                        method,
                        url,
                        response.status_code,
                        response.text[:500],
                    )
                response.raise_for_status()
                return response
            except httpx.TransportError as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES - 1:
                    logger.warning(
                        "Chatwoot %s %s transport error: %s, retrying in %.1fs (%d/%d)",
                        method,
                        url,
                        exc,
                        _RETRY_DELAYS[attempt],
                        attempt + 1,
                        _MAX_RETRIES,
                    )
                    await asyncio.sleep(_RETRY_DELAYS[attempt])
                    continue
                raise
        raise last_exc  # type: ignore[misc]

    async def filter_conversations(self, payload: dict) -> dict:
        url = f"{self._account_path}/conversations/filter"
        resp = await self._request("POST", url, json=payload)
        return resp.json()

    async def get_custom_attribute_definitions(self) -> dict:
        url = f"{self._account_path}/custom_attribute_definitions"
        resp = await self._request("GET", url)
        return resp.json()

    async def update_custom_attributes(
        self, conversation_id: int, attributes: dict
    ) -> dict:
        url = f"{self._account_path}/conversations/{conversation_id}/custom_attributes"
        resp = await self._request("POST", url, json={"custom_attributes": attributes})
        return resp.json()

    async def get_conversation(self, conversation_id: int) -> dict:
        url = f"{self._account_path}/conversations/{conversation_id}"
        resp = await self._request("GET", url)
        return resp.json()

    async def safe_update_custom_attributes(
        self, conversation_id: int, attributes: dict
    ) -> dict:
        try:
            conv = await self.get_conversation(conversation_id)
            existing = conv.get("custom_attributes") or {}
        except Exception:
            logger.warning(
                "Could not read existing attributes for conv %s, "
                "sending partial update",
                conversation_id,
            )
            return await self.update_custom_attributes(conversation_id, attributes)

        merged = {**existing, **attributes}
        return await self.update_custom_attributes(conversation_id, merged)


chatwoot_client = ChatwootClient()

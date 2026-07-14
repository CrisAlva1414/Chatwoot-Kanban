"""Cliente delgado sobre la API de Chatwoot."""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class ChatwootClient:
    def __init__(self) -> None:
        self.base_url = settings.chatwoot_base_url.rstrip("/")
        self.account_id = settings.chatwoot_account_id
        self._headers = {
            "api_access_token": settings.chatwoot_bot_token,
            "Content-Type": "application/json",
        }

    @property
    def _account_path(self) -> str:
        return f"{self.base_url}/api/v1/accounts/{self.account_id}"

    async def filter_conversations(self, payload: dict) -> dict:
        url = f"{self._account_path}/conversations/filter"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, headers=self._headers, json=payload)
            if response.status_code >= 400:
                logger.error(
                    "Chatwoot filter error %s: %s",
                    response.status_code,
                    response.text[:500],
                )
            response.raise_for_status()
            return response.json()

    async def get_custom_attribute_definitions(self) -> dict:
        url = f"{self._account_path}/custom_attribute_definitions"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=self._headers)
            if response.status_code >= 400:
                logger.error(
                    "Chatwoot definitions error %s: %s",
                    response.status_code,
                    response.text[:500],
                )
            response.raise_for_status()
            return response.json()

    async def update_custom_attributes(
        self, conversation_id: int, attributes: dict
    ) -> dict:
        url = f"{self._account_path}/conversations/{conversation_id}/custom_attributes"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url, headers=self._headers, json={"custom_attributes": attributes}
            )
            if response.status_code >= 400:
                logger.error(
                    "Chatwoot update attributes error %s: %s",
                    response.status_code,
                    response.text[:500],
                )
            response.raise_for_status()
            return response.json()


chatwoot_client = ChatwootClient()

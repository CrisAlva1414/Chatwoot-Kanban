"""
Cliente delgado sobre la API de Chatwoot.

Etapa 1: solo necesitamos LEER. El método de escritura
(`update_custom_attributes`) está acá pero no lo usamos todavía
hasta la Etapa 2 — lo dejamos listo para no reescribir el cliente después.
"""

import httpx

from app.config import settings


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
        """
        POST /api/v1/accounts/{account_id}/conversations/filter

        `payload` es el body crudo que espera Chatwoot, algo como:
        {
          "payload": [
            {
              "attribute_key": "tarea_estado",
              "filter_operator": "equal_to",
              "values": ["tarea_activa"],
              "query_operator": "AND"
            }
          ]
        }

        Devolvemos el JSON tal cual lo entrega Chatwoot, sin transformar nada
        todavía -- el objetivo de esta etapa es justamente ver ese shape real.
        """
        url = f"{self._account_path}/conversations/filter"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, headers=self._headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def get_custom_attribute_definitions(self) -> dict:
        """
        GET /api/v1/accounts/{account_id}/custom_attribute_definitions

        Útil para confirmar, antes de filtrar, que el attribute_key que
        vamos a usar (ej. 'tarea_estado', 'pipeline_stage') existe
        realmente y ver sus valores configurados.
        """
        url = f"{self._account_path}/custom_attribute_definitions"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=self._headers)
            response.raise_for_status()
            return response.json()

    async def update_custom_attributes(
        self, conversation_id: int, attributes: dict
    ) -> dict:
        """
        POST a custom attributes en una conversación de Chatwoot

        No se usa en la Etapa 1 -- lo dejamos listo para la Etapa 2.
        """
        url = f"{self._account_path}/conversations/{conversation_id}/custom_attributes"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url, headers=self._headers, json={"custom_attributes": attributes}
            )
            response.raise_for_status()
            return response.json()


chatwoot_client = ChatwootClient()

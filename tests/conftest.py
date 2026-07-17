import hashlib
import hmac
import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("CHATWOOT_BASE_URL", "https://test.chatwoot.com")
os.environ.setdefault("CHATWOOT_ACCOUNT_ID", "1")
os.environ.setdefault("CHATWOOT_BOT_TOKEN", "test-token")
os.environ.setdefault("CHATWOOT_WEBHOOK_SECRET", "test-secret")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")

from app.main import app

MOCK_ATTRIBUTE_DEFINITIONS = [
    {
        "id": 1,
        "attribute_display_name": "Pipeline 01 Etapas",
        "attribute_display_type": "list",
        "attribute_description": None,
        "attribute_key": "pipeline_01_etapas",
        "attribute_values": ["Potencial", "En evaluación", "Cerrado"],
        "attribute_model": "conversation_attribute",
        "default_value": None,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
]

MOCK_FILTER_RESPONSE = {
    "payload": {
        "conversations": [
            {
                "id": 101,
                "meta": {
                    "sender": {
                        "name": "Juan Pérez",
                        "thumbnail": "",
                    }
                },
                "messages": [
                    {"content": "Hola, necesito ayuda", "text": "Hola, necesito ayuda"}
                ],
                "updated_at": "2026-07-13T10:00:00Z",
                "custom_attributes": {
                    "kanban_view_fecha_termino": "2026-07-20T23:59:59.999Z"
                },
            },
            {
                "id": 102,
                "meta": {
                    "sender": {
                        "name": "María López",
                        "thumbnail": "",
                    }
                },
                "messages": [{"content": "Consulta sobre precio", "text": ""}],
                "updated_at": "2026-07-12T15:30:00Z",
                "custom_attributes": {},
            },
        ],
        "meta": {"count": 2},
    }
}


def _sign(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


@pytest.fixture()
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _patch_lifespan():
    with (
        patch("app.main.init_pool", new_callable=AsyncMock),
        patch("app.main.close_pool", new_callable=AsyncMock),
        patch("app.main.chatwoot_client") as mock_client,
    ):
        mock_client.init = AsyncMock()
        mock_client.close = AsyncMock()
        yield


@pytest.fixture()
def mock_chatwoot_ok():
    with (
        patch("app.routers.kanban.chatwoot_client") as mock_client,
        patch(
            "app.routers.kanban.get_tasks_for_conversations",
            new_callable=AsyncMock,
            return_value={},
        ),
    ):
        mock_client.get_custom_attribute_definitions = AsyncMock(
            return_value=MOCK_ATTRIBUTE_DEFINITIONS
        )
        mock_client.filter_conversations = AsyncMock(return_value=MOCK_FILTER_RESPONSE)
        mock_client.base_url = "https://test.chatwoot.com"
        yield mock_client


@pytest.fixture()
def mock_chatwoot_empty():
    with (
        patch("app.routers.kanban.chatwoot_client") as mock_client,
        patch(
            "app.routers.kanban.get_tasks_for_conversations",
            new_callable=AsyncMock,
            return_value={},
        ),
    ):
        mock_client.get_custom_attribute_definitions = AsyncMock(
            return_value=MOCK_ATTRIBUTE_DEFINITIONS
        )
        mock_client.filter_conversations = AsyncMock(
            return_value={"payload": {"conversations": [], "meta": {"count": 0}}}
        )
        mock_client.base_url = "https://test.chatwoot.com"
        yield mock_client


@pytest.fixture()
def mock_chatwoot_error():
    with patch("app.routers.kanban.chatwoot_client") as mock_client:
        mock_client.get_custom_attribute_definitions = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        mock_client.filter_conversations = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        mock_client.base_url = "https://test.chatwoot.com"
        yield mock_client


@pytest.fixture()
def mock_chatwoot_flat_response():
    with (
        patch("app.routers.kanban.chatwoot_client") as mock_client,
        patch(
            "app.routers.kanban.get_tasks_for_conversations",
            new_callable=AsyncMock,
            return_value={},
        ),
    ):
        mock_client.get_custom_attribute_definitions = AsyncMock(
            return_value=MOCK_ATTRIBUTE_DEFINITIONS
        )
        mock_client.filter_conversations = AsyncMock(
            return_value={
                "conversations": [
                    {
                        "id": 201,
                        "meta": {
                            "sender": {
                                "name": "Pedro Soto",
                                "thumbnail": "",
                            }
                        },
                        "messages": [],
                        "updated_at": "2026-07-10T08:00:00Z",
                        "custom_attributes": {
                            "kanban_view_fecha_termino": "2026-07-25T23:59:59.999Z"
                        },
                    }
                ]
            }
        )
        mock_client.base_url = "https://test.chatwoot.com"
        yield mock_client

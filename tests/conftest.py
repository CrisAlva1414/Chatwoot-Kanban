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
        "id": 6,
        "attribute_display_name": "Pipeline 01 Etapas",
        "attribute_display_type": "list",
        "attribute_description": None,
        "attribute_key": "pipeline_01_etapas",
        "attribute_values": ["Potencial", "En evaluación", "Cerrado"],
        "attribute_model": "contact_attribute",
        "default_value": None,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
]

MOCK_CONTACTS_FILTER_RESPONSE = {
    "meta": {"count": 2, "current_page": 1},
    "payload": [
        {
            "id": 101,
            "name": "Juan Pérez",
            "email": "juan@example.com",
            "phone_number": "+56912345678",
            "thumbnail": "",
            "custom_attributes": {
                "kanban_view_fecha_termino": "2026-07-20T23:59:59.999Z"
            },
            "last_activity_at": 1784000000,
        },
        {
            "id": 102,
            "name": "María López",
            "email": "maria@example.com",
            "phone_number": "+56987654321",
            "thumbnail": "",
            "custom_attributes": {},
            "last_activity_at": 1783900000,
        },
    ],
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


@pytest.fixture(autouse=True)
def _clear_board_cache():
    from app.routers.kanban import _board_cache

    _board_cache.clear()
    yield
    _board_cache.clear()


@pytest.fixture()
def mock_chatwoot_ok():
    with (
        patch("app.routers.kanban.chatwoot_client") as mock_client,
        patch(
            "app.routers.kanban.get_tasks_for_contacts",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "app.routers.kanban.batch_sync_tasks_from_chatwoot",
            new_callable=AsyncMock,
            return_value={"updated": 0, "created": 0, "closed": 0},
        ),
    ):
        mock_client.get_custom_attribute_definitions = AsyncMock(
            return_value=MOCK_ATTRIBUTE_DEFINITIONS
        )
        mock_client.filter_contacts = AsyncMock(
            return_value=MOCK_CONTACTS_FILTER_RESPONSE
        )
        mock_client.base_url = "https://test.chatwoot.com"
        yield mock_client


@pytest.fixture()
def mock_chatwoot_empty():
    with (
        patch("app.routers.kanban.chatwoot_client") as mock_client,
        patch(
            "app.routers.kanban.get_tasks_for_contacts",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "app.routers.kanban.batch_sync_tasks_from_chatwoot",
            new_callable=AsyncMock,
            return_value={"updated": 0, "created": 0, "closed": 0},
        ),
    ):
        mock_client.get_custom_attribute_definitions = AsyncMock(
            return_value=MOCK_ATTRIBUTE_DEFINITIONS
        )
        mock_client.filter_contacts = AsyncMock(
            return_value={"payload": [], "meta": {"count": 0, "current_page": 1}}
        )
        mock_client.base_url = "https://test.chatwoot.com"
        yield mock_client


@pytest.fixture()
def mock_chatwoot_error():
    with patch("app.routers.kanban.chatwoot_client") as mock_client:
        mock_client.get_custom_attribute_definitions = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        mock_client.filter_contacts = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        mock_client.base_url = "https://test.chatwoot.com"
        yield mock_client


@pytest.fixture()
def mock_chatwoot_flat_response():
    with (
        patch("app.routers.kanban.chatwoot_client") as mock_client,
        patch(
            "app.routers.kanban.get_tasks_for_contacts",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "app.routers.kanban.batch_sync_tasks_from_chatwoot",
            new_callable=AsyncMock,
            return_value={"updated": 0, "created": 0, "closed": 0},
        ),
    ):
        mock_client.get_custom_attribute_definitions = AsyncMock(
            return_value=MOCK_ATTRIBUTE_DEFINITIONS
        )
        mock_client.filter_contacts = AsyncMock(
            return_value={
                "payload": [
                    {
                        "id": 201,
                        "name": "Pedro Soto",
                        "email": "pedro@example.com",
                        "phone_number": "",
                        "thumbnail": "",
                        "custom_attributes": {
                            "kanban_view_fecha_termino": "2026-07-25T23:59:59.999Z"
                        },
                        "last_activity_at": 1783800000,
                    }
                ],
                "meta": {"count": 1, "current_page": 1},
            }
        )
        mock_client.base_url = "https://test.chatwoot.com"
        yield mock_client

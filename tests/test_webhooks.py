from unittest.mock import AsyncMock, patch

from tests.conftest import _sign


def test_webhook_valid_signature(client):
    body = (
        b'{"id": "evt-001", "event": "conversation_updated", "conversation": {"id": 1}}'
    )
    sig = _sign(body, "test-secret")

    mock_pool = AsyncMock()
    mock_pool.fetchrow = AsyncMock(return_value=None)
    mock_pool.execute = AsyncMock()

    with patch("app.routers.webhooks.get_pool", return_value=mock_pool):
        response = client.post(
            "/webhooks/conversation-updated",
            content=body,
            headers={
                "x-chatwoot-signature": sig,
                "content-type": "application/json",
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_webhook_invalid_signature(client):
    body = b'{"id": "evt-002", "event": "conversation_updated"}'

    response = client.post(
        "/webhooks/conversation-updated",
        content=body,
        headers={
            "x-chatwoot-signature": "invalid-sig",
            "content-type": "application/json",
        },
    )
    assert response.status_code == 401


def test_webhook_missing_event_id(client):
    body = b'{"event": "conversation_updated", "conversation": {"id": 1}}'
    sig = _sign(body, "test-secret")

    response = client.post(
        "/webhooks/conversation-updated",
        content=body,
        headers={
            "x-chatwoot-signature": sig,
            "content-type": "application/json",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


def test_webhook_duplicate_event(client):
    body = (
        b'{"id": "evt-003", "event": "conversation_updated", "conversation": {"id": 1}}'
    )
    sig = _sign(body, "test-secret")

    mock_pool = AsyncMock()
    mock_pool.fetchrow = AsyncMock(return_value={"id": 1})

    with patch("app.routers.webhooks.get_pool", return_value=mock_pool):
        response = client.post(
            "/webhooks/conversation-updated",
            content=body,
            headers={
                "x-chatwoot-signature": sig,
                "content-type": "application/json",
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "duplicate"

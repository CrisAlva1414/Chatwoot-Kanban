from unittest.mock import AsyncMock, patch


def test_kanban_config_returns_columns(client, mock_chatwoot_ok):
    response = client.get("/api/kanban/config")
    assert response.status_code == 200
    data = response.json()
    assert data["columns"] == ["Potencial", "En evaluación", "Cerrado"]
    assert data["chatwoot_url"] == "https://test.chatwoot.com"


def test_kanban_config_no_pipeline_attribute(client):
    with patch("app.routers.kanban.chatwoot_client") as mock_client:
        mock_client.get_custom_attribute_definitions = AsyncMock(
            return_value=[{"attribute_key": "other_attr", "attribute_values": []}]
        )
        mock_client.base_url = "https://test.chatwoot.com"

        response = client.get("/api/kanban/config")
        assert response.status_code == 200
        assert response.json()["columns"] == []


def test_kanban_config_chatwoot_error(client, mock_chatwoot_error):
    response = client.get("/api/kanban/config")
    assert response.status_code == 502


def test_kanban_board_all_stages(client, mock_chatwoot_ok):
    response = client.get("/api/kanban/board")
    assert response.status_code == 200
    data = response.json()
    assert len(data["columns"]) == 3
    assert data["columns"][0]["stage"] == "Potencial"
    assert len(data["columns"][0]["conversations"]) == 2


def test_kanban_board_single_stage(client, mock_chatwoot_ok):
    response = client.get("/api/kanban/board?stage=Potencial")
    assert response.status_code == 200
    data = response.json()
    assert len(data["columns"]) == 1
    assert data["columns"][0]["stage"] == "Potencial"


def test_kanban_board_normalizes_conversations(client, mock_chatwoot_ok):
    response = client.get("/api/kanban/board?stage=Potencial")
    card = response.json()["columns"][0]["conversations"][0]
    assert card["id"] == 101
    assert card["contact_name"] == "Juan Pérez"
    assert card["last_message"] == "Hola, necesito ayuda"
    assert card["custom_attributes"] == {"tarea_estado": "tarea_activa"}


def test_kanban_board_handles_flat_response(client, mock_chatwoot_flat_response):
    response = client.get("/api/kanban/board?stage=Potencial")
    assert response.status_code == 200
    cards = response.json()["columns"][0]["conversations"]
    assert len(cards) == 1
    assert cards[0]["id"] == 201


def test_kanban_board_empty_stage(client, mock_chatwoot_empty):
    response = client.get("/api/kanban/board?stage=Potencial")
    assert response.status_code == 200
    assert response.json()["columns"][0]["conversations"] == []


def test_kanban_board_chatwoot_error(client, mock_chatwoot_error):
    response = client.get("/api/kanban/board")
    assert response.status_code == 502


def test_debug_status_ok(client, mock_chatwoot_ok):
    response = client.get("/api/kanban/debug-status")
    assert response.status_code == 200
    data = response.json()
    assert data["checks"]["chatwoot_connection"] == "ok"
    assert data["checks"]["pipeline_attribute"] == "found"
    assert data["checks"]["pipeline_stages"] == [
        "Potencial",
        "En evaluación",
        "Cerrado",
    ]


def test_debug_status_chatwoot_error(client, mock_chatwoot_error):
    response = client.get("/api/kanban/debug-status")
    assert response.status_code == 200
    data = response.json()
    assert data["checks"]["chatwoot_connection"] == "failed"
    assert "error" in data["checks"]


def test_debug_raw_returns_parsed(client, mock_chatwoot_ok):
    response = client.get("/api/kanban/debug-raw?stage=Potencial")
    assert response.status_code == 200
    data = response.json()
    assert "raw" in data
    assert "parsed_conversations" in data
    assert len(data["parsed_conversations"]) == 2

from unittest.mock import AsyncMock, patch


def test_kanban_config_returns_columns(client, mock_chatwoot_ok):
    response = client.get("/kanban/config")
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

        response = client.get("/kanban/config")
        assert response.status_code == 200
        assert response.json()["columns"] == []


def test_kanban_config_chatwoot_error(client, mock_chatwoot_error):
    response = client.get("/kanban/config")
    assert response.status_code == 502


def test_kanban_board_all_stages(client, mock_chatwoot_ok):
    response = client.get("/kanban/board")
    assert response.status_code == 200
    data = response.json()
    assert len(data["columns"]) == 3
    assert data["columns"][0]["stage"] == "Potencial"
    assert len(data["columns"][0]["contacts"]) == 2


def test_kanban_board_single_stage(client, mock_chatwoot_ok):
    response = client.get("/kanban/board?stage=Potencial")
    assert response.status_code == 200
    data = response.json()
    assert len(data["columns"]) == 1
    assert data["columns"][0]["stage"] == "Potencial"


def test_kanban_board_normalizes_contacts(client, mock_chatwoot_ok):
    response = client.get("/kanban/board?stage=Potencial")
    card = response.json()["columns"][0]["contacts"][0]
    assert card["id"] == 101
    assert card["contact_name"] == "Juan Pérez"
    expected_attrs = {"kanban_view_fecha_termino": "2026-07-20T23:59:59.999Z"}
    assert card["custom_attributes"] == expected_attrs


def test_kanban_board_handles_flat_response(client, mock_chatwoot_flat_response):
    response = client.get("/kanban/board?stage=Potencial")
    assert response.status_code == 200
    cards = response.json()["columns"][0]["contacts"]
    assert len(cards) == 1
    assert cards[0]["id"] == 201


def test_kanban_board_empty_stage(client, mock_chatwoot_empty):
    response = client.get("/kanban/board?stage=Potencial")
    assert response.status_code == 200
    assert response.json()["columns"][0]["contacts"] == []


def test_kanban_board_chatwoot_error(client, mock_chatwoot_error):
    response = client.get("/kanban/board")
    assert response.status_code == 502


def test_debug_status_ok(client, mock_chatwoot_ok):
    response = client.get("/kanban/debug-status")
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
    response = client.get("/kanban/debug-status")
    assert response.status_code == 200
    data = response.json()
    assert data["checks"]["chatwoot_connection"] == "failed"
    assert "error" in data["checks"]


def test_debug_raw_returns_parsed(client, mock_chatwoot_ok):
    response = client.get("/kanban/debug-raw?stage=Potencial")
    assert response.status_code == 200
    data = response.json()
    assert "raw" in data
    assert "parsed_contacts" in data
    assert len(data["parsed_contacts"]) == 2


def test_move_stage_ok(client, mock_chatwoot_ok):
    with (
        patch("app.routers.kanban.get_or_create_agent") as mock_agent,
        patch("app.routers.kanban.write_audit_log", new_callable=AsyncMock),
    ):
        mock_agent.return_value = {
            "id": 1,
            "email": "bot@i-labs.cl",
            "nombre": "Bot",
        }
        mock_chatwoot_ok.safe_update_contact_custom_attributes = AsyncMock(
            return_value={"payload": {"id": 101}}
        )
        response = client.patch(
            "/kanban/board/101/stage",
            json={"stage": "Potencial"},
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True
        assert response.json()["stage"] == "Potencial"


def test_move_stage_invalid(client, mock_chatwoot_ok):
    with patch("app.routers.kanban.get_or_create_agent") as mock_agent:
        mock_agent.return_value = {
            "id": 1,
            "email": "bot@i-labs.cl",
            "nombre": "Bot",
        }
        response = client.patch(
            "/kanban/board/101/stage",
            json={"stage": "EtapaInvalida"},
        )
        assert response.status_code == 400


def test_move_stage_chatwoot_error(client, mock_chatwoot_ok):
    with (
        patch("app.routers.kanban.get_or_create_agent") as mock_agent,
        patch("app.routers.kanban.write_audit_log", new_callable=AsyncMock),
    ):
        mock_agent.return_value = {
            "id": 1,
            "email": "bot@i-labs.cl",
            "nombre": "Bot",
        }
        mock_chatwoot_ok.safe_update_contact_custom_attributes = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        response = client.patch(
            "/kanban/board/101/stage",
            json={"stage": "Potencial"},
        )
        assert response.status_code == 502


def test_create_task(client, mock_chatwoot_ok):
    with (
        patch("app.routers.kanban.get_or_create_agent") as mock_agent,
        patch(
            "app.routers.kanban.get_active_task",
            new_callable=AsyncMock,
        ) as mock_active,
        patch(
            "app.routers.kanban.upsert_task",
            new_callable=AsyncMock,
        ) as mock_upsert,
        patch(
            "app.routers.kanban.write_audit_log",
            new_callable=AsyncMock,
        ),
    ):
        mock_agent.return_value = {
            "id": 1,
            "email": "bot@i-labs.cl",
            "nombre": "Bot",
        }
        mock_active.return_value = None
        mock_upsert.return_value = {"id": 10, "action": "created"}
        mock_chatwoot_ok.safe_update_contact_custom_attributes = AsyncMock(
            return_value={"payload": {"id": 101}}
        )
        response = client.post(
            "/kanban/tasks",
            json={
                "contact_id": 101,
                "mensaje": "Enviar propuesta",
                "fecha_vencimiento": "2026-07-20",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["action"] == "created"
        assert data["task_id"] == 10


def test_create_task_overwrite(client, mock_chatwoot_ok):
    with (
        patch("app.routers.kanban.get_or_create_agent") as mock_agent,
        patch(
            "app.routers.kanban.get_active_task",
            new_callable=AsyncMock,
        ) as mock_active,
        patch(
            "app.routers.kanban.upsert_task",
            new_callable=AsyncMock,
        ) as mock_upsert,
        patch(
            "app.routers.kanban.write_audit_log",
            new_callable=AsyncMock,
        ),
    ):
        mock_agent.return_value = {
            "id": 1,
            "email": "bot@i-labs.cl",
            "nombre": "Bot",
        }
        mock_active.return_value = {
            "id": 5,
            "mensaje": "Tarea anterior",
            "fecha_vencimiento": "2026-07-15",
            "creado_por_nombre": "María",
        }
        mock_upsert.return_value = {"id": 5, "action": "updated"}
        mock_chatwoot_ok.safe_update_contact_custom_attributes = AsyncMock(
            return_value={"payload": {"id": 101}}
        )
        response = client.post(
            "/kanban/tasks",
            json={
                "contact_id": 101,
                "mensaje": "Nueva tarea",
                "fecha_vencimiento": "2026-07-25",
            },
        )
        assert response.status_code == 200
        assert response.json()["action"] == "updated"


def test_close_task(client, mock_chatwoot_ok):
    with (
        patch("app.routers.kanban.get_or_create_agent") as mock_agent,
        patch("app.routers.kanban.close_task", new_callable=AsyncMock) as mock_close,
        patch("app.routers.kanban.write_audit_log", new_callable=AsyncMock),
    ):
        mock_agent.return_value = {
            "id": 1,
            "email": "bot@i-labs.cl",
            "nombre": "Bot",
        }
        mock_close.return_value = {
            "action": "closed",
            "previous": {
                "contact_id": 101,
                "conversation_id": 500,
                "estado": "tarea_activa",
            },
        }
        mock_chatwoot_ok.safe_update_contact_custom_attributes = AsyncMock(
            return_value={"payload": {"id": 101}}
        )
        response = client.patch("/kanban/tasks/10/close")
        assert response.status_code == 200
        assert response.json()["ok"] is True


def test_close_task_not_found(client, mock_chatwoot_ok):
    with (
        patch("app.routers.kanban.get_or_create_agent") as mock_agent,
        patch("app.routers.kanban.close_task", new_callable=AsyncMock) as mock_close,
    ):
        mock_agent.return_value = {
            "id": 1,
            "email": "bot@i-labs.cl",
            "nombre": "Bot",
        }
        mock_close.return_value = {"error": "not_found"}
        response = client.patch("/kanban/tasks/999/close")
        assert response.status_code == 404


def test_get_tasks(client):
    with patch(
        "app.routers.kanban.get_active_task", new_callable=AsyncMock
    ) as mock_task:
        mock_task.return_value = None
        response = client.get("/kanban/tasks?contact_id=101")
        assert response.status_code == 200
        assert response.json()["task"] is None


def test_stats_endpoint(client):
    with patch(
        "app.routers.kanban.get_agent_stats", new_callable=AsyncMock
    ) as mock_stats:
        mock_stats.return_value = []
        response = client.get("/kanban/stats")
        assert response.status_code == 200
        assert response.json()["agents"] == []


def test_stats_history_endpoint(client):
    with patch(
        "app.routers.kanban.get_audit_history", new_callable=AsyncMock
    ) as mock_history:
        mock_history.return_value = []
        response = client.get("/kanban/stats/history")
        assert response.status_code == 200
        assert response.json()["history"] == []


def test_cron_tick_endpoint(client):
    with (
        patch("app.routers.kanban.get_or_create_agent") as mock_agent,
        patch("app.routers.kanban.cron_tick", new_callable=AsyncMock) as mock_cron,
        patch("app.routers.kanban.write_audit_log", new_callable=AsyncMock),
    ):
        mock_agent.return_value = {
            "id": 1,
            "email": "bot@i-labs.cl",
            "nombre": "Bot",
        }
        mock_cron.return_value = {
            "hoy": 0,
            "vencida": 0,
            "synced": 0,
            "failed": 0,
        }
        response = client.post("/kanban/cron/tick")
        assert response.status_code == 200
        assert response.json()["ok"] is True
        assert "transitions" in response.json()


def test_dashboard_page(client):
    response = client.get("/kanban/dashboard")
    assert response.status_code == 200
    assert "Volver al Kanban" in response.text

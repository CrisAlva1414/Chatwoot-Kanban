import logging
import math
from datetime import date
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.chatwoot_client import chatwoot_client
from app.database import (
    close_task,
    cron_tick,
    edit_task,
    get_active_task,
    get_agent_stats,
    get_audit_history,
    get_or_create_agent,
    get_tasks_for_conversations,
    sync_task_from_chatwoot,
    upsert_task,
    write_audit_log,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kanban", tags=["kanban"])

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

PIPELINE_ATTR_KEY = "pipeline_01_etapas"

TASK_MSG_ATTR_KEY = "kanban_view_mensaje"
TASK_DATE_ATTR_KEY = "kanban_view_fecha_termino"


class MoveStageRequest(BaseModel):
    stage: str


class CreateTaskRequest(BaseModel):
    conversation_id: int
    mensaje: str
    fecha_vencimiento: date


class EditTaskRequest(BaseModel):
    mensaje: str
    fecha_vencimiento: date


async def _get_actor(request: Request) -> tuple[int, str, str]:
    email = request.headers.get("cf-access-authenticated-user-email", "")
    if not email:
        email = "bot@i-labs.cl"
        name = "Bot (sin auth)"
    else:
        name = email.split("@")[0].replace(".", " ").title()
    agent = await get_or_create_agent(email, name)
    return agent["id"], agent["nombre"], agent["email"]


@router.get("", response_class=HTMLResponse)
async def kanban_page():
    html = TEMPLATE_DIR / "kanban.html"
    if not html.exists():
        raise HTTPException(status_code=404, detail="template not found")
    return HTMLResponse(html.read_text())


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    html = TEMPLATE_DIR / "dashboard.html"
    if not html.exists():
        raise HTTPException(status_code=404, detail="template not found")
    return HTMLResponse(html.read_text())


@router.patch("/board/{conversation_id}/stage")
async def move_stage(conversation_id: int, body: MoveStageRequest, request: Request):
    actor_id, actor_name, actor_email = await _get_actor(request)

    definitions = await chatwoot_client.get_custom_attribute_definitions()
    pipeline_attr = _find_pipeline_attribute(definitions)
    valid_stages = pipeline_attr.get("attribute_values", []) if pipeline_attr else []
    if valid_stages and body.stage not in valid_stages:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stage '{body.stage}'. Valid: {valid_stages}",
        )

    try:
        await write_audit_log(
            conversation_id=conversation_id,
            contact_id=None,
            actor_agent_id=actor_id,
            actor_name=actor_name,
            action="stage_change",
            previous_state={"stage_from": "unknown"},
            new_state={"stage_to": body.stage},
        )
        await chatwoot_client.safe_update_custom_attributes(
            conversation_id, {PIPELINE_ATTR_KEY: body.stage}
        )
        await write_audit_log(
            conversation_id=conversation_id,
            contact_id=None,
            actor_agent_id=actor_id,
            actor_name=actor_name,
            action="stage_change",
            previous_state=None,
            new_state={"stage_to": body.stage},
            chatwoot_call_ok=True,
        )
        return {"ok": True, "stage": body.stage}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to move conversation %s: %s", conversation_id, exc)
        await write_audit_log(
            conversation_id=conversation_id,
            contact_id=None,
            actor_agent_id=actor_id,
            actor_name=actor_name,
            action="stage_change",
            previous_state=None,
            new_state={"stage_to": body.stage},
            chatwoot_call_ok=False,
        )
        raise HTTPException(
            status_code=502, detail=f"Chatwoot API error: {exc}"
        ) from exc


@router.post("/tasks")
async def create_task(body: CreateTaskRequest, request: Request):
    actor_id, actor_name, actor_email = await _get_actor(request)

    existing = await get_active_task(body.conversation_id)
    action_label = "updated" if existing else "created"
    previous = None
    if existing:
        previous = {
            "mensaje": existing["mensaje"],
            "fecha_vencimiento": str(existing["fecha_vencimiento"]),
            "creado_por": existing["creado_por_nombre"],
        }

    result = await upsert_task(
        conversation_id=body.conversation_id,
        mensaje=body.mensaje,
        fecha_vencimiento=body.fecha_vencimiento,
        actor_agent_id=actor_id,
    )

    chatwoot_ok = True
    try:
        fecha_iso = body.fecha_vencimiento.isoformat() + "T23:59:59.999Z"
        attrs = {
            TASK_MSG_ATTR_KEY: body.mensaje,
            TASK_DATE_ATTR_KEY: fecha_iso,
        }
        await chatwoot_client.safe_update_custom_attributes(body.conversation_id, attrs)
    except Exception as exc:
        logger.error(
            "Chatwoot sync failed for task on conv %s: %s",
            body.conversation_id,
            exc,
        )
        chatwoot_ok = False

    audit_action = "task_overwritten" if existing else "create"
    await write_audit_log(
        conversation_id=body.conversation_id,
        contact_id=None,
        actor_agent_id=actor_id,
        actor_name=actor_name,
        action=audit_action,
        previous_state=previous,
        new_state={
            "mensaje": body.mensaje,
            "fecha_vencimiento": body.fecha_vencimiento.isoformat(),
        },
        chatwoot_call_ok=chatwoot_ok,
    )

    return {
        "ok": True,
        "action": action_label,
        "task_id": result["id"],
        "chatwoot_synced": chatwoot_ok,
    }


@router.patch("/tasks/{task_id}")
async def update_task_endpoint(task_id: int, body: EditTaskRequest, request: Request):
    actor_id, actor_name, _ = await _get_actor(request)

    result = await edit_task(
        task_id,
        mensaje=body.mensaje,
        fecha_vencimiento=body.fecha_vencimiento,
    )
    if result.get("error") == "not_found":
        raise HTTPException(status_code=404, detail="Task not found")

    previous = result.get("previous", {})
    chatwoot_ok = True
    try:
        conv_id = previous.get("conversation_id")
        if conv_id:
            fecha_iso = body.fecha_vencimiento.isoformat() + "T23:59:59.999Z"
            attrs = {
                TASK_MSG_ATTR_KEY: body.mensaje,
                TASK_DATE_ATTR_KEY: fecha_iso,
            }
            await chatwoot_client.safe_update_custom_attributes(conv_id, attrs)
    except Exception as exc:
        logger.error("Chatwoot sync failed for task %s: %s", task_id, exc)
        chatwoot_ok = False

    await write_audit_log(
        conversation_id=previous.get("conversation_id", 0),
        contact_id=None,
        actor_agent_id=actor_id,
        actor_name=actor_name,
        action="edit",
        previous_state={
            "mensaje": previous.get("mensaje"),
            "fecha_vencimiento": str(previous.get("fecha_vencimiento", "")),
        },
        new_state={
            "mensaje": body.mensaje,
            "fecha_vencimiento": body.fecha_vencimiento.isoformat(),
        },
        chatwoot_call_ok=chatwoot_ok,
    )

    return {"ok": True, "task_id": task_id, "chatwoot_synced": chatwoot_ok}


@router.patch("/tasks/{task_id}/close")
async def close_task_endpoint(task_id: int, request: Request):
    actor_id, actor_name, _ = await _get_actor(request)

    result = await close_task(task_id, cerrado_por=actor_id)
    if result.get("error") == "not_found":
        raise HTTPException(status_code=404, detail="Task not found")
    if result.get("error") == "already_closed":
        raise HTTPException(status_code=409, detail="Task is already closed")

    previous = result.get("previous", {})
    chatwoot_ok = True
    try:
        conv_id = previous.get("conversation_id")
        if conv_id:
            await chatwoot_client.safe_update_custom_attributes(
                conv_id, {TASK_MSG_ATTR_KEY: "", TASK_DATE_ATTR_KEY: ""}
            )
    except Exception as exc:
        logger.error("Chatwoot sync failed closing task %s: %s", task_id, exc)
        chatwoot_ok = False

    await write_audit_log(
        conversation_id=previous.get("conversation_id", 0),
        contact_id=None,
        actor_agent_id=actor_id,
        actor_name=actor_name,
        action="close",
        previous_state={"estado": previous.get("estado")},
        new_state={"estado": "tarea_cerrada"},
        chatwoot_call_ok=chatwoot_ok,
    )

    return {"ok": True, "task_id": task_id, "chatwoot_synced": chatwoot_ok}


@router.get("/tasks")
async def get_tasks(conversation_id: int | None = None):
    if conversation_id:
        task = await get_active_task(conversation_id)
        return {"task": task}
    return {"tasks": []}


@router.post("/cron/tick")
async def kanban_cron_tick(request: Request):
    actor_id, actor_name, _ = await _get_actor(request)
    try:
        result = await cron_tick()
        await write_audit_log(
            conversation_id=0,
            contact_id=None,
            actor_agent_id=actor_id,
            actor_name=actor_name,
            action="cron_tick",
            previous_state=None,
            new_state=result,
            source="cron",
        )
        return {"ok": True, "transitions": result}
    except Exception as exc:
        logger.error("Cron tick failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Cron tick failed: {exc}") from exc


@router.get("/stats")
async def kanban_stats():
    stats = await get_agent_stats()
    return {"agents": stats}


@router.get("/stats/history")
async def kanban_stats_history(limit: int = 50):
    history = await get_audit_history(limit)
    return {"history": history}


@router.get("/config")
async def kanban_config():
    try:
        definitions = await chatwoot_client.get_custom_attribute_definitions()
    except Exception as exc:
        logger.error("Failed to fetch attribute definitions: %s", exc)
        raise HTTPException(
            status_code=502, detail=f"Chatwoot API error: {exc}"
        ) from exc

    pipeline_attr = _find_pipeline_attribute(definitions)
    if not pipeline_attr:
        return {
            "columns": [],
            "chatwoot_url": chatwoot_client.base_url,
            "chatwoot_account_id": chatwoot_client.account_id,
        }

    return {
        "columns": pipeline_attr.get("attribute_values", []),
        "chatwoot_url": chatwoot_client.base_url,
        "chatwoot_account_id": chatwoot_client.account_id,
    }


@router.get("/board")
async def kanban_board(stage: str | None = None):
    try:
        definitions = await chatwoot_client.get_custom_attribute_definitions()
    except Exception as exc:
        logger.error("Failed to fetch attribute definitions: %s", exc)
        raise HTTPException(
            status_code=502, detail=f"Chatwoot API error: {exc}"
        ) from exc

    pipeline_attr = _find_pipeline_attribute(definitions)
    if not pipeline_attr:
        return {
            "columns": [],
            "chatwoot_url": chatwoot_client.base_url,
            "chatwoot_account_id": chatwoot_client.account_id,
        }

    stages = pipeline_attr.get("attribute_values", [])
    target_stages = [stage] if stage else stages

    columns = []
    for s in target_stages:
        payload = {
            "payload": [
                {
                    "attribute_key": PIPELINE_ATTR_KEY,
                    "filter_operator": "equal_to",
                    "values": [s],
                    "query_operator": None,
                }
            ]
        }
        all_cards = []
        page = 1
        try:
            while True:
                resp = await chatwoot_client.filter_conversations(payload, page=page)
                cards = _parse_conversations(resp)
                all_cards.extend(cards)
                meta = _extract_meta(resp)
                all_count = meta.get("all_count", 0)
                page_size = 25
                total_pages = (
                    max(1, math.ceil(all_count / page_size)) if all_count else 1
                )
                if page >= total_pages:
                    break
                page += 1

            for card in all_cards:
                await sync_task_from_chatwoot(
                    card["id"], card.get("custom_attributes") or {}
                )

            conv_ids = [c["id"] for c in all_cards if c.get("id")]
            tasks_map = await get_tasks_for_conversations(conv_ids)
            for card in all_cards:
                task = tasks_map.get(card["id"])
                if task:
                    card["task"] = {
                        "id": task["id"],
                        "estado": task["estado"],
                        "mensaje": task["mensaje"],
                        "fecha_vencimiento": str(task["fecha_vencimiento"]),
                        "creado_por": task["creado_por_nombre"],
                    }
            columns.append({"stage": s, "conversations": all_cards})
        except Exception as exc:
            logger.error("Failed to filter conversations for stage '%s': %s", s, exc)
            raise HTTPException(
                status_code=502,
                detail=f"Chatwoot API error filtering stage '{s}': {exc}",
            ) from exc

    return {
        "columns": columns,
        "chatwoot_url": chatwoot_client.base_url,
        "chatwoot_account_id": chatwoot_client.account_id,
    }


@router.get("/debug-status")
async def kanban_debug_status():
    status = {"chatwoot_url": chatwoot_client.base_url, "checks": {}}

    try:
        definitions = await chatwoot_client.get_custom_attribute_definitions()
        status["checks"]["chatwoot_connection"] = "ok"
        status["checks"]["attribute_definitions_count"] = len(definitions)

        pipeline_attr = _find_pipeline_attribute(definitions)
        if pipeline_attr:
            status["checks"]["pipeline_attribute"] = "found"
            status["checks"]["pipeline_attribute_key"] = pipeline_attr.get(
                "attribute_key"
            )
            status["checks"]["pipeline_stages"] = pipeline_attr.get(
                "attribute_values", []
            )
        else:
            status["checks"]["pipeline_attribute"] = "not_found"
            status["checks"]["available_keys"] = [
                d.get("attribute_key") for d in definitions
            ]
    except Exception as exc:
        status["checks"]["chatwoot_connection"] = "failed"
        status["checks"]["error"] = str(exc)

    return status


@router.get("/debug-raw")
async def kanban_debug_raw(stage: str = "Potencial"):
    payload = {
        "payload": [
            {
                "attribute_key": PIPELINE_ATTR_KEY,
                "filter_operator": "equal_to",
                "values": [stage],
                "query_operator": None,
            }
        ]
    }
    try:
        resp = await chatwoot_client.filter_conversations(payload)
        return {
            "stage": stage,
            "raw": resp,
            "top_level_keys": list(resp.keys())
            if isinstance(resp, dict)
            else type(resp).__name__,
            "parsed_conversations": _parse_conversations(resp),
        }
    except Exception as exc:
        logger.error("Debug raw failed for stage '%s': %s", stage, exc)
        return {"error": str(exc)}


def _find_pipeline_attribute(definitions: list) -> dict | None:
    for d in definitions:
        if d.get("attribute_key") == PIPELINE_ATTR_KEY:
            return d
    return None


def _extract_meta(resp: dict) -> dict:
    meta = resp.get("meta") or {}
    if meta:
        return meta
    for key in ("payload", "data"):
        val = resp.get(key)
        if isinstance(val, dict):
            meta = val.get("meta") or {}
            if meta:
                return meta
    return {}


def _parse_conversations(resp: dict | list) -> list:
    raw = _extract_conversation_list(resp)
    return [_normalize_conversation(c) for c in raw]


def _extract_conversation_list(resp: dict | list) -> list:
    if isinstance(resp, list):
        return resp
    if not isinstance(resp, dict):
        return []

    for key in ("conversations", "data", "payload"):
        val = resp.get(key)
        if isinstance(val, list):
            return val
        if isinstance(val, dict):
            return _extract_conversation_list(val)

    return []


def _normalize_conversation(conv: dict) -> dict:
    sender = (conv.get("meta") or {}).get("sender") or {}
    messages = conv.get("messages") or []
    last_msg = messages[-1] if messages else {}

    return {
        "id": conv.get("id"),
        "contact_name": sender.get("name") or "",
        "thumbnail": sender.get("thumbnail") or "",
        "last_message": last_msg.get("content") or "",
        "updated_at": conv.get("updated_at") or "",
        "custom_attributes": conv.get("custom_attributes") or {},
    }

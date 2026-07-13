import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from app.chatwoot_client import chatwoot_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["kanban"])

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

PIPELINE_ATTR_KEY = "pipeline_01_etapas"


@router.get("/kanban", response_class=HTMLResponse)
async def kanban_page():
    html = TEMPLATE_DIR / "kanban.html"
    if not html.exists():
        raise HTTPException(status_code=404, detail="template not found")
    return HTMLResponse(html.read_text())


@router.get("/api/kanban/config")
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
        return {"columns": [], "chatwoot_url": chatwoot_client.base_url}

    return {
        "columns": pipeline_attr.get("attribute_values", []),
        "chatwoot_url": chatwoot_client.base_url,
    }


@router.get("/api/kanban/board")
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
        return {"columns": [], "chatwoot_url": chatwoot_client.base_url}

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
                    "query_operator": "AND",
                    "custom_attribute_type": "conversation_attribute",
                }
            ]
        }
        try:
            resp = await chatwoot_client.filter_conversations(payload)
            cards = _parse_conversations(resp)
            columns.append({"stage": s, "conversations": cards})
        except Exception as exc:
            logger.error("Failed to filter conversations for stage '%s': %s", s, exc)
            raise HTTPException(
                status_code=502,
                detail=f"Chatwoot API error filtering stage '{s}': {exc}",
            ) from exc

    return {"columns": columns, "chatwoot_url": chatwoot_client.base_url}


@router.get("/api/kanban/debug-status")
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


@router.get("/api/kanban/debug-raw")
async def kanban_debug_raw(stage: str = "Potencial"):
    payload = {
        "payload": [
            {
                "attribute_key": PIPELINE_ATTR_KEY,
                "filter_operator": "equal_to",
                "values": [stage],
                "query_operator": "AND",
                "custom_attribute_type": "conversation_attribute",
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
    contact = conv.get("contact") or {}
    messages = conv.get("messages") or []
    last_msg = messages[-1] if messages else {}

    return {
        "id": conv.get("id"),
        "contact_name": contact.get("name") or conv.get("contact_name") or "",
        "thumbnail": contact.get("thumbnail") or conv.get("thumbnail") or "",
        "last_message": last_msg.get("content") or last_msg.get("text") or "",
        "updated_at": conv.get("updated_at") or "",
        "custom_attributes": conv.get("custom_attributes") or {},
    }

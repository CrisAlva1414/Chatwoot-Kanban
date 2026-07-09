from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from app.chatwoot_client import chatwoot_client

router = APIRouter(tags=["kanban"])

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


@router.get("/kanban", response_class=HTMLResponse)
async def kanban_page():
    html = TEMPLATE_DIR / "kanban.html"
    if not html.exists():
        raise HTTPException(status_code=404, detail="template not found")
    return HTMLResponse(html.read_text())


@router.get("/api/kanban/config")
async def kanban_config():
    definitions = await chatwoot_client.get_custom_attribute_definitions()
    pipeline_attr = None
    for d in definitions:
        if d.get("attribute_key") == "pipeline_01_etapas":
            pipeline_attr = d
            break
    if not pipeline_attr:
        return {"columns": [], "chatwoot_url": chatwoot_client.base_url}
    return {
        "columns": pipeline_attr.get("attribute_values", []),
        "chatwoot_url": chatwoot_client.base_url,
    }


@router.get("/api/kanban/board")
async def kanban_board(stage: str | None = None):
    definitions = await chatwoot_client.get_custom_attribute_definitions()
    pipeline_attr = None
    for d in definitions:
        if d.get("attribute_key") == "pipeline_01_etapas":
            pipeline_attr = d
            break
    if not pipeline_attr:
        return {"columns": []}

    stages = pipeline_attr.get("attribute_values", [])
    target_stages = [stage] if stage else stages

    columns = []
    for s in target_stages:
        payload = {
            "payload": [
                {
                    "attribute_key": "pipeline_01_etapas",
                    "filter_operator": "equal_to",
                    "values": [s],
                    "query_operator": "AND",
                    "custom_attribute_type": "conversation_attribute",
                }
            ]
        }
        try:
            resp = await chatwoot_client.filter_conversations(payload)
        except Exception:
            resp = {"conversations": [], "payload": []}

        cards = _parse_conversations(resp)
        columns.append({"stage": s, "conversations": cards})

    return {"columns": columns, "chatwoot_url": chatwoot_client.base_url}


@router.get("/api/kanban/debug-raw")
async def kanban_debug_raw():
    """Devuelve la respuesta cruda de Chatwoot para debuggear el shape."""
    stage = "Potencial"
    payload = {
        "payload": [
            {
                "attribute_key": "pipeline_01_etapas",
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
            "keys": list(resp.keys())
            if isinstance(resp, dict)
            else type(resp).__name__,
        }
    except Exception as exc:
        return {"error": str(exc)}


def _parse_conversations(resp: dict) -> list:
    """Intenta extraer conversaciones del response de Chatwoot."""
    if isinstance(resp, dict):
        for key in ("payload", "conversations", "data"):
            val = resp.get(key)
            if isinstance(val, list):
                return val
        return []
    if isinstance(resp, list):
        return resp
    return []


def _last_message_preview(conv: dict, maxlen: int = 80) -> str:
    messages = conv.get("messages") or []
    if not messages:
        return ""
    last = messages[-1]
    content = last.get("content") or last.get("text") or ""
    return content if len(content) <= maxlen else content[:maxlen] + "…"

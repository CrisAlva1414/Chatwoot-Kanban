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

        conversations = resp.get("conversations") or resp.get("payload") or []
        cards = []
        for c in conversations:
            meta = c.get("meta") or {}
            sender = meta.get("sender") or {}
            cards.append(
                {
                    "id": c.get("id"),
                    "contact_name": sender.get("name")
                    or sender.get("email")
                    or f"#{c.get('id')}",
                    "thumbnail": sender.get("thumbnail"),
                    "last_message": _last_message_preview(c),
                    "custom_attributes": c.get("custom_attributes") or {},
                    "inbox_id": c.get("inbox_id"),
                    "updated_at": c.get("updated_at"),
                }
            )
        columns.append({"stage": s, "conversations": cards})

    return {"columns": columns, "chatwoot_url": chatwoot_client.base_url}


def _last_message_preview(conv: dict, maxlen: int = 80) -> str:
    messages = conv.get("messages") or []
    if not messages:
        return ""
    last = messages[-1]
    content = last.get("content") or last.get("text") or ""
    return content if len(content) <= maxlen else content[:maxlen] + "…"

import hashlib
import hmac
import logging

from fastapi import APIRouter, HTTPException, Request

from app.config import settings
from app.database import get_pool, sync_task_from_chatwoot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _verify_signature(payload: bytes, header: str | None) -> bool:
    if not settings.chatwoot_webhook_secret:
        return True
    if not header:
        return False
    expected = hmac.new(
        settings.chatwoot_webhook_secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, header)


@router.post("/conversation-updated")
async def conversation_updated(request: Request):
    body = await request.body()
    sig = request.headers.get("x-chatwoot-signature")
    if not _verify_signature(body, sig):
        raise HTTPException(status_code=401, detail="invalid signature")

    data = await request.json()
    event_id = data.get("id")
    if not event_id:
        return {"status": "ignored", "reason": "missing event id"}

    pool = get_pool()
    existing = await pool.fetchrow(
        "SELECT id FROM webhook_events WHERE event_id = $1", event_id
    )
    if existing:
        return {"status": "duplicate", "event_id": event_id}

    conversation = data.get("conversation") or {}
    await pool.execute(
        """INSERT INTO webhook_events (event_id, conversation_id, event_type, payload)
           VALUES ($1, $2, $3, $4)""",
        event_id,
        conversation.get("id"),
        data.get("event", "unknown"),
        body.decode(),
    )

    conv_id = conversation.get("id")
    custom_attrs = conversation.get("custom_attributes") or {}
    if conv_id and (
        custom_attrs.get("kanban_view_mensaje")
        or custom_attrs.get("kanban_view_fecha_termino")
    ):
        try:
            result = await sync_task_from_chatwoot(conv_id, custom_attrs)
            if result:
                logger.info("Webhook sync conv %s: %s", conv_id, result["action"])
        except Exception as exc:
            logger.error("Webhook sync failed for conv %s: %s", conv_id, exc)

    return {"status": "ok", "event_id": event_id}

import logging
import math

from fastapi import APIRouter
from pydantic import BaseModel

from app.chatwoot_client import chatwoot_client
from app.database import get_pool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/migrate", tags=["migrate"])

PIPELINE_ATTR_KEY = "pipeline_01_etapas"
TASK_MSG_ATTR_KEY = "kanban_view_mensaje"
TASK_DATE_ATTR_KEY = "kanban_view_fecha_termino"
STAGES = ["Potencial", "Contactado", "Inicial", "Negociacion", "Ganado", "Perdido"]


class MigrateResult(BaseModel):
    contacts_processed: int
    contacts_updated: int
    contacts_skipped: int
    contacts_failed: int
    db_tasks_migrated: int
    details: list[dict]


@router.post("/contact-attributes", response_model=MigrateResult)
async def migrate_conversation_attributes_to_contacts():
    all_conversations: list[dict] = []

    for stage in STAGES:
        page = 1
        while True:
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
                resp = await chatwoot_client.filter_conversations(payload, page=page)
            except Exception as exc:
                logger.error(
                    "Failed to fetch conversations for stage '%s' page %s: %s",
                    stage,
                    page,
                    exc,
                )
                break

            conversations = _extract_list(resp)
            all_conversations.extend(conversations)

            meta = resp.get("meta") or {}
            count = meta.get("all_count", 0)
            page_size = 25
            total_pages = max(1, math.ceil(count / page_size)) if count else 1
            if page >= total_pages:
                break
            page += 1

    contact_map: dict[int, dict] = {}
    for conv in all_conversations:
        sender = (conv.get("meta") or {}).get("sender") or {}
        contact_id = sender.get("id")
        if not contact_id:
            continue

        attrs = conv.get("custom_attributes") or {}
        stage = attrs.get(PIPELINE_ATTR_KEY, "")
        msg = attrs.get(TASK_MSG_ATTR_KEY, "")
        fecha = attrs.get(TASK_DATE_ATTR_KEY, "")

        if not stage and not msg and not fecha:
            continue

        updated = conv.get("updated_at", 0)
        if isinstance(updated, str):
            updated = 0

        existing = contact_map.get(contact_id)
        if existing and existing["_updated"] >= updated:
            continue

        contact_map[contact_id] = {
            "contact_id": contact_id,
            "contact_name": sender.get("name", ""),
            "stage": stage,
            "msg": msg,
            "fecha": fecha,
            "_updated": updated,
            "_conv_id": conv.get("id"),
        }

    result = MigrateResult(
        contacts_processed=len(contact_map),
        contacts_updated=0,
        contacts_skipped=0,
        contacts_failed=0,
        db_tasks_migrated=0,
        details=[],
    )

    for contact_id, data in contact_map.items():
        attrs_to_set: dict = {}
        if data["stage"]:
            attrs_to_set[PIPELINE_ATTR_KEY] = data["stage"]
        if data["msg"]:
            attrs_to_set[TASK_MSG_ATTR_KEY] = data["msg"]
        if data["fecha"]:
            attrs_to_set[TASK_DATE_ATTR_KEY] = data["fecha"]

        if not attrs_to_set:
            result.contacts_skipped += 1
            continue

        try:
            await chatwoot_client.update_contact_custom_attributes(
                contact_id, attrs_to_set
            )
            result.contacts_updated += 1
            result.details.append(
                {
                    "contact_id": contact_id,
                    "contact_name": data["contact_name"],
                    "attrs_set": list(attrs_to_set.keys()),
                    "from_conv": data["_conv_id"],
                    "status": "ok",
                }
            )
        except Exception as exc:
            result.contacts_failed += 1
            result.details.append(
                {
                    "contact_id": contact_id,
                    "contact_name": data["contact_name"],
                    "status": "failed",
                    "error": str(exc),
                }
            )

    pool = get_pool()
    for contact_id, data in contact_map.items():
        try:
            await pool.execute(
                """UPDATE tareas
                   SET contact_id = $1
                   WHERE conversation_id = $2 AND contact_id IS NULL""",
                contact_id,
                data["_conv_id"],
            )
            result.db_tasks_migrated += 1
        except Exception as exc:
            logger.error(
                "Failed to migrate DB task for contact %s: %s", contact_id, exc
            )

    return result


@router.post("/db-tasks-only")
async def migrate_db_tasks_to_contact_id():
    pool = get_pool()

    rows = await pool.fetch(
        """SELECT t.id, t.conversation_id, t.contact_id
           FROM tareas t
           WHERE t.contact_id IS NULL AND t.conversation_id IS NOT NULL"""
    )

    migrated = 0
    failed = 0
    details = []

    for row in rows:
        conv_id = row["conversation_id"]
        try:
            conv = await chatwoot_client.get_conversation(conv_id)
            sender = (conv.get("meta") or {}).get("sender") or {}
            contact_id = sender.get("id")
            if not contact_id:
                failed += 1
                details.append(
                    {
                        "task_id": row["id"],
                        "conversation_id": conv_id,
                        "status": "no_contact",
                    }
                )
                continue

            await pool.execute(
                "UPDATE tareas SET contact_id = $1 WHERE id = $2",
                contact_id,
                row["id"],
            )
            migrated += 1
            details.append(
                {
                    "task_id": row["id"],
                    "conversation_id": conv_id,
                    "contact_id": contact_id,
                    "status": "ok",
                }
            )
        except Exception as exc:
            failed += 1
            details.append(
                {
                    "task_id": row["id"],
                    "conversation_id": conv_id,
                    "status": "failed",
                    "error": str(exc),
                }
            )

    return {
        "total": len(rows),
        "migrated": migrated,
        "failed": failed,
        "details": details,
    }


@router.get("/status")
async def migration_status():
    pool = get_pool()

    total_tasks = await pool.fetchval("SELECT COUNT(*) FROM tareas")
    tasks_with_contact = await pool.fetchval(
        "SELECT COUNT(*) FROM tareas WHERE contact_id IS NOT NULL"
    )
    tasks_without_contact = await pool.fetchval(
        """SELECT COUNT(*) FROM tareas
           WHERE contact_id IS NULL
             AND estado NOT IN ('tarea_cerrada')"""
    )

    tasks_total_active = await pool.fetchval(
        """SELECT COUNT(*) FROM tareas
           WHERE estado NOT IN ('tarea_cerrada')"""
    )

    return {
        "total_tasks": total_tasks,
        "total_active_tasks": tasks_total_active,
        "tasks_with_contact_id": tasks_with_contact,
        "tasks_without_contact_id": tasks_without_contact,
        "tasks_closed": total_tasks - tasks_total_active,
        "migration_complete": tasks_without_contact == 0 and total_tasks > 0,
    }


@router.post("/cleanup-duplicates")
async def cleanup_duplicate_tasks():
    pool = get_pool()
    result = {"closed": 0, "skipped": 0, "errors": []}

    orphans = await pool.fetch(
        """SELECT id, conversation_id FROM tareas
           WHERE contact_id IS NULL AND conversation_id IS NOT NULL"""
    )

    for row in orphans:
        conv_id = row["conversation_id"]
        try:
            conv = await chatwoot_client.get_conversation(conv_id)
            sender = (conv.get("meta") or {}).get("sender") or {}
            contact_id = sender.get("id")
            if not contact_id:
                result["skipped"] += 1
                continue

            existing = await pool.fetchrow(
                "SELECT id FROM tareas WHERE contact_id = $1 AND id != $2",
                contact_id,
                row["id"],
            )
            if existing:
                await pool.execute(
                    """UPDATE tareas
                       SET estado = 'tarea_cerrada',
                           contact_id = NULL,
                           cerrado_por = (
                             SELECT id FROM agentes
                              WHERE email = 'bot@i-labs.cl' LIMIT 1
                           ),
                           cerrado_en = now()
                       WHERE id = $1""",
                    row["id"],
                )
                result["closed"] += 1
            else:
                await pool.execute(
                    "UPDATE tareas SET contact_id = $1 WHERE id = $2",
                    contact_id,
                    row["id"],
                )
                result["closed"] += 1
        except Exception as exc:
            result["errors"].append(
                {
                    "task_id": row["id"],
                    "conversation_id": conv_id,
                    "error": str(exc),
                }
            )

    return result


def _extract_list(resp: dict | list) -> list:
    if isinstance(resp, list):
        return resp
    if not isinstance(resp, dict):
        return []
    for key in ("conversations", "data", "payload"):
        val = resp.get(key)
        if isinstance(val, list):
            return val
        if isinstance(val, dict):
            return _extract_list(val)
    return []

import json
import logging
from contextlib import suppress
from datetime import date

import asyncpg

from app.config import settings

logger = logging.getLogger(__name__)

pool: asyncpg.Pool | None = None


async def init_pool() -> asyncpg.Pool:
    global pool
    dsn = settings.resolved_db_url
    pool = await asyncpg.create_pool(dsn=dsn, min_size=2, max_size=10)
    await _init_schema()
    return pool


async def close_pool() -> None:
    global pool
    if pool:
        await pool.close()
        pool = None


def get_pool() -> asyncpg.Pool:
    assert pool is not None, "database pool not initialized"
    return pool


async def _init_schema() -> None:
    sql = """
    CREATE TABLE IF NOT EXISTS agentes (
      id                SERIAL PRIMARY KEY,
      email             TEXT NOT NULL UNIQUE,
      nombre            TEXT NOT NULL,
      chatwoot_agent_id INTEGER,
      activo            BOOLEAN NOT NULL DEFAULT true
    );

    CREATE TABLE IF NOT EXISTS tareas (
      id                BIGSERIAL PRIMARY KEY,
      contact_id        INTEGER,
      conversation_id   INTEGER,
      mensaje           TEXT NOT NULL,
      fecha_vencimiento DATE NOT NULL,
      estado            TEXT NOT NULL DEFAULT 'tarea_activa',
      creado_por        INTEGER NOT NULL REFERENCES agentes(id),
      cerrado_por       INTEGER REFERENCES agentes(id),
      created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
      cerrado_en        TIMESTAMPTZ,
      sync_pendiente    BOOLEAN NOT NULL DEFAULT false
    );

    CREATE TABLE IF NOT EXISTS task_audit_log (
      id               BIGSERIAL PRIMARY KEY,
      contact_id       INTEGER,
      conversation_id  INTEGER,
      actor_agent_id   INTEGER NOT NULL,
      actor_name       TEXT NOT NULL,
      action           TEXT NOT NULL,
      previous_state   JSONB,
      new_state        JSONB,
      source           TEXT NOT NULL DEFAULT 'manual',
      chatwoot_call_ok BOOLEAN,
      created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_audit_conversation
      ON task_audit_log (conversation_id);
    CREATE INDEX IF NOT EXISTS idx_audit_actor
      ON task_audit_log (actor_agent_id);

    CREATE TABLE IF NOT EXISTS webhook_events (
      id               BIGSERIAL PRIMARY KEY,
      event_id         TEXT NOT NULL UNIQUE,
      contact_id       INTEGER,
      conversation_id  INTEGER,
      event_type       TEXT NOT NULL,
      payload          JSONB NOT NULL,
      processed_at     TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_webhook_event_id
      ON webhook_events (event_id);
    """
    async with pool.acquire() as conn:
        await conn.execute(sql)
        await _migrate_schema(conn)


async def _migrate_schema(conn) -> None:
    col_check = await conn.fetchrow(
        """SELECT column_name FROM information_schema.columns
           WHERE table_name = 'tareas' AND column_name = 'contact_id'"""
    )
    if not col_check:
        await conn.execute("ALTER TABLE tareas ADD COLUMN contact_id INTEGER")

    await conn.execute("ALTER TABLE tareas ALTER COLUMN conversation_id DROP NOT NULL")

    old_constraint = await conn.fetchrow(
        """SELECT conname FROM pg_constraint
           WHERE conrelid = 'tareas'::regclass
             AND conname = 'tareas_conversation_id_key'"""
    )
    if old_constraint:
        await conn.execute(
            "ALTER TABLE tareas DROP CONSTRAINT tareas_conversation_id_key"
        )

    await conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_tareas_contact_id "
        "ON tareas (contact_id) WHERE contact_id IS NOT NULL"
    )

    audit_col = await conn.fetchrow(
        """SELECT column_name FROM information_schema.columns
           WHERE table_name = 'task_audit_log' AND column_name = 'contact_id'"""
    )
    if not audit_col:
        await conn.execute("ALTER TABLE task_audit_log ADD COLUMN contact_id INTEGER")

    await conn.execute(
        "ALTER TABLE task_audit_log ALTER COLUMN conversation_id DROP NOT NULL"
    )

    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_contact ON task_audit_log (contact_id)"
    )

    webhook_col = await conn.fetchrow(
        """SELECT column_name FROM information_schema.columns
           WHERE table_name = 'webhook_events' AND column_name = 'contact_id'"""
    )
    if not webhook_col:
        await conn.execute("ALTER TABLE webhook_events ADD COLUMN contact_id INTEGER")

    await conn.execute(
        "ALTER TABLE webhook_events ALTER COLUMN conversation_id DROP NOT NULL"
    )


async def get_or_create_agent(email: str, nombre: str = "") -> dict:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, nombre FROM agentes WHERE email = $1", email
        )
        if row:
            return dict(row)
        result = await conn.fetchrow(
            "INSERT INTO agentes (email, nombre)"
            " VALUES ($1, $2)"
            " RETURNING id, email, nombre",
            email,
            nombre or email.split("@")[0],
        )
        return dict(result)


async def write_audit_log(
    *,
    contact_id: int | None,
    conversation_id: int | None = None,
    actor_agent_id: int,
    actor_name: str,
    action: str,
    previous_state: dict | None,
    new_state: dict | None,
    source: str = "manual",
    chatwoot_call_ok: bool | None = None,
) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO task_audit_log
               (contact_id, conversation_id, actor_agent_id, actor_name,
                 action, previous_state, new_state, source, chatwoot_call_ok)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
            contact_id,
            conversation_id,
            actor_agent_id,
            actor_name,
            action,
            json.dumps(previous_state) if previous_state else None,
            json.dumps(new_state) if new_state else None,
            source,
            chatwoot_call_ok,
        )


async def upsert_task(
    *,
    contact_id: int,
    conversation_id: int | None,
    mensaje: str,
    fecha_vencimiento: date,
    actor_agent_id: int,
) -> dict:
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            """SELECT id, mensaje, fecha_vencimiento, estado, creado_por, created_at
               FROM tareas WHERE contact_id = $1""",
            contact_id,
        )
        if existing:
            await conn.execute(
                """UPDATE tareas
                   SET mensaje = $2, fecha_vencimiento = $3,
                       conversation_id = $4, sync_pendiente = true
                   WHERE id = $1""",
                existing["id"],
                mensaje,
                fecha_vencimiento,
                conversation_id,
            )
            return {"id": existing["id"], "action": "updated"}
        result = await conn.fetchrow(
            """INSERT INTO tareas
               (contact_id, conversation_id, mensaje, fecha_vencimiento, creado_por)
               VALUES ($1, $2, $3, $4, $5)
               RETURNING id""",
            contact_id,
            conversation_id,
            mensaje,
            fecha_vencimiento,
            actor_agent_id,
        )
        return {"id": result["id"], "action": "created"}


async def edit_task(task_id: int, *, mensaje: str, fecha_vencimiento: date) -> dict:
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            """SELECT id, contact_id, conversation_id, mensaje,
                      fecha_vencimiento, estado
               FROM tareas WHERE id = $1""",
            task_id,
        )
        if not existing:
            return {"error": "not_found"}
        await conn.execute(
            """UPDATE tareas
               SET mensaje = $2, fecha_vencimiento = $3, sync_pendiente = true
               WHERE id = $1""",
            task_id,
            mensaje,
            fecha_vencimiento,
        )
        return {"action": "edited", "previous": dict(existing)}


async def close_task(task_id: int, *, cerrado_por: int) -> dict:
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id, contact_id, conversation_id, estado FROM tareas WHERE id = $1",
            task_id,
        )
        if not existing:
            return {"error": "not_found"}
        if existing["estado"] == "tarea_cerrada":
            return {"error": "already_closed"}
        await conn.execute(
            """UPDATE tareas
               SET estado = 'tarea_cerrada', cerrado_por = $2,
                   cerrado_en = now(), sync_pendiente = true
               WHERE id = $1""",
            task_id,
            cerrado_por,
        )
        return {"action": "closed", "previous": dict(existing)}


async def get_active_task(contact_id: int) -> dict | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT t.*, a.nombre AS creado_por_nombre
               FROM tareas t
               JOIN agentes a ON a.id = t.creado_por
               WHERE t.contact_id = $1
               AND t.estado NOT IN ('tarea_cerrada', 'tarea_vencida')""",
            contact_id,
        )
        return dict(row) if row else None


async def get_tasks_for_contacts(contact_ids: list[int]) -> dict:
    if not contact_ids:
        return {}
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT t.*, a.nombre AS creado_por_nombre
               FROM tareas t
               JOIN agentes a ON a.id = t.creado_por
               WHERE t.contact_id = ANY($1)
               AND (
                 t.estado NOT IN ('tarea_cerrada', 'tarea_vencida')
                 OR t.cerrado_en >= now() - interval '24 hours'
               )""",
            contact_ids,
        )
        return {row["contact_id"]: dict(row) for row in rows}


async def get_pending_sync_tasks() -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, contact_id, conversation_id, estado, fecha_vencimiento
               FROM tareas WHERE sync_pendiente = true"""
        )
        return [dict(row) for row in rows]


async def mark_task_synced(task_id: int) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE tareas SET sync_pendiente = false WHERE id = $1", task_id
        )


async def cron_tick() -> dict:
    transitions = {"hoy": 0, "vencida": 0, "synced": 0, "failed": 0}
    async with pool.acquire() as conn:
        today_rows = await conn.fetch(
            """UPDATE tareas SET estado = 'tarea_hoy', sync_pendiente = true
               WHERE estado = 'tarea_activa' AND fecha_vencimiento <= CURRENT_DATE
               RETURNING id, contact_id"""
        )
        transitions["hoy"] = len(today_rows)

        vencida_rows = await conn.fetch(
            """UPDATE tareas SET estado = 'tarea_vencida', sync_pendiente = true
               WHERE estado = 'tarea_hoy'
               RETURNING id, contact_id"""
        )
        transitions["vencida"] = len(vencida_rows)

    pending = await get_pending_sync_tasks()
    for task in pending:
        try:
            from app.chatwoot_client import chatwoot_client

            contact_id = task.get("contact_id")
            if not contact_id:
                logger.warning("Task %s has no contact_id, skipping sync", task["id"])
                transitions["failed"] += 1
                continue

            fecha_iso = task["fecha_vencimiento"].isoformat() + "T23:59:59.999Z"
            await chatwoot_client.safe_update_contact_custom_attributes(
                contact_id,
                {"kanban_view_fecha_termino": fecha_iso},
                skip_read=True,
            )
            await mark_task_synced(task["id"])
            transitions["synced"] += 1
        except Exception as exc:
            logger.error(
                "Cron sync failed for task %s (contact %s): %s",
                task["id"],
                task.get("contact_id"),
                exc,
            )
            transitions["failed"] += 1

    return transitions


async def sync_task_from_chatwoot(
    contact_id: int,
    custom_attributes: dict,
    conversation_id: int | None = None,
) -> dict | None:
    mensaje = (custom_attributes.get("kanban_view_mensaje") or "").strip()
    fecha_raw = (custom_attributes.get("kanban_view_fecha_termino") or "").strip()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, estado FROM tareas WHERE contact_id = $1",
            contact_id,
        )

        if not mensaje and not fecha_raw:
            if row and row["estado"] != "tarea_cerrada":
                agent = await get_or_create_agent("bot@i-labs.cl")
                await conn.execute(
                    """UPDATE tareas
                       SET estado = 'tarea_cerrada', cerrado_por = $2,
                           cerrado_en = now()
                       WHERE id = $1""",
                    row["id"],
                    agent["id"],
                )
                return {"action": "closed"}
            return None

        fecha = date.today()
        if fecha_raw:
            with suppress(ValueError):
                fecha = date.fromisoformat(fecha_raw[:10])

        if row:
            await conn.execute(
                """UPDATE tareas
                   SET mensaje = $2, fecha_vencimiento = $3,
                       estado = 'tarea_activa',
                       conversation_id = $4,
                       cerrado_por = NULL, cerrado_en = NULL
                   WHERE id = $1""",
                row["id"],
                mensaje,
                fecha,
                conversation_id,
            )
            return {"action": "updated"}

        agent_ = await get_or_create_agent("bot@i-labs.cl")
        result = await conn.fetchrow(
            """INSERT INTO tareas
               (contact_id, conversation_id, mensaje, fecha_vencimiento, creado_por)
               VALUES ($1, $2, $3, $4, $5)
               RETURNING id""",
            contact_id,
            conversation_id,
            mensaje or "(Sincronizado desde Chatwoot)",
            fecha,
            agent_["id"],
        )
        return {"action": "created", "task_id": result["id"]}


async def batch_sync_tasks_from_chatwoot(contacts_data: list[dict]) -> dict:
    if not contacts_data:
        return {"updated": 0, "created": 0, "closed": 0}

    entries = []
    for contact in contacts_data:
        attrs = contact.get("custom_attributes") or {}
        mensaje = (attrs.get("kanban_view_mensaje") or "").strip()
        fecha_raw = (attrs.get("kanban_view_fecha_termino") or "").strip()
        fecha = date.today()
        if fecha_raw:
            with suppress(ValueError):
                fecha = date.fromisoformat(fecha_raw[:10])
        entries.append(
            {
                "contact_id": contact["contact_id"],
                "conversation_id": contact.get("conversation_id"),
                "mensaje": mensaje,
                "fecha_raw": fecha_raw,
                "fecha": fecha,
            }
        )

    async with pool.acquire() as conn:
        contact_ids = [e["contact_id"] for e in entries if e["contact_id"]]
        if not contact_ids:
            return {"updated": 0, "created": 0, "closed": 0}

        rows = await conn.fetch(
            "SELECT id, contact_id, estado FROM tareas WHERE contact_id = ANY($1)",
            contact_ids,
        )
        existing_map = {row["contact_id"]: dict(row) for row in rows}

        updates: list[tuple] = []
        creates: list[tuple] = []
        closes: list[tuple] = []
        bot_agent_id: int | None = None

        for entry in entries:
            cid = entry["contact_id"]
            existing = existing_map.get(cid)

            if not entry["mensaje"] and not entry["fecha_raw"]:
                if existing and existing["estado"] != "tarea_cerrada":
                    if bot_agent_id is None:
                        agent = await get_or_create_agent("bot@i-labs.cl")
                        bot_agent_id = agent["id"]
                    closes.append((existing["id"], bot_agent_id))
                continue

            if existing:
                updates.append(
                    (
                        existing["id"],
                        entry["mensaje"] or "(Sincronizado desde Chatwoot)",
                        entry["fecha"],
                        entry["conversation_id"],
                    )
                )
            else:
                if bot_agent_id is None:
                    agent = await get_or_create_agent("bot@i-labs.cl")
                    bot_agent_id = agent["id"]
                creates.append(
                    (
                        cid,
                        entry["conversation_id"],
                        entry["mensaje"] or "(Sincronizado desde Chatwoot)",
                        entry["fecha"],
                        bot_agent_id,
                    )
                )

        if updates:
            await conn.executemany(
                """UPDATE tareas
                   SET mensaje = $2, fecha_vencimiento = $3,
                       estado = 'tarea_activa',
                       conversation_id = $4,
                       cerrado_por = NULL, cerrado_en = NULL
                   WHERE id = $1""",
                updates,
            )
        if creates:
            await conn.executemany(
                """INSERT INTO tareas
                   (contact_id, conversation_id, mensaje, fecha_vencimiento, creado_por)
                   VALUES ($1, $2, $3, $4, $5)""",
                creates,
            )
        if closes:
            await conn.executemany(
                """UPDATE tareas
                   SET estado = 'tarea_cerrada', cerrado_por = $2, cerrado_en = now()
                   WHERE id = $1""",
                closes,
            )

    return {"updated": len(updates), "created": len(creates), "closed": len(closes)}


async def get_agent_stats() -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT
                 a.id AS agent_id,
                 a.nombre,
                 a.email,
                 COUNT(*) FILTER (WHERE action = 'create')
                   AS tasks_created,
                 COUNT(*) FILTER (WHERE action = 'close')
                   AS tasks_closed,
                 COUNT(*) FILTER (WHERE action = 'task_overwritten')
                   AS tasks_overwritten,
                 COUNT(*)
                   FILTER (WHERE action = 'close'
                     AND chatwoot_call_ok IS DISTINCT FROM false)
                   AS successful_closes
               FROM task_audit_log al
               JOIN agentes a ON a.id = al.actor_agent_id
               GROUP BY a.id, a.nombre, a.email
               ORDER BY tasks_closed DESC"""
        )
        return [dict(row) for row in rows]


async def get_audit_history(limit: int = 50) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT
                 al.id, al.conversation_id, al.actor_name, al.action,
                 al.previous_state, al.new_state, al.source,
                 al.chatwoot_call_ok, al.created_at
               FROM task_audit_log al
               ORDER BY al.created_at DESC
               LIMIT $1""",
            limit,
        )
        return [dict(row) for row in rows]

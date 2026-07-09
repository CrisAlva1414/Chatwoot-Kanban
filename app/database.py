import asyncpg

from app.config import settings

pool: asyncpg.Pool | None = None


async def init_pool() -> asyncpg.Pool:
    global pool
    dsn = settings.database_url
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
      conversation_id   INTEGER NOT NULL UNIQUE,
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
      conversation_id  INTEGER NOT NULL,
      contact_id       INTEGER,
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
      conversation_id  INTEGER NOT NULL,
      event_type       TEXT NOT NULL,
      payload          JSONB NOT NULL,
      processed_at     TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_webhook_event_id
      ON webhook_events (event_id);
    """
    async with pool.acquire() as conn:
        await conn.execute(sql)

# ADR-004 — Audit log aplicativo como fuente de atribución real

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-07-09 |
| **Proyecto** | kanban.ruki-bot.com |
| **Decidido por** | Sesión de factibilidad técnica inicial |

---

## Contexto

Dado que todas las llamadas a Chatwoot se hacen con el token del bot-user (ADR-002), el dashboard nativo de Chatwoot registra todas las acciones como realizadas por el bot-user, sin atribución al agente humano real.

Chatwoot dispone de Audit Logs nativos, pero estos registran acciones de usuarios logueados en el dashboard web, no acciones realizadas via API con token. No son una alternativa viable para este caso.

El negocio requiere poder determinar quién creó y quién cerró cada tarea, mínimamente para métricas de productividad por agente (`COUNT(*) GROUP BY cerrado_por`).

## Decisión

Mantener un **audit log propio en la BD** que se escribe en el momento en que el backend recibe la acción desde la sesión autenticada del agente (antes de llamar a Chatwoot). El log es la fuente de verdad de atribución; Chatwoot no lo es.

## Fundamento técnico

El flujo garantiza que la identidad real del agente siempre está disponible en el backend antes de que se haga cualquier llamada downstream:

```
Agente (sesión Cloudflare Access)
  → request a backend con header CF_ACCESS_AUTHENTICATED_USER_EMAIL
  → backend extrae email, cruza con tabla agentes, obtiene actor real
  → escribe en task_audit_log (actor_agent_id, action, previous_state, new_state, source)
  → llama a Chatwoot con bot-user token
  → si Chatwoot falla → chatwoot_call_ok = false en el log (no se pierde el intento)
```

## Schema propuesto

```sql
CREATE TABLE task_audit_log (
  id               BIGSERIAL PRIMARY KEY,
  conversation_id  INTEGER NOT NULL,
  contact_id       INTEGER,
  actor_agent_id   INTEGER NOT NULL,
  actor_name       TEXT NOT NULL,          -- snapshot: no depende de que el agente siga existiendo
  action           TEXT NOT NULL,          -- 'create' | 'reassign' | 'close' | 'auto_expire' | 'edit_message'
  previous_state   JSONB,
  new_state        JSONB,
  source           TEXT NOT NULL DEFAULT 'manual',  -- 'manual' | 'cron'
  chatwoot_call_ok BOOLEAN,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_conversation ON task_audit_log (conversation_id);
CREATE INDEX idx_audit_actor        ON task_audit_log (actor_agent_id);
```

## Decisiones de diseño dentro del schema

- **`actor_name` como snapshot de texto:** si el agente se elimina de la BD, el log sigue siendo legible sin joins rotos. Estándar en auditoría point-in-time.
- **`source = 'cron'`:** permite distinguir "el agente cerró la tarea a tiempo" de "el sistema la marcó vencida automáticamente" en reportes, sin necesidad de lógica extra.
- **`chatwoot_call_ok`:** registra si el espejo en Chatwoot se actualizó correctamente. Si es `false`, el estado real está en el log pero el custom_attribute `tarea_estado` en Chatwoot puede estar desincronizado — permite detectar y remediar sin perder el evento.
- **`previous_state / new_state` como JSONB:** el modelo de tarea es pequeño y puede evolucionar; JSONB evita migraciones constantes para cambios en el payload de estados.

## Consecuencias

- El panel histórico (últimas 100 tareas) y métricas de productividad (`quién cerró más tareas`) salen directamente de este log con queries simples, sin parsear texto de notas ni consultar Chatwoot.
- El log es append-only por diseño: nunca se actualiza una fila existente, solo se insertan nuevas filas por cada transición de estado.

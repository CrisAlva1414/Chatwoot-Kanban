# Sesión 005 — Fix URL account, paginación y webhook sync

- **Fecha:** 2026-07-20
- **Propósito:** Corregir bugs de URL "Abrir en Chatwoot" (account 1→3),
  paginación de leads (solo 25), e implementar sincronización bidireccional
  Chatwoot → BD local vía webhook + read-through.

## Contexto

Tres problemas detectados en producción:

1. **URL de Chatwoot incorrecta** — Al hacer click en una card o en el modal
   "Abrir en Chatwoot", redirigía a `/app/accounts/1/conversations/{id}`
   cuando debería ser account `3`.

2. **Paginación rota** — Etapas con muchos leads (ej. "Perdidos" con 163) solo
   mostraban 25 porque la paginación no funcionaba.

3. **Sin sync bidireccional** — Si un agente modificaba `kanban_view_mensaje` o
   `kanban_view_fecha_termino` directo en Chatwoot, la BD local nunca se
   enteraba y el Kanban mostraba datos stale.

## Cambios realizados

### 1. Fix URL de Chatwoot (account_id)

**Problema (doble):**

- El click en una card ya no llamaba a `openConversation()` (función antigua)
  sino a `openTaskModal()`, que tenía su PROPIA construcción de URL con el
  mismo regex roto. Nuestra fix anterior solo cubrió `openConversation()`.
  
- `openTaskModal()` en kanban.html:673 usaba:
  ```javascript
  chatwootUrl.match(/\/accounts\/(\d+)/)  // nunca matchea
  ```
  y caía al fallback `accounts/1`.

**Fix:**
- `openTaskModal()` ahora usa `chatwootAccountId` directo (variable capturada
  desde la API), mismo patrón que `openConversation()`.

### 2. Paginación de leads

**Problema (oculto):** El loop de páginas asumía que `meta` está en el
top-level de la respuesta de Chatwoot, pero la API lo devuelve anidado dentro
de `payload`:
```json
{"payload": {"conversations": [...], "meta": {"pages_count": 7}}}
```
`resp.get("meta")` devolvía `None` → `total_pages = 1` → siempre una página.

**Fix:**
- Nueva helper `_extract_meta(resp)` que busca `meta` en top-level y también
  dentro de `payload`/`data` (mismo patrón que `_extract_conversation_list`).
- Agregado `chatwoot_account_id` al return del caso `not pipeline_attr`.

### 3. Sincronización bidireccional (Chatwoot → BD local)

**Arquitectura:** Dos capas de sync:

#### a) Read-through en `kanban_board()`
Después de recolectar todas las conversaciones (con paginación), se llama a
`sync_task_from_chatwoot()` por cada card antes de buscar las tareas locales.
Esto asegura que al refrescar el board, la BD local refleje el estado actual
de Chatwoot. Cubre casos donde el webhook no llegó (caída, reinicio).

#### b) Webhook processing en `webhooks.py`
Cuando Chatwoot notifica `conversation_updated`, además de guardar el evento
raw en `webhook_events`, se extraen `custom_attributes` y se llama a
`syc_task_from_chatwoot()` si hay datos de tarea (`kanban_view_mensaje` o
`kanban_view_fecha_termino`).

#### Función `sync_task_from_chatwoot()` en `database.py`

Lógica idempotente:
| Chatwoot tiene `mensaje`? | Tarea local existe? | Acción |
|---|---|---|
| Sí | No | `INSERT` con agente bot, mensaje "(Sincronizado desde Chatwoot)" |
| Sí | Sí (cualquier estado) | `UPDATE` mensaje, fecha, reset estado a `tarea_activa`, limpia cerrado |
| No (vacíos) | Sí y no cerrada | `UPDATE` estado = `tarea_cerrada` |
| No (vacíos) | No o ya cerrada | No-op |

## Archivos tocados

**Modificados:**
- `app/templates/kanban.html` — `openTaskModal()` usa `chatwootAccountId`
- `app/routers/kanban.py` — `_extract_meta()`, read-through sync, fallback
  `chatwoot_account_id`, import `sync_task_from_chatwoot`
- `app/database.py` — nueva función `sync_task_from_chatwoot()`
- `app/routers/webhooks.py` — llamar a `sync_task_from_chatwoot()` en cada
  evento `conversation_updated`

## Archivos renombrados

- `docs/sesiones/005-2026-07-20-fix-url-account-y-paginacion.md` →
  `005-2026-07-20-fix-url-account-paginacion-webhook.md`

## Próximo paso

- Configurar webhook en Chatwoot apuntando a
  `https://kanban.example.com/webhooks/conversation-updated` con secret
  `tkA9gJdJL2fRSsSBLgCCkjRy`
- Verificar en staging que los 3 fixes funcionan

# Sesión 011 — Non-blocking operations y optimizaciones de UX

- **Fecha:** 2026-07-26
- **Propósito:** Eliminar operaciones bloqueantes en creación/modificación de tareas, reducir latencia de polling, y optimizar la experiencia de usuario con cache + optimistic UI.

## Contexto

El sistema de Kanban + tareas requería alta sincronización entre DB local y Chatwoot, pero las operaciones de escritura (crear/editar/cerrar tareas) eran bloqueantes: el usuario esperaba 200-2000ms por la llamada HTTP a la API de Chatwoot antes de recibir confirmación. El polling cada 30s disparaba N×HTTP calls (una por etapa × paginación) para cada usuario activo.

## Cambios realizados

### 1. Background Tasks (`app/routers/kanban.py`)

**Problema:** Operaciones `POST /tasks`, `PATCH /tasks/{id}`, `PATCH /tasks/{id}/close` esperaban la respuesta de Chatwoot antes de devolver al cliente.

**Solución:** Usar `BackgroundTasks` de FastAPI. El endpoint:
1. Ejecuta validación + DB local (~10-50ms)
2. Retorna "ok" inmediatamente al usuario
3. En background: sync a Chatwoot + write audit log

**Función helper:** `_bg_sync_task_and_audit()` — ejecuta `safe_update_contact_custom_attributes` + `write_audit_log` en background. Si falla, loggea error y flag `sync_pendiente` garantiza reintento vía `cron_tick`.

**Endpoints modificados:**
- `create_task` — `POST /tasks`
- `update_task_endpoint` — `PATCH /tasks/{id}`
- `close_task_endpoint` — `PATCH /tasks/{id}/close`

**No modificado:** `move_stage` (`PATCH /board/{id}/stage`) se mantiene síncrono por requerir validación de stages.

### 2. Board cache server-side (`app/routers/kanban.py`)

**Problema:** Cada polling de cada usuario disparaba N llamadas a Chatwoot (`filter_contacts` por etapa × paginación).

**Solución:** Cache en memoria del resultado de `GET /board` con TTL de 8 segundos.
- `_board_cache: dict[str, tuple[float, dict]]`
- `_get_cached_board(stage)` / `_set_cached_board(stage, data)`
- `_invalidate_board_cache()` — llamado en `create_task`, `update_task_endpoint`, `close_task_endpoint`, `move_stage`
- Response incluye `generated_at` (timestamp) para que el frontend detecte cambios

### 3. Aumentar page_size (`app/chatwoot_client.py`)

**Problema:** Chatwoot devuelve 15 contactos por página, generando múltiples HTTP calls por etapa.

**Solución:** `filter_contacts()` ahora envía `page_size=50` por defecto. `_PAGE_SIZE = 50` en `kanban.py` para cálculo de paginación.

### 4. Optimistic UI frontend (`app/templates/kanban.html`)

**Problema:** Al crear/editar/cerrar tarea, el frontend abría modal, esperaba respuesta del server, y recargaba el board completo.

**Solución:**
- `optimisticTaskUpdate(contactId, taskData)` — actualiza el badge de tarea en la card inmediatamente
- `createTask()`, `saveTask()`, `closeTaskAction()` — cierran el modal y actualizan la UI antes de llamar al API
- Si la API falla → `refreshBoard()` para rollback

### 5. Polling adaptativo (`app/templates/kanban.html`)

**Problema:** Polling fijo cada 30s sin importar si el board cambió.

**Solución:**
- Usa `setTimeout` recursivo en vez de `setInterval`
- Compara `generated_at` del server con `lastGeneratedAt` local
- Sin cambios: aumenta intervalo gradualmente (+10s hasta max 60s)
- Con cambios: resetea a intervalo mínimo (15s)
- Si el tab está oculto o hay modal abierto, aplaza el poll

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `app/chatwoot_client.py` | +page_size en `filter_contacts` |
| `app/routers/kanban.py` | +BackgroundTasks, +board cache, +_bg_sync_task_and_audit, refactor create/update/close endpoints |
| `app/templates/kanban.html` | +optimisticTaskUpdate, optimistic UI en CRUD, polling adaptativo con setTimeout |
| `tests/conftest.py` | +fixture `_clear_board_cache` |
| `docs/sesiones/011-2026-07-26-non-blocking-optimizaciones.md` | Creado |

## Decisiones

- No se requirió nuevo ADR — son optimizaciones de performance/UX sin cambios arquitectónicos (similar a sesión 009)
- **BackgroundTasks vs asyncio.create_task:** BackgroundTasks de FastAPI garantiza ejecución dentro del ciclo de vida del request. Es más seguro que `asyncio.create_task()` que podría cancelarse.
- **move_stage síncrono:** Se mantiene porque la validación de stage requiere respuesta inmediata. El frontend ya hace optimistic UI en drag & drop.
- **TTL de 8s:** Suficiente para que múltiples usuarios polling simultáneamente peguen al cache, pero corto para mantener frescura de datos.
- **page_size 50:** Valor conservador; Chatwoot no documenta límite máximo pero 50 es seguro.

## Próximo paso

1. Deploy a staging (develop → Arcane)
2. Probar en devkanban.ruki-bot.com:
   - Crear tarea: debe ser instantáneo
   - Editar/cerrar tarea: debe ser instantáneo
   - Mover stages: sin cambios
   - Polling: verificar que el tablero se actualiza
3. Si OK → PR a main → merge

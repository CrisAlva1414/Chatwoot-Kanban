# Sesión 009 — Performance: board loading, Chatwoot API calls, frontend polling

- **Fecha:** 2026-07-23
- **Propósito:** Reducir latencia en carga del tablero, creación/modificación de tareas y polling 30s sin cambios estructurales en BD.

## Contexto

El tablero Kanban sufría de:

1. **Board load lento**: Por cada tarjeta en el tablero se ejecutaba una query BD individual (`sync_task_from_chatwoot` por cada card → N+1 queries). Las etapas se cargaban secuencialmente.
2. **Crear/Editar/Cerrar tarea**: Cada operación hacía 2 llamadas a la API de Chatwoot (GET + POST) cuando el POST mergea igualmente.
3. **Polling 30s**: Recargaba el board completo aunque el tablero estuviera en una tab oculta.
4. **Attribute definitions**: Se fetcheaban en cada request sin caché.

## Cambios realizados

### 1. Batch sync en board loading (`app/database.py` + `app/routers/kanban.py`)

**Problema:** `sync_task_from_chatwoot()` se llamaba por cada tarjeta → N queries BD individuales.

**Solución:** Nueva función `batch_sync_tasks_from_chatwoot()` que recibe todas las tarjetas de una etapa y ejecuta batch upserts con `executemany` (3 queries: updates, creates, closes).

### 2. Skip read en `safe_update_custom_attributes` (`app/chatwoot_client.py` + `app/routers/kanban.py`)

**Problema:** `safe_update_custom_attributes()` leía atributos existentes (GET) antes de hacer POST, cuando Chatwoot mergea server-side.

**Solución:** Parámetro `skip_read=True` — POST directo sin GET previo. Seguro porque solo enviamos nuestros 3 keys conocidos (`pipeline_01_etapas`, `kanban_view_mensaje`, `kanban_view_fecha_termino`) y Chatwoot mergea con el resto.

Aplicado en: `move_stage`, `create_task`, `update_task_endpoint`, `close_task_endpoint`, `cron_tick`.

### 3. Cache de attribute definitions (`app/chatwoot_client.py`)

**Problema:** `get_custom_attribute_definitions()` se llamaba en cada request a `/board`, `/config`, `/debug-status`, `move_stage`.

**Solución:** Cache en memoria con TTL de 5 minutos.

### 4. Paralelización de etapas (`app/routers/kanban.py`)

**Problema:** Las etapas se cargaban secuencialmente en `kanban_board()`.

**Solución:** Extraída lógica a `_load_stage()` y ejecutada con `asyncio.gather()` para carga paralela.

### 5. Polling inteligente con Page Visibility API (`app/templates/kanban.html`)

**Problema:** Polling 30s se ejecutaba incluso en tabs ocultas.

**Solución:** Listener `visibilitychange` que pausa polling cuando el tab no está visible y refresca inmediatamente al volver.

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `app/chatwoot_client.py` | +cache TTL 5min en `get_custom_attribute_definitions` + parámetro `skip_read` en `safe_update_custom_attributes` |
| `app/database.py` | Nueva función `batch_sync_tasks_from_chatwoot` + `skip_read=True` en `cron_tick` |
| `app/routers/kanban.py` | Import `asyncio` + `batch_sync_tasks_from_chatwoot`; `skip_read=True` en todos los endpoints de tareas; `kanban_board` refactorizado con `asyncio.gather` + batch sync |
| `app/templates/kanban.html` | Page Visibility API — polling se pausa en tabs ocultas, refresca al volver |
| `tests/conftest.py` | Fixtures actualizadas a `batch_sync_tasks_from_chatwoot` |
| `docs/sesiones/009-2026-07-23-performance-board-pooling-cache.md` | Creado |

## Decisiones

- No se requirió nuevo ADR — son optimizaciones de código existente sin cambios arquitectónicos.
- `executemany` de asyncpg usado para batch upserts (disponible desde asyncpg 0.21).
- `skip_read` es seguro porque la API de Chatwoot mergea custom_attributes via POST; no necesitamos leer antes a menos que debamos preservar keys que no enviamos.

## Próximo paso

1. Monitorear latencia en staging tras deploy
2. Confirmar que el cron tick nocturno funciona correctamente con `skip_read`
3. Considerar migrar a `INSERT … ON CONFLICT` si `executemany` muestra cuello de botella en tableros grandes

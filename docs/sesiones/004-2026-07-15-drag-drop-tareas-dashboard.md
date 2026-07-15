# Sesión 004 — Drag & Drop fix, sistema de tareas y dashboard

- **Fecha:** 2026-07-15
- **Propósito:** Corregir el drag & drop (no actualizaba Chatwoot), implementar
  el sistema de tareas 1:1 con conversaciones, cron para transiciones, y
  dashboard de métricas de agentes.

## Contexto

El Kanban mostraba conversaciones correctamente pero el drag & drop tenía
un bug crítico: el frontend llamaba directo a la API de Chatwoot sin pasar
por el backend, lo que impedía el audit trail y la sincronización con la BD
propia. Además, el sistema de tareas (definido en ADR-005) no tenía endpoints
ni UI implementada.

## Cambios realizados

### 1. Fix drag & drop (bug en producción)

**Problema:** El frontend hacía `POST /api/conversations/{id}/custom-attributes`
directo a Chatwoot. Al soltar, borraba el card y ponía un placeholder vacío.
Si fallaba, no había rollback.

**Fix:**
- Nuevo endpoint `PATCH /kanban/board/{conversation_id}/stage`
- Valida etapa destino contra las definiciones de Chatwoot
- Escribe `task_audit_log` con `action='stage_change'`
- Llama a `chatwoot_client.update_custom_attributes()`
- Frontend usa el nuevo endpoint, mueve el card al DOM sin placeholder
- Toast de error si falla, card se queda en su posición original

### 2. Sistema de tareas 1:1

Relación exacta 1 conversación : 1 tarea activa. Si se crea una nueva
para una conversación que ya tiene una, se sobrescribe (UPDATE).

**Endpoints:**
| Método | Ruta | Propósito |
|--------|------|-----------|
| `POST` | `/kanban/tasks` | Crear/sobrescribir tarea. Sync a Chatwoot |
| `PATCH` | `/kanban/tasks/{id}` | Editar mensaje/fecha |
| `PATCH` | `/kanban/tasks/{id}/close` | Cerrar tarea |
| `GET` | `/kanban/tasks` | Verificar tarea por conversation_id |

**Custom attributes en Chatwoot (espejo):**
- `tarea_estado`: estado actual (tarea_activa, tarea_hoy, tarea_vencida, tarea_cerrada)
- `tarea_vencimiento`: fecha límite

**BD propia (fuente de verdad):** tabla `tareas` existente, sin cambios
estructurales.

**Sobrescribir tarea:** Genera `action='task_overwritten'` en audit log
con `previous_state` que incluye quién creó la tarea original.

### 3. Integración tareas en el board

`GET /kanban/board` ahora incluye en cada card:
```json
{
  "task": {
    "id": 45,
    "estado": "tarea_activa",
    "mensaje": "Enviar propuesta",
    "fecha_vencimiento": "2026-07-20",
    "creado_por": "María"
  }
}
```

El frontend muestra badges de color por estado de tarea (azul=activa,
ámbar=hoy, rojo=vencida).

### 4. Cron para transiciones automáticas

`POST /kanban/cron/tick` ejecutado por cron externo a las 23:30:
- `tarea_activa` → `tarea_hoy` (cuando `fecha_vencimiento <= hoy`)
- `tarea_hoy` → `tarea_vencida`
- Reintenta filas con `sync_pendiente = true`
- Cada transición escribe audit log con `source='cron'`

### 5. Dashboard de agentes

Página separada `/kanban/dashboard` con botón "Volver al Kanban".
Métricas calculadas desde `task_audit_log`:
- Resumen: tareas creadas, cerradas, sobrescritas, agentes activos
- Tabla por agente: creadas, cerradas, sobrescritas, cierre OK
- Historial reciente de acciones

**Endpoints:**
| Método | Ruta | Propósito |
|--------|------|-----------|
| `GET` | `/kanban/stats` | Métricas por agente |
| `GET` | `/kanban/stats/history` | Últimas 50 acciones del audit log |

### 6. Database helpers

Nuevas funciones en `database.py`:
- `get_or_create_agent()` — lookup o insert de agente por email
- `write_audit_log()` — insert en `task_audit_log`
- `upsert_task()` — crear o actualizar tarea 1:1
- `edit_task()` / `close_task()` — modificar estado de tarea
- `get_active_task()` / `get_tasks_for_conversations()` — queries de tarea
- `cron_tick()` — transiciones automáticas + sync reconciliación
- `get_agent_stats()` / `get_audit_history()` — métricas para dashboard

## ADR

- **ADR-012 creado:** Operaciones de escritura en el Kanban y sistema de tareas.
  Define: intermediación del backend en escrituras, relación 1:1, sync con
  Chatwoot, cron a las 23:30, dashboard de métricas.
- **ADR-005 sin cambios:** La definición original del modelo de datos sigue
  vigente. El constraint `UNIQUE(conversation_id)` ya existía.

## Tests

29 tests pasando (17 existentes + 12 nuevos):
- `test_move_stage_ok` / `test_move_stage_invalid` / `test_move_stage_chatwoot_error`
- `test_create_task` / `test_create_task_overwrite`
- `test_close_task` / `test_close_task_not_found`
- `test_get_tasks`
- `test_stats_endpoint` / `test_stats_history_endpoint`
- `test_cron_tick_endpoint`
- `test_dashboard_page`

## Archivos tocados

**Modificados:**
- `app/database.py` — 10 funciones helper nuevas (agentes, audit, tareas, cron, stats)
- `app/routers/kanban.py` — PATCH stage, endpoints de tareas, cron, stats, dashboard
- `app/templates/kanban.html` — frontend usa nuevo endpoint PATCH, badges de tarea, toast, botón dashboard
- `tests/conftest.py` — mock de `get_tasks_for_conversations` en fixtures
- `tests/test_kanban.py` — 12 tests nuevos
- `docs/README.md` — referencia a ADR-012

**Nuevos:**
- `app/templates/dashboard.html` — dashboard de agentes
- `docs/adr/012-operaciones-escritura-kanban.md` — ADR del sistema de tareas

## Próximo paso

- Configurar cron job en el NAS (23:30 diarias, `POST /kanban/cron/tick`)
- Conectar Cloudflare Access para atribución real de agentes
- Evaluar: ¿crear tarea desde el Kanban con un botón por card?

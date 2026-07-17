# Sesión 007 — Fix fechas, estado on-the-fly, drag & drop y polling

- **Fecha:** 2026-07-17
- **Propósito:** Corregir el off-by-one de fechas (se mostraba un día antes),
  calcular el estado de las tareas on-the-fly en el frontend, mejorar el drag &
  drop para no perder el badge de tarea, eliminar el título del dashboard y
  agregar polling de sincronización.

## Contexto

En producción se observaron varios bugs menores:
1. Las fechas se guardaban con `T04:00:00.000Z` lo que en Chile mostraba el día
   anterior.
2. El badge de tarea desaparecía al hacer drag & drop porque `setupDropZone`
   reconstruía el cardData sin el task.
3. El estado de las tareas (vencida, cerrada, etc.) se calculaba con
   `cron_tick` y podía quedar desactualizado.
4. El título "Dashboard de Agentes" era redundante con el iframe.
5. No había polling para ver cambios de otros agentes en tiempo real.

## Cambios realizados

### 1. Fix off-by-one de fechas

**Problema:** Las fechas se guardaban con `T04:00:00.000Z` (medianoche Chile
≈ 4am UTC), causando que Chatwoot mostrara el día anterior.

**Fix:** Cambiar a `T23:59:59.999Z` para que la fecha mostrada siempre sea
correcta.

**Archivos:**
- `app/routers/kanban.py` — create_task, update_task
- `app/database.py` — cron_tick
- `tests/conftest.py` — mock data
- `tests/test_kanban.py` — assertions

### 2. Estado on-the-fly (computeTaskEstado)

**Problema:** El estado dependía del campo `estado` en la BD o del
`cron_tick`, que podía estar desactualizado.

**Fix:** Crear `computeTaskEstado(task)` en el frontend que calcula el estado
en tiempo real con lógica de 24h:
- `tarea_cerrada`: cerrado en las últimas 24h
- `tarea_vencida`: vencida hace más de 24h
- `tarea_hoy`: vence hoy
- `tarea_activa`: tiene fecha futura
- `null`: task expirada (>24h vencida o cerrada)

**Archivos:**
- `app/templates/kanban.html` — computeTaskEstado, renderTaskBadge,
  renderColumns, openTaskModal, event listeners

### 3. Fix drag & drop (guardar/restaurar task)

**Problema:** Al hacer drag & drop, `setupDropZone` reconstruía el cardData
desde el DOM pero no incluía el task, por lo que el badge desaparecía.

**Fix:**
- `createCard()`: guardar `el.dataset.task = JSON.stringify(card.task)`
- `setupDropZone()`: restaurar `task: draggable.dataset.task ?
  JSON.parse(draggable.dataset.task) : null`

**Archivos:**
- `app/templates/kanban.html` — createCard, setupDropZone

### 4. Query de tareas incluye cerradas recientes

**Problema:** Las tareas cerradas desaparecían inmediatamente del Kanban.

**Fix:** Agregar `OR t.cerrado_en >= now() - interval '24 hours'` a la query
`get_tasks_for_conversations` para mantener tareas cerradas visibles por 24h.

**Archivos:**
- `app/database.py` — get_tasks_for_conversations

### 5. Eliminar título dashboard

**Cambio:** Remover `<h1>Dashboard de Agentes</h1>` del template.

**Archivos:**
- `app/templates/dashboard.html`
- `tests/test_kanban.py` — test_dashboard_page

### 6. Polling de sincronización

**Funcionalidad:** Agregar `setInterval` cada 30s que llama `loadBoard()` y
`renderBoard()` para reflejar cambios de otros agentes.

- Se pausa cuando hay un modal abierto (`currentModalCardId`)
- Se reinicia al cerrar el modal

**Archivos:**
- `app/templates/kanban.html` — startPolling, stopPolling, init, openTaskModal,
  closeTaskModal

## Verificación

- `ruff check .` → OK
- `ruff format --check .` → OK
- `pytest -v` → 29 passed

## Siguiente sesión

- Evaluar performance del polling (¿diferencial vs full refresh?)
- Confirmar que el fix de fechas funciona en Chile (prueba en producción)

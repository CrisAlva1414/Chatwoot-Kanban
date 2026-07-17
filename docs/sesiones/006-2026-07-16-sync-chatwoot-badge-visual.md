# Sesión 006 — Sync con Chatwoot y badge visual de tareas

- **Fecha:** 2026-07-16
- **Propósito:** Alinear los custom attributes del código con los creados en
  Chatwoot (`kanban_view_mensaje`, `kanban_view_fecha_termino`), corregir el
  bug de fechas que mostraba "hace 20630d", y agregar un badge visual en las
  cards del Kanban para ver la fecha de vencimiento de la tarea.

## Contexto

Los custom attributes creados en Chatwoot eran `kanban_view_mensaje` y
`kanban_view_fecha_termino`, pero el código usaba `tarea_estado` y
`tarea_vencimiento`. Además, el `updated_at` de Chatwoot es un Unix timestamp
en segundos, pero JavaScript `new Date()` lo interpretaba como milisegundos,
resultando en una fecha de 1970 (≈ 20630 días).

## Cambios realizados

### 1. Fix del bug de fechas (timeAgo)

**Problema:** `updated_at` de Chatwoot viene como Unix timestamp en segundos
(ej: `1784258149`). JavaScript `new Date(1784258149)` lo interpreta como
milisegundos → 21 enero 1970 → "hace 20630d".

**Fix:** Detectar si el valor es numérico de 10 dígitos (timestamp en segundos)
y multiplicar por 1000:

```javascript
function timeAgo(dateStr) {
  if (!dateStr) return '';
  let d;
  if (typeof dateStr === 'number' || /^\d{10}(\.\d+)?$/.test(String(dateStr))) {
    d = new Date(Number(dateStr) * 1000);
  } else {
    d = new Date(dateStr);
  }
  // ...
}
```

### 2. Actualización de custom attribute keys

| Antes (incorrecto) | Ahora (correcto) |
|---------------------|------------------|
| `tarea_estado` | `kanban_view_mensaje` |
| `tarea_vencimiento` | `kanban_view_fecha_termino` |

**Archivos modificados:**
- `app/routers/kanban.py` — constantes `TASK_MSG_ATTR_KEY` y `TASK_DATE_ATTR_KEY`
- `app/database.py` — `cron_tick()` usa `kanban_view_fecha_termino`
- `app/templates/kanban.html` — frontend lee los nuevos keys
- `tests/conftest.py` — mock data actualizado
- `tests/test_kanban.py` — assertion actualizada

### 3. Formato ISO 8601 para Chatwoot

Las fechas se envían a Chatwoot como ISO 8601 con timezone UTC:
```python
fecha_iso = body.fecha_vencimiento.isoformat() + "T04:00:00.000Z"
```

Chatwoot almacena y devuelve: `"2026-07-20T04:00:00.000Z"`

### 4. Sync al cerrar tarea

Al cerrar una tarea, se limpian ambos atributos en Chatwoot:
```python
await chatwoot_client.update_custom_attributes(
    conv_id, {TASK_MSG_ATTR_KEY: "", TASK_DATE_ATTR_KEY: ""}
)
```

### 5. Badge visual de fecha en cards

Nuevo badge con rectángulo redondeado (border-radius: 12px) que muestra:
- Icono de calendario (📅)
- Fecha de vencimiento en formato local (DD/MM/YYYY)
- Color amber si está activa, rojo si está vencida
- Tooltip con el mensaje de la tarea al hacer hover

```css
.card-task {
  border-radius: 12px;
  background: rgb(var(--amber) / 0.12);
  color: rgb(180 120 0);
  border: 1px solid rgb(var(--amber) / 0.25);
}
.card-task.overdue {
  background: rgb(var(--red) / 0.1);
  color: rgb(var(--red));
  border-color: rgb(var(--red) / 0.25);
}
```

### 6. Filtro de tareas actualizado

El filtro de estado ahora usa datos de la BD (campo `task.estado`) en vez
de `custom_attributes.tarea_estado`. Se agregó opción "Sin tarea" al
selector.

### 7. Eliminación de sync de estado

Ya no se sincroniza `tarea_estado` a Chatwoot (no existe el atributo).
El estado de la tarea (activo/hoy/vencida/cerrada) solo vive en la BD.

## Archivos tocados

**Modificados:**
- `app/routers/kanban.py` — keys, formato ISO, sync al cerrar
- `app/database.py` — `cron_tick()` con nuevo key
- `app/templates/kanban.html` — fix timeAgo, badge visual, tooltip, filtro
- `tests/conftest.py` — mock data actualizado
- `tests/test_kanban.py` — assertion de custom_attributes

## Tests

29 tests pasando (sin cambios en la suite, solo actualizados fixtures y
assertions).

## Próximo paso

- Desplegar y verificar en producción que:
  1. El badge de fecha se muestra correctamente en las cards
  2. El tooltip muestra el mensaje de la tarea
  3. La fecha "hace 20630d" ya no aparece
  4. Al crear/editar tarea, Chatwoot muestra los atributos
  5. Al cerrar tarea, Chatwoot limpia los atributos

---

## Hotfix: Read-Merge-Write para custom attributes (crítico)

### Problema

**Los leads desaparecían del Kanban después de crear una tarea.**

Chatwoot en algunas versiones hace **REPLACE** (no MERGE) al recibir
`POST /conversations/{id}/custom_attributes`. Al enviar solo los atributos
de tarea (`kanban_view_mensaje`, `kanban_view_fecha_termino`), se borraba
`pipeline_01_etapas` → el lead no aparecía en ninguna columna.

Había 5 puntos vulnerables:
1. `create_task` → borraba `pipeline_01_etapas`
2. `update_task` → borraba `pipeline_01_etapas`
3. `close_task` → borraba `pipeline_01_etapas`
4. `move_stage` → borraba `kanban_view_*`
5. `cron_tick` → borraba todo

### Fix: safe_update_custom_attributes

Nuevo método en `chatwoot_client.py` que implementa read-merge-write:

```python
async def safe_update_custom_attributes(
    self, conversation_id: int, attributes: dict
) -> dict:
    # 1. GET atributos actuales
    conv = await self.get_conversation(conversation_id)
    existing = conv.get("custom_attributes") or {}
    # 2. MERGE: existentes + nuevos
    merged = {**existing, **attributes}
    # 3. POST el resultado completo
    return await self.update_custom_attributes(conversation_id, merged)
```

**Fallback:** Si falla la lectura, envía el update parcial (mejor que nada).

### Archivos modificados

- `app/chatwoot_client.py` — `get_conversation()` + `safe_update_custom_attributes()`
- `app/routers/kanban.py` — 4 call sites actualizados
- `app/routers/api.py` — 1 call site actualizado
- `app/database.py` — `cron_tick()` actualizado
- `app/templates/kanban.html` — reset del filtro de estado después de crear/editar/cerrar tarea
- `tests/test_kanban.py` — mocks actualizados

# ADR-005 — Modelo de datos de tareas: BD propia + espejo único en Chatwoot

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-07-09 |
| **Proyecto** | kanban.ruki-bot.com |
| **Decidido por** | Sesión de factibilidad técnica inicial |

---

## Contexto

El sistema de tareas requiere almacenar: mensaje de la misión, fecha de creación, fecha de vencimiento, estado actual, y atribución (creador/cerrador). Se evaluó dónde debe vivir cada dato considerando que Chatwoot soporta custom attributes de tipo `Text`, `Date`, `List` y `Number` sobre conversaciones.

Se exploraron dos enfoques:

**Opción A — Todo en custom_attributes de Chatwoot:** cada campo de la tarea es un custom_attribute propio (`tarea_mensaje`, `tarea_vencimiento`, `tarea_creada_en`, `tarea_creador`, `tarea_estado`). Chatwoot es fuente de verdad completa.

**Opción B — BD propia como fuente de verdad, Chatwoot solo recibe espejo de estado:** el contenido real de la tarea (mensaje, fechas, atribución) vive en la BD del backend. Solo `tarea_estado` (tipo `List`) se replica en Chatwoot.

## Decisión

**Opción B.** Un único custom_attribute `tarea_estado` en Chatwoot. Todo el contenido real en BD propia.

## Fundamento técnico

La elección de Opción B se tomó al confirmar que:

1. El backend propio ya es requerido por otras decisiones (ADR-002, ADR-003, ADR-004). El costo marginal de una tabla más es mínimo.
2. Usar 5 custom_attributes en vez de 1 implica que cada operación de crear/cerrar tarea requiere escribir 5 campos — aunque la API acepta múltiples keys en un solo POST, el acoplamiento con el schema de Chatwoot crece y cualquier renaming de campo requiere migración en Chatwoot y en el código.
3. El único valor que necesita vivir en Chatwoot es `tarea_estado`, porque es el campo que se usa como filtro en `/conversations/filter` para agrupar las tarjetas del Kanban sin consultar la BD propia.

## Reglas de negocio fijadas

- **1 tarea activa por conversación a la vez.** Si ya existe una tarea en estado distinto de `tarea_cerrada` o `null`, el backend rechaza la creación de una nueva.
- **Estados y transiciones:**
  ```
  null → tarea_activa  (creación manual)
  tarea_activa → tarea_hoy   (cron, cuando fecha_vencimiento == hoy)
  tarea_hoy    → tarea_vencida (cron a las 23:30 si no fue cerrada)
  tarea_activa / tarea_hoy → tarea_cerrada (acción manual desde el Kanban)
  ```
- **Pool rotativo:** cualquier agente puede crear o cerrar la tarea de cualquier conversación. No hay ownership de lead.
- **Cron a las 23:30:** detecta tareas no cerradas cuya `fecha_vencimiento <= hoy` y las transiciona a `tarea_vencida`. La transición es silenciosa (no genera nota en Chatwoot).

## Nota sobre private notes (descartadas)

Se evaluó usar una private note con prefijo `[TAREA]` como "contenedor del mensaje" de la tarea, aprovechando el historial nativo de mensajes de Chatwoot. Se descartó porque:
- Introduce una segunda llamada a la API por operación (crear nota + actualizar custom_attribute) aumentando la ventana de inconsistencia.
- Requiere guardar el `message_id` en la BD para referencia directa, complejizando el modelo sin beneficio neto dado que el backend ya existe.
- El historial de tareas se resuelve más limpiamente con el audit log propio (ADR-004).

## Schema de tabla de tareas

```sql
CREATE TABLE tareas (
  id               BIGSERIAL PRIMARY KEY,
  conversation_id  INTEGER NOT NULL UNIQUE,  -- UNIQUE: garantiza 1 tarea activa por conversación
  mensaje          TEXT NOT NULL,
  fecha_vencimiento DATE NOT NULL,
  estado           TEXT NOT NULL DEFAULT 'tarea_activa',
  creado_por       INTEGER NOT NULL REFERENCES agentes(id),
  cerrado_por      INTEGER REFERENCES agentes(id),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  cerrado_en       TIMESTAMPTZ,
  sync_pendiente   BOOLEAN NOT NULL DEFAULT false  -- true si el POST a Chatwoot falló
);
```

## Punto de fragilidad y mitigación

Cada operación implica 2 pasos no atómicos: escritura en la BD propia + POST al custom_attribute de Chatwoot. Si el POST a Chatwoot falla:
- El estado real en la BD es correcto.
- El espejo en Chatwoot está desactualizado.
- `sync_pendiente = true` marca la fila para reintento.

Mitigación: el backend reintenta el POST a Chatwoot hasta 3 veces con backoff exponencial. Si todos los reintentos fallan, marca `sync_pendiente = true` y lo resuelve en el siguiente ciclo del cron o en una tarea de reconciliación. No se falla en silencio.

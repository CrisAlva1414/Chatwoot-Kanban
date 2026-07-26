# ADR-006 — Kanban de pipeline sobre custom_attributes de conversación

| Campo | Valor |
|---|---|
| **Estado** | Parcialmente suplantado por ADR-016 |
| **Fecha** | 2026-07-09 |
| **Proyecto** | kanban.ruki-bot.com |
| **Decidido por** | Sesión de factibilidad técnica inicial |
| **Suplantado por** | ADR-016 (modelo contact-based desde 2026-07-26) |

---

## Contexto

Chatwoot no tiene una vista Kanban nativa por etapas de pipeline. El objetivo es construir una vista que permita ver conversaciones (leads) agrupadas por etapa dentro de un pipeline seleccionable, con capacidad de mover tarjetas entre etapas mediante drag & drop.

## Decisión

Usar **custom_attributes de tipo `List` sobre conversaciones** como fuente de datos del Kanban. Dos custom_attributes relevantes: `pipeline` (selector de pipeline activo) y `pipeline_stage` (etapa dentro del pipeline). El Kanban se alimenta de la API `/conversations/filter`.

## Jerarquía de filtros de la vista

```
[Selector de Pipeline ▼]         ← filtra por valor de custom_attribute 'pipeline'
   └── Columnas = etapas          ← valores del List 'pipeline_stage' para ese pipeline
         └── [Filtro tarea_estado ▼]  ← capa adicional sobre el mismo query
               └── Tarjetas = conversaciones que cumplen ambos criterios
```

El filtro de `tarea_estado` y el de `pipeline_stage` se combinan en un **único request** a `/conversations/filter` con ambos `attribute_key` en el payload, no en dos llamadas separadas.

## Endpoints utilizados

| Operación | Endpoint | Notas |
|---|---|---|
| Definiciones de custom attributes | `GET /api/v1/accounts/{id}/custom_attribute_definitions` | Confirma keys exactos y valores válidos. Se cachea en arranque. |
| Leer conversaciones por stage | `POST /api/v1/accounts/{id}/conversations/filter` | Filtra por `pipeline` + `pipeline_stage` + `tarea_estado` en un solo request |
| Mover tarjeta (drag & drop) | `POST /api/v1/accounts/{id}/conversations/{id}/custom_attributes` | Actualiza `pipeline_stage` al soltar la tarjeta |
| Sincronización entre agentes | Webhook `conversation_updated` | Detecta cambios de stage hechos por otros agentes |

## Limitaciones identificadas

1. **Webhook `conversation_updated` tiene bugs históricos de disparo duplicado** (issue #7402). La lógica de actualización del Kanban debe ser idempotente: dedup por `conversation.id + updated_at` antes de refrescar la tarjeta.
2. **Inconsistencias de schema en el payload del webhook** entre versiones de Chatwoot (issue #13993). Validar defensivamente con Pydantic — no asumir campos opcionales como presentes.
3. **Paginación de `/conversations/filter`:** la paginación estándar aplica (Chatwoot no tiene cursor-based para este endpoint). Con volumen alto por columna, se requiere cacheo o paginación lazy en el frontend. No es un problema para el volumen actual del equipo.
4. **Chatwoot no soporta valores condicionales de List** (ej. mostrar solo las etapas válidas para el pipeline seleccionado basado en el valor de otro custom_attribute). Los valores disponibles de `pipeline_stage` son los mismos independientemente del pipeline seleccionado. La separación por pipeline se mantiene en config propia del frontend o del backend, no en Chatwoot.

## Consecuencias

- El drag & drop es pura lógica de frontend (librería `dnd-kit` o similar). El drop dispara un POST al backend, que a su vez llama a Chatwoot. Chatwoot no tiene restricciones sobre esto.
- El Kanban no tiene backend propio de estado: la fuente de verdad de en qué etapa está cada lead siempre es Chatwoot. No se sincroniza ni cachea el stage en la BD propia.
- La vista de tareas **no es un Kanban separado** — es un filtro adicional (por `tarea_estado`) sobre el mismo Kanban de pipeline.

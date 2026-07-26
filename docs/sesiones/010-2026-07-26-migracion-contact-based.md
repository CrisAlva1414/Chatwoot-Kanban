# Sesión 010 — Migración conversation-based → contact-based

- **Fecha:** 2026-07-26
- **Propósito:** Migrar la integración Kanban de custom attributes de conversación a custom attributes de contacto, eliminando duplicación de contactos en el tablero.

## Contexto

El Kanban mostraba conversaciones como tarjetas. Un mismo contacto con múltiples conversaciones (WhatsApp, Instagram, Email) aparecía repetidamente en el tablero, causando:
- Duplicación visual de contactos
- Inestabilidad en las tareas (asociadas a conversaciones, no a personas)
- Fricción operativa para los agentes

## Pruebas de API realizadas

Antes de implementar, se validaron los endpoints reales de Chatwoot:

| Endpoint | Método | Resultado |
|----------|--------|-----------|
| `/custom_attribute_definitions` | GET | Confirmados 7 atributos: 3 conversation + 3 contact + 1 contact (pipeline_02) |
| `/contacts/filter` | POST | Funciona con paginación, shape plano (name, thumbnail directos) |
| `/contacts/{id}` | PATCH | **Mergea** custom_attributes, no sobreescribe |
| `/contacts/{id}/custom_attributes` | POST | **404** — no existe este endpoint |
| `/contacts/{id}/conversations` | GET | Devuelve conversaciones del contacto |

**Hallazgo clave:** Los custom attributes de contacto ya existían en Chatwoot (ids 6, 7, 9) pero estaban vacíos. Los de conversación (ids 1, 4, 5) seguían activos.

**Datos a migrar:** ~323 conversaciones distribuidas en 6 etapas, ~187 contactos totales.

## Cambios realizados

### 1. `app/chatwoot_client.py`

Nuevos métodos para operaciones sobre contactos:
- `filter_contacts(payload, page)` — POST `/contacts/filter`
- `get_contact(contact_id)` — GET `/contacts/{id}`
- `get_contact_conversations(contact_id)` — GET `/contacts/{id}/conversations`
- `update_contact_custom_attributes(contact_id, attrs)` — PATCH `/contacts/{id}`
- `safe_update_contact_custom_attributes(contact_id, attrs, skip_read)` — con merge

### 2. `app/database.py`

- Tabla `tareas`: nueva columna `contact_id`, `conversation_id` pasa a nullable
- UNIQUE migrado de `conversation_id` a `contact_id` (partial index)
- Función `_migrate_schema()` para migración automática al arrancar
- `write_audit_log`: `contact_id` como parámetro principal
- `upsert_task`: recibe `contact_id` + `conversation_id` (opcional)
- `get_active_task(contact_id)` en vez de `get_active_task(conversation_id)`
- `get_tasks_for_contacts(contact_ids)` reemplaza `get_tasks_for_conversations`
- `cron_tick`: sincroniza contra contacto
- `sync_task_from_chatwoot` y `batch_sync`: operan sobre `contact_id`

### 3. `app/routers/kanban.py`

- `kanban_board()` usa `filter_contacts` en vez de `filter_conversations`
- `_normalize_contact()` reemplaza `_normalize_conversation()`
- `move_stage(contact_id)` actualiza atributos del contacto
- `create_task/update/close`: operan sobre `contact_id`
- `CreateTaskRequest`: `contact_id` en vez de `conversation_id`
- URL: `/board/{contact_id}/stage`
- `_find_pipeline_attribute`: prioriza `contact_attribute` sobre `conversation_attribute`
- Board response: `contacts` en vez de `conversations`

### 4. `app/routers/webhooks.py`

- Nuevo handler `POST /webhooks/contact-updated` para evento `contact_updated`
- Handler `conversation-updated` mantenido (legacy) pero sin sync de tareas
- Ambos extraen `contact_id` del payload

### 5. `app/routers/api.py`

- Nuevo endpoint `POST /api/contacts/{contact_id}/custom-attributes`
- Endpoint de conversaciones mantenido (legacy)

### 6. `app/routers/migrate.py` (nuevo)

- `POST /migrate/contact-attributes` — migra atributos de conversación a contacto
- `POST /migrate/db-tasks-only` — migra solo tareas de BD sin contacto asignado
- `GET /migrate/status` — estado de la migración

### 7. `app/templates/kanban.html`

- Tarjetas muestran contacto (name, thumbnail directos)
- API calls usan `contact_id`
- Link a Chatwoot abre `/contacts/{id}/conversations`
- `data-contact-id` reemplaza `data-conversation-id`
- `last_activity_at` reemplaza `updated_at`
- Eliminado `last_message` (no disponible en contactos)

### 8. Tests

- `conftest.py`: mocks actualizados a contactos (`filter_contacts`, shape plano)
- `test_kanban.py`: 25 tests migrados a contact-based
- `test_webhooks.py`: nuevos tests para `contact-updated` + legacy `conversation-updated`
- **31 tests pasan, 0 fallan**

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `app/chatwoot_client.py` | +5 métodos de contacto |
| `app/database.py` | Schema migration + refactor queries |
| `app/routers/kanban.py` | Reescrito completo (contact-based) |
| `app/routers/webhooks.py` | Reescrito (contact-updated + legacy) |
| `app/routers/api.py` | +endpoint contactos |
| `app/routers/migrate.py` | **Nuevo** — endpoints de migración |
| `app/main.py` | +include migrate router |
| `app/templates/kanban.html` | Migrado a contact-based |
| `tests/conftest.py` | Mocks actualizados |
| `tests/test_kanban.py` | Tests migrados |
| `tests/test_webhooks.py` | Tests actualizados + nuevos |
| `docs/adr/016-migracion-conversation-a-contact-based.md` | **Nuevo** |
| `docs/sesiones/010-2026-07-26-migracion-contact-based.md` | **Nuevo** |

## Decisiones

- **ADR-016 creado**: documenta la decisión de migrar a contact-based
- **Coexistencia temporal**: ambos sets de custom attributes viven en Chatwoot durante la transición
- **conversation_id nullable**: se mantiene como campo informativo en la tabla `tareas`
- **Mismo key**: `pipeline_01_etapas` se reutiliza como contact_attribute (no se crea nuevo key)
- **Migración en caliente**: script idempotente ejecutable una vez vía endpoint HTTP

## Próximo paso

1. Deploy a staging (develop → Arcane)
2. Ejecutar `POST /migrate/contact-attributes` en staging
3. Verificar tablero con contactos
4. Ejecutar `POST /migrate/db-tasks-only` para tareas sin contacto
5. Verificar `GET /migrate/status` — confirmar migración completa
6. Probar drag & drop, crear/cerrar tareas
7. Si todo OK → PR a main → deploy a producción
8. Post-validación: eliminar custom attributes de conversación (ids 1, 4, 5)

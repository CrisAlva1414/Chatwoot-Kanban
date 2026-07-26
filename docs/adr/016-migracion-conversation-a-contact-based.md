# ADR-016: Migración de conversation-based a contact-based

- **Fecha:** 2026-07-26
- **Estado:** Aceptado
- **Autor(es):** Sesión 010
- **Suplanta:** ADR-006 (parcialmente, para el modelo de datos del Kanban)

## Contexto

Los custom attributes del Kanban (`pipeline_01_etapas`, `kanban_view_mensaje`,
`kanban_view_fecha_termino`) estaban definidos como `conversation_attribute` en
Chatwoot. Un mismo contacto puede tener múltiples conversaciones (distintas
redes sociales: WhatsApp, Instagram, Email), lo que causaba:

1. **Duplicación en el tablero**: el mismo contacto aparecía múltiples veces
   (una por cada conversación con atributos poblados).
2. **Inestabilidad de tareas**: las tareas se asociaban a conversaciones,
   no a personas, causando inconsistencia cuando un contacto tenía tareas
   en distintas conversaciones.
3. **Fricción operativa**: los agentes no podían ver el estado real del
   pipeline de un contacto sin revisar todas sus conversaciones.

Ejemplo real: el contacto "Hanyi Rosales" (id:215) tenía 3 conversaciones
en la etapa "Contactado", "Fresia Pacheco" (id:207) tenía 3, etc.

## Decisión

Migrar toda la integración a **custom attributes de contacto**
(`contact_attribute`). Las tarjetas del Kanban pasan a ser contactos,
no conversaciones. Cada contacto aparece una sola vez independientemente
de cuántas conversaciones tenga.

### Cambios técnicos

| Componente | Antes | Después |
|------------|-------|---------|
| Custom attributes | `conversation_attribute` | `contact_attribute` |
| Tarjetas del Kanban | Conversaciones | Contactos |
| Identificador principal | `conversation_id` | `contact_id` |
| API de filtrado | `/conversations/filter` | `/contacts/filter` |
| API de escritura | `POST /conversations/{id}/custom_attributes` | `PATCH /contacts/{id}` |
| Tabla `tareas` UNIQUE | `conversation_id` | `contact_id` |
| Webhook principal | `conversation_updated` | `contact_updated` |
| Link a Chatwoot | `/conversations/{id}` | `/contacts/{id}/conversations` |

### Coexistencia temporal

Durante la transición, ambos sets de custom attributes coexisten en Chatwoot:
- `conversation_attribute` (ids 1, 4, 5) — legacy, se eliminarán post-migración
- `contact_attribute` (ids 6, 7, 9) — nuevos, fuente de verdad

La migración de datos se realiza mediante el endpoint `POST /migrate/contact-attributes`
que:
1. Itera todas las conversaciones con `pipeline_01_etapas` poblado
2. Agrupa por `contact_id`
3. Toma la conversación con `updated_at` más reciente
4. PATCH al contacto con sus custom attributes
5. Migra las tareas de la BD propia de `conversation_id` a `contact_id`

### Schema de BD

```sql
-- Antes
CREATE TABLE tareas (
  conversation_id INTEGER NOT NULL UNIQUE,
  ...
);

-- Después
CREATE TABLE tareas (
  contact_id      INTEGER,
  conversation_id INTEGER,  -- nullable, informativo
  ...
);
CREATE UNIQUE INDEX idx_tareas_contact_id
  ON tareas (contact_id) WHERE contact_id IS NOT NULL;
```

## Consecuencias

- **Positivas:**
  - Cada contacto aparece una sola vez en el Kanban
  - Las tareas son estables y se asocian a personas, no a conversaciones
  - El estado del pipeline es consistente por contacto
  - Menos tarjetas en el tablero (187 contactos vs 323 conversaciones)

- **Negativas:**
  - Se pierde la granularidad por conversación individual
  - El campo `last_message` ya no está disponible directamente en la tarjeta
  - Requiere migración de datos existentes

- **Riesgos:**
  - La migración en caliente puede causar inconsistencias temporales
  - Si el script falla parcialmente, algunos contactos pueden quedar
    sin atributos

## Alternativas consideradas

| Opción | Pros | Contras | ¿Por qué no? |
|--------|------|---------|--------------|
| Mantener conversation-based | Sin migración | Duplicación persistente, inestabilidad | No resuelve el problema raíz |
| Híbrido (contactos + última conversación) | Más datos por tarjeta | Complejidad de sync, dos fuentes de verdad | Over-engineering para el caso de uso |
| Nuevo custom attribute con key distinto | Sin conflicto de keys | Duplicación de atributos en Chatwoot | Mismo key, distinto modelo funciona |

# Sesión 001 — Factibilidad técnica y arquitectura: Kanban + Sistema de Tareas

| Campo | Valor |
|---|---|
| **Fecha** | 2026-07-09 |
| **Tipo** | Diseño / Factibilidad / Kick-off de desarrollo |
| **Proyecto** | kanban.ruki-bot.com integrado con chatwoot.ruki-bot.com |
| **Estado al cierre** | Etapa 1 entregada — en producción con cambios propios del desarrollador |

---

## Objetivo de la sesión

Determinar la factibilidad técnica de integrar dos features sobre Chatwoot self-hosted que otros CRMs manejan nativamente:

1. **Vista Kanban por pipeline** con drag & drop sobre etapas de conversación.
2. **Sistema de tareas** con asignación, duración y estados automáticos.

El alcance se limitó explícitamente a factibilidad, existencia de endpoints y limitaciones técnicas — sin prototipar UI ni elegir librerías de frontend.

---

## Fuentes consultadas

- `https://www.chatwoot.com/hc/user-guide/articles/1677691702-how-to-use-dashboard-apps` — mecanismo del iframe, payload de `postMessage`, flag `hmac_verified`.
- `https://www.chatwoot.com/llms.txt` — índice general de capacidades: REST API, webhooks, websocket, Dashboard Apps.
- Búsquedas adicionales sobre: filtros por `custom_attributes`, webhook `conversation_updated`, endpoint `create_message` y `sender_id`, Personal Access Token lifecycle, issue #12590 (scoped tokens), issue #7402 (webhook duplicado), issue #13993 (inconsistencias de schema en webhook).

---

## Decisiones tomadas (resumen ejecutivo)

| # | Decisión | ADR |
|---|---|---|
| 1 | Dashboard App es solo superficie visual; toda la lógica va contra la REST API | ADR-001 |
| 2 | Un único bot-user con token en backend; nunca tokens por agente humano | ADR-002 |
| 3 | Cloudflare Access con OTP por `@i-labs.cl` como capa de auth de agentes | ADR-003 |
| 4 | Audit log propio como única fuente de atribución real (quién hizo qué) | ADR-004 |
| 5 | BD propia como fuente de verdad de tareas; Chatwoot solo recibe `tarea_estado` | ADR-005 |
| 6 | Kanban sobre custom_attributes de conversación vía `/conversations/filter` | ADR-006 |
| 7 | Python + FastAPI + PostgreSQL; deploy por SSH + build en servidor + Arcane | ADR-007 |

---

## Alcance cerrado del MVP

### Feature 1 — Kanban de pipeline

- Columnas = valores del custom_attribute `pipeline_stage` (tipo List en Chatwoot).
- Selector superior de pipeline filtra por `pipeline` (otro custom_attribute).
- Filtro adicional por `tarea_estado` dentro de la misma vista (un solo request a `/conversations/filter`).
- Drag & drop actualiza `pipeline_stage` via `POST /custom_attributes`.
- Sincronización entre agentes vía webhook `conversation_updated` con manejo de duplicados (idempotencia por `conversation.id + updated_at`).

### Feature 2 — Sistema de tareas

- **1 tarea activa por conversación** — se bloquea la creación si ya existe una viva.
- **Pool rotativo** — cualquier agente puede crear o cerrar la tarea de cualquier conversación. Sin ownership.
- **Estados:** `tarea_activa → tarea_hoy → tarea_vencida → tarea_cerrada`.
- **Cron a las 23:30** — transiciona automáticamente tareas no cerradas. Silencioso (no genera nota).
- **Creación** vía modal al hacer click sobre el lead en el Kanban.
- **Dato del mensaje y fechas** en BD propia. `tarea_estado` es el único espejo en Chatwoot.
- **Private notes descartadas** como mecanismo de almacenamiento (ver ADR-005).

### Panel histórico

- Lista plana de las últimas 100 tareas, sin filtros, desde el audit log.
- Query: `SELECT ... FROM task_audit_log ORDER BY created_at DESC LIMIT 100`.

### Fuera del MVP (explícito)

- Procesos recurrentes tipo "contactar cada 3 meses" — se modela en sistema separado.
- Múltiples tareas simultáneas o historial por lead — descartado, es 1:1.
- Roles diferenciados dentro de la app — todos los agentes `@i-labs.cl` tienen los mismos permisos en MVP.
- Notificación push nativa a agentes (vía @mention en private note) — descartada al eliminar el uso de private notes.

---

## Entregables de la sesión

### Codebase Etapa 1 entregado (zip)

Estructura de repo inicial para exploración read-only de la API de Chatwoot:

```
chatwoot-integration/
├── app/
│   ├── main.py                  # FastAPI entrypoint, incluye router de debug
│   ├── config.py                # Pydantic Settings cargando desde .env
│   ├── chatwoot_client.py       # Wrapper httpx sobre API de Chatwoot (bot-user token)
│   ├── routers/
│   │   └── conversations.py    # Endpoints de exploración read-only
│   └── schemas/                 # Vacío — a completar con shapes reales en Etapa 1
├── Dockerfile                   # Python 3.12-slim, uvicorn en puerto 8000
├── compose.yml                  # Servicios: app + postgres:16-alpine
├── .env.example                 # Keys documentadas sin valores
├── requirements.txt
└── .gitignore
```

**Endpoints disponibles en esta entrega:**

- `GET /health` — liveness check.
- `GET /debug/custom-attribute-definitions` — devuelve el JSON crudo de Chatwoot con todas las definiciones de custom attributes. **Primer endpoint a llamar** para confirmar que `tarea_estado` y los keys de pipeline existen y ver su formato exacto (Chatwoot es case-sensitive en `attribute_key`).
- `POST /debug/conversations/filter?attribute_key={key}&value={value}` — devuelve el JSON crudo de una búsqueda filtrada. **Objetivo de esta etapa:** ver el shape real de la respuesta antes de definir los schemas Pydantic.

### Pendiente para completar Etapa 1

El desarrollador debe:
1. Crear el bot-user en Chatwoot (`api-bot@i-labs.cl` o similar) y obtener su token.
2. Confirmar el `account_id` desde la URL del dashboard (`/app/accounts/{id}/`).
3. Completar el `.env` con `CHATWOOT_BASE_URL=https://chatwoot.ruki-bot.com`, `CHATWOOT_ACCOUNT_ID` y `CHATWOOT_BOT_TOKEN`.
4. Hacer `docker compose build && docker compose up -d`.
5. Llamar a `GET /debug/custom-attribute-definitions` y pegar la respuesta para definir los schemas Pydantic reales en `app/schemas/chatwoot.py`.
6. Llamar a `POST /debug/conversations/filter` con un key real y confirmar el shape de paginación y de cada conversación en la respuesta.

Con esos dos JSONs confirmados, se puede cerrar la Etapa 1 y comenzar la Etapa 2 (escritura).

---

## Etapas del proyecto (mapa completo)

| Etapa | Contenido | Estado |
|---|---|---|
| **Etapa 0** | Cloudflare Access + validación JWT en backend + tabla `agentes` | Pendiente |
| **Etapa 1** | Lectura desde Chatwoot — `/conversations/filter` y `/custom_attribute_definitions` | Entregado (en producción con ajustes del desarrollador) |
| **Etapa 2** | Escritura puntual — `POST /custom_attributes` sobre conversación de prueba + validación de webhook `conversation_updated` | Pendiente |
| **Etapa 3** | Feature 1: Kanban completo con drag & drop y sincronización entre agentes | Pendiente |
| **Etapa 4** | Feature 2: tareas completas — modal de creación, cron, bloqueo 1-activa, panel histórico | Pendiente |

---

## Riesgos técnicos identificados y abiertos

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Webhook `conversation_updated` con doble disparo (issue #7402) | Alta | Medio | Idempotencia por `conversation.id + updated_at` |
| Schema inconsistente del webhook entre versiones (issue #13993) | Media | Medio | Validación defensiva con Pydantic, campos opcionales |
| `POST /custom_attributes` exitoso pero `POST` previo (otro campo) fallido — estado parcial | Baja | Alto | Retry con backoff + flag `sync_pendiente` en BD |
| Shape real de `/conversations/filter` diferente al documentado | Media | Alto | Objetivo explícito de la Etapa 1 verificarlo antes de construir |
| Chatwoot no soporta valores condicionales de List entre custom_attributes | Confirmado | Bajo | Lógica de etapas válidas por pipeline vive en config del backend/frontend |

---

## Notas de contexto del negocio

- Empresa sin Salesforce ni CRM dedicado — Chatwoot es el sistema central.
- Equipo de agentes < 10 personas con modelo de **recepcionista rotatorio** (pool compartido de conversaciones, sin ownership de lead).
- Todos los agentes tienen correo `@i-labs.cl` (Hostinger). No hay Google Workspace ni Microsoft 365.
- Infraestructura en servidor propio, expuesta vía Cloudflare. Dominio principal: `ruki-bot.com`. Servicios relevantes: `chatwoot.ruki-bot.com`, `kanban.ruki-bot.com`.
- Codebase privado — sin uso de registries externos ni CI/CD de terceros.

# Sesión 013 — Demo autocontenida y capturas para el README

| Campo | Valor |
|---|---|
| **Fecha** | 2026-08-30 |
| **Tipo** | Infraestructura demo / Documentación |
| **Proyecto** | chatwoot-kanban |
| **Estado al cierre** | Demo levantada y verificada, README actualizado |

---

## Objetivo de la sesión

Poder levantar el proyecto con datos mockup para mostrar la interfaz
(tablero + dashboard) en el README, sin depender de una instancia real de
Chatwoot.

## Qué se hizo

### 1. Mock de la API de Chatwoot (`demo/mock_chatwoot.py`)

Reimplementa únicamente los endpoints que consume `ChatwootClient`:

- `GET /api/v1/accounts/{id}/custom_attribute_definitions`
- `POST /api/v1/accounts/{id}/contacts/filter`
- `GET|PATCH /api/v1/accounts/{id}/contacts/{contact_id}`
- `GET /avatars/{seed}.svg` (avatares SVG con iniciales, offline)

Seed de 28 contactos repartidos en 7 etapas del pipeline
(`Potencial` → `Perdido`), con `kanban_view_mensaje` y
`kanban_view_fecha_termino` calculados en relación a la fecha actual para
que el tablero siempre muestre tareas activas / de hoy / vencidas.

### 2. Seed de BD para el dashboard (`demo/seed_db.py`)

Idempotente (marca `source='seed'`): crea 5 agentes y 60 eventos de
auditoría para poblar `/kanban/stats` y `/kanban/stats/history`.
Se ejecuta como servicio `db-seed` en compose (`PYTHONPATH=/code`,
usa `get_pool()` en vez de importar `pool` para no capturar `None`).

### 3. Orquestación (`docker-compose.demo.yml`)

Tres servicios: `postgres` (puerto host 5433), `mock-chatwoot` (:8095) y
`app` (:8000), más `db-seed`. La app apunta `CHATWOOT_BASE_URL` al mock;
**no se tocó ningún archivo de `app/`**.

### 4. Capturas (`demo/screenshot.py`, `docs/demo/*.png`)

Playwright + Chromium headless: tablero, modal de tarea y dashboard en
light y dark. Verificadas por contenido (no imágenes en blanco).

### 5. Documentación

- `README.md` — sección **Demo** con capturas y "Opción A" en Quick Start.
- `docs/demo/README.md` — cómo levantar, endpoints del mock y cómo regenerar capturas.
- `docs/adr/018-demo-mockup-chatwoot.md` — ADR de la decisión.
- `docs/README.md` — índice actualizado.

## Archivos tocados

| Archivo | Tipo de cambio |
|---|---|
| `demo/mock_chatwoot.py` | Nuevo |
| `demo/seed_db.py` | Nuevo |
| `demo/screenshot.py` | Nuevo |
| `demo/Dockerfile` | Nuevo |
| `demo/requirements.txt` | Nuevo |
| `docker-compose.demo.yml` | Nuevo |
| `docs/demo/README.md` | Nuevo |
| `docs/demo/kanban-light.png` | Nuevo |
| `docs/demo/kanban-dark.png` | Nuevo |
| `docs/demo/kanban-task-modal.png` | Nuevo |
| `docs/demo/dashboard-light.png` | Nuevo |
| `docs/demo/dashboard-dark.png` | Nuevo |
| `docs/adr/018-demo-mockup-chatwoot.md` | Nuevo |
| `docs/sesiones/013-2026-08-30-demo-mockup-readme.md` | Nuevo |
| `README.md` | Edición (sección Demo + Opción A quick start) |
| `docs/README.md` | Edición (índice) |

## Decisiones tomadas

| Decisión | ADR |
|---|---|
| Mock HTTP separado en lugar de "modo demo" dentro de la app | ADR-018 |
| Fechas seed relativas a hoy (demo "fresca" cualquier día) | ADR-018 |
| Avatares servidos por el propio mock (funciona offline) | ADR-018 |

## Pruebas realizadas

- `ruff check demo/ app/ tests/` → all checks passed.
- Endpoints del mock verificados con `curl`.
- `/health`, `/kanban/config`, `/kanban/board` (7 columnas, contactos +
  tareas), `/kanban/stats` y `/kanban/stats/history` devolviendo datos.
- Capturas generadas con contenido (no en blanco).

## Nota operativa

En esta máquina el cliente de Docker negociaba API 1.43 (más vieja que el
daemon), así que se usó `DOCKER_API_VERSION=1.44` para levantar y operar el
stack demo. En un entorno normal `docker compose` basta.

## Próximo paso

1. Revisar las capturas de `docs/demo/` a ojo y ajustar si algo no convence
   (p. ej. emojis del badge de tarea en headless).
2. Commit + push en `develop` y merge a `main` cuando corresponda.
# Sesión 012 — Desvinculación, limpieza y apertura open source

| Campo | Valor |
|---|---|
| **Fecha** | 2026-07-31 |
| **Tipo** | Limpieza / Documentación / Publicación |
| **Proyecto** | chatwoot-kanban (ex The-Company) |
| **Estado al cierre** | Listo para publicación pública en GitHub |

---

## Objetivo de la sesión

Desvincular el proyecto de la empresa original, eliminar referencias a
"ruki", "i-labs" y valores hardcodeados, y preparar el repositorio para
su publicación como open source bajo licencia MIT.

---

## Qué se hizo

### 1. Limpieza de código fuente

- **`app/config.py`**: `postgres_host` default → `"postgres"`. Nuevos campos: `chatwoot_bot_email`, `chatwoot_frontend_url`.
- **`app/main.py`**: `title="Chatwoot Integration - i-labs"` → `"Chatwoot-Kanban"`.
- **`app/database.py`**: 4x `"bot@i-labs.cl"` → `settings.chatwoot_bot_email`.
- **`app/routers/kanban.py`**: `"bot@i-labs.cl"` fallback → `settings.chatwoot_bot_email`. Nombre fallback → `"Bot (dev)"`. Endpoint `/kanban/config` ahora devuelve `chatwoot_frontend_url`.
- **`app/templates/kanban.html`**: URLs hardcodeadas a `ruki-bot.com` → usan `chatwoot_frontend_url` dinámico desde config.
- **`tests/test_kanban.py`**: 8x `"bot@i-labs.cl"` → `"bot@example.com"`.

### 2. Infraestructura Docker y CI

- **`docker-compose.yml`**: Servicios renombrados (`chatwoot-kanban-db`, `chatwoot-kanban-app`), red `chatwoot_shared`, imagen `ghcr.io/crisalva1414/chatwoot-kanban:main`.
- **`developer-compose.yml`**: Ídem staging con `:develop`.
- **`.env.example`**: `POSTGRES_HOST=chatwoot-kanban-db`. Nuevas vars: `CHATWOOT_BOT_EMAIL`, `CHATWOOT_FRONTEND_URL`.
- **`pyproject.toml`**: `name = "chatwoot-kanban"`.
- **Workflows CI**: `${{ github.repository }}` resuelve dinámicamente — no requieren cambios.

### 3. Documentación histórica

Reemplazos masivos en `AGENTS.md`, `docs/adr/` (9 archivos) y `docs/sesiones/` (11 archivos):
- `ruki-*` → `chatwoot-*`
- `ruki-bot.com` → `example.com`, `@i-labs.cl` → `@example.com`
- `i-labs` / `I-Labs-Chile` → `the-company` / `The-Company`
- ~50 ocurrencias limpiadas en total

### 4. Documentación open source (archivos nuevos)

- **`README.md`** — features (énfasis en sync bidireccional con custom attributes de Chatwoot, pipeline stages nativos, cron automático, drag & drop), arquitectura, quick start, API endpoints.
- **`CONTRIBUTING.md`** — setup dev, convenciones (Conventional Commits, Ruff, tipado estricto), proceso de PR.
- **`LICENSE`** — MIT.
- **`SECURITY.md`** — política de reporte de vulnerabilidades.
- **`CODE_OF_CONDUCT.md`** — Contributor Covenant 2.1.
- **`CHANGELOG.md`** — v0.1.0 inicial.

### 5. ADR-017

Documenta la decisión de desvincular y abrir el proyecto como open source
bajo MIT, detallando las sustituciones realizadas y el racional.

---

## Archivos tocados

| Archivo | Tipo de cambio |
|---|---|
| `app/config.py` | Edición |
| `app/main.py` | Edición |
| `app/database.py` | Edición (4x reemplazo) |
| `app/routers/kanban.py` | Edición (fallback + config endpoint) |
| `app/templates/kanban.html` | Edición (URLs dinámicas) |
| `tests/test_kanban.py` | Edición (8x reemplazo) |
| `docker-compose.yml` | Reescritura completa |
| `developer-compose.yml` | Reescritura completa |
| `.env.example` | Reescritura completa |
| `pyproject.toml` | Edición |
| `AGENTS.md` | Limpieza de referencias |
| `docs/adr/*.md` (9 archivos) | Limpieza de referencias |
| `docs/sesiones/*.md` (11 archivos) | Limpieza de referencias |
| `docs/format/git.md` | Limpieza de referencias |
| `docs/adr/017-desvinculacion-y-apertura-open-source.md` | Nuevo |
| `docs/sesiones/012-2026-07-31-desvinculacion-limpieza-open-source.md` | Nuevo |
| `README.md` | Nuevo |
| `CONTRIBUTING.md` | Nuevo |
| `LICENSE` | Nuevo |
| `SECURITY.md` | Nuevo |
| `CODE_OF_CONDUCT.md` | Nuevo |
| `CHANGELOG.md` | Nuevo |

---

## Decisiones tomadas

| Decisión | ADR |
|---|---|
| Licencia MIT (misma que Chatwoot) | ADR-017 |
| Eliminar referencias a la empresa pero conservar ADRs históricos con placeholders genéricos | ADR-017 |
| Hacer configurables email bot y URL frontend vía `.env` en lugar de hardcodear | ADR-017 |

---

## Próximo paso

1. Cambiar remote a `CrisAlva1414/chatwoot-kanban`.
2. Push a GitHub.
3. Editar repo: descripción, tags, visibilidad pública.
4. Configurar branch protection en `main`.
5. Publicar en GitHub Discussions (Show and Tell).

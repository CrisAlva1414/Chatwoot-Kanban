# Ruki Plugins — Kanban

Integración Kanban/Tareas para Chatwoot CRM. Plugin desplegado como API
FastAPI, sin frontend propio; la UI será vía iframe embebido en Chatwoot.

## Stack

| Capa       | Tecnología                        |
| ---------- | --------------------------------- |
| Runtime    | Python 3.12                       |
| Framework  | FastAPI                           |
| Cliente    | httpx (Chatwoot API)              |
| DB         | PostgreSQL 16 via asyncpg         |
| Lint       | Ruff                              |
| CI         | GitHub Actions (lint + pytest)    |
| Deploy     | Docker → GHCR → Arcane GitOps     |
| Exposición | Cloudflare Tunnel + Access        |

## Estructura del proyecto

```
├── AGENTS.md              ← este archivo
├── docker-compose.yml     ← producción (Arcane sync: main)
├── developer-compose.yml  ← staging (Arcane sync: develop)
├── Dockerfile
├── pyproject.toml
├── ruff.toml
├── requirements.txt
├── .env.example
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── main.py             ← FastAPI app
│   ├── config.py           ← pydantic-settings
│   ├── chatwoot_client.py  ← wrapper de la API de Chatwoot
│   ├── database.py         ← asyncpg pool + schema + queries
│   ├── schemas/
│   │   └── chatwoot.py     ← Pydantic models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── kanban.py       ← Core: board, tasks, cron, stats
│   │   ├── webhooks.py     ← Webhook receiver
│   │   ├── conversations.py
│   │   └── api.py          ← Proxy endpoint
│   └── templates/
│       ├── kanban.html
│       └── dashboard.html
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_kanban.py
│   └── test_webhooks.py
├── .github/
│   └── workflows/
│       ├── docker_publish.yml         ← build :main (push a main)
│       ├── docker_publish_develop.yml ← build :develop (push a develop)
│       └── test.yml                   ← lint + pytest (PRs a main/develop)
└── docs/
    ├── README.md
    ├── adr/                ← Architecture Decision Records
    ├── format/             ← Convenciones (git, python, comentarios)
    └── sesiones/           ← Contexto por sesión para el LLM
```

## Convenciones (resumen)

- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, etc.)
- **Python**: Ruff con línea de 88 chars, tipado estricto, sin comentarios
  superfluos
- **Comentarios**: Solo docstrings en módulos públicos; estilo Google.
  Sin comentarios inline a menos que expliquen un "por qué" no obvio.
- **Documentación**: Todo cambio sustancial debe incluir o actualizar
  el ADR correspondiente y la sesión activa.
- **BD**: Los schemas se versionan con Alembic (cuando se agregue).
- **Etapas**: El proyecto evoluciona por etapas (ver ADR-011). Cada
  sesión documenta avances y el siguiente paso.

## Flujo de trabajo diario

### Modelo de ramas

| Rama | Entorno | Deploy |
|------|---------|--------|
| `main` | Producción | Arcane GitOps (auto, tras merge de develop) |
| `develop` | Staging | Arcane GitOps (auto, tras push) |

### Proceso habitual

```
1. Trabajar en develop directamente
2. git push origin develop
3. GitHub Actions: lint + pytest → build :develop → GHCR
4. Arcane: auto-sync → pull → redeploy en NAS
5. Probar en devkanban.ruki-bot.com
6. Si todo OK → PR develop → main
7. Tests pasan → approve manual → merge
8. Arcane: auto-sync → pull → redeploy en kanban.ruki-bot.com
```

### Entorno staging (Arcane)

El proyecto de staging se configura manualmente en Arcane:
1. Crear proyecto desde Git Repo
2. Seleccionar branch `develop`
3. Compose file: `developer-compose.yml`
4. Configurar `.env` con `POSTGRES_DB=kanban_staging`
5. Auto Sync: ON

### Rollback manual

Si algo falla en staging o producción, desde Arcane:
1. Abrir el proyecto
2. Click "Redeploy" (pull latest) o "Restart"
3. O manualmente en el servidor: `docker compose pull && docker compose up -d`

## Referencias

- [docs/README.md](docs/README.md) — índice completo
- [docs/adr/](docs/adr/) — decisiones arquitectónicas
- [docs/format/](docs/format/) — convenciones detalladas
- [docs/sesiones/](docs/sesiones/) — historial por sesión

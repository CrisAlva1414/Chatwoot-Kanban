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
| Deploy     | Docker → GHCR → compose en NAS    |
| Exposición | Cloudflare Tunnel + Access        |

## Estructura del proyecto

```
├── AGENTS.md              ← este archivo
├── docker-compose.yml
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
│   └── routers/
│       ├── __init__.py
│       └── conversations.py
├── .github/
│   └── workflows/
│       └── docker_publish.yml
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

## Referencias

- [docs/README.md](docs/README.md) — índice completo
- [docs/adr/](docs/adr/) — decisiones arquitectónicas
- [docs/format/](docs/format/) — convenciones detalladas
- [docs/sesiones/](docs/sesiones/) — historial por sesión

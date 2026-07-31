# Contributing to Chatwoot-Kanban

Thanks for your interest in contributing!

## Development Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 16 (or Docker)
- A Chatwoot instance (local or remote) for integration testing

### Local environment

```bash
git clone https://github.com/CrisAlva1414/Chatwoot-Kanban.git
cd chatwoot-kanban
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

Create a `.env` file from the example:

```bash
cp .env.example .env
```

For local development, you can use Docker for PostgreSQL:

```bash
docker compose up -d chatwoot-kanban-db
```

Or point `POSTGRES_HOST` to your local PostgreSQL instance.

### Running tests

```bash
pytest tests/ -v
```

Tests use mocked Chatwoot API responses. A PostgreSQL service is not required for unit tests.

### Code quality

```bash
ruff check app/ tests/
ruff format --check app/ tests/
```

Format automatically:

```bash
ruff format app/ tests/
```

## Conventions

### Commits

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(kanban): add multi-pipeline support
fix(sync): handle empty custom attributes in webhook
docs(readme): update quick start instructions
```

- **Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`
- **Description**: in English, present imperative, no period at the end

### Python

- Ruff with line-length 88, double quotes, LF line endings
- Strict typing — no untyped functions in public API
- Docstrings in Google style for public modules (no inline comments unless explaining non-obvious "why")

### Branches

- `main` — production-ready code
- `develop` — integration branch for ongoing work
- Feature/fix branches from `develop`

## Pull Request Process

1. Fork the repo and create a branch from `develop`.
2. Make your changes following the conventions above.
3. Add or update tests as needed.
4. Run `ruff check` and `pytest` locally.
5. Open a PR against `develop` with a clear description.
6. CI must pass (lint + pytest).
7. A maintainer will review and merge.

## Project Structure

```
├── app/
│   ├── main.py              # FastAPI entrypoint
│   ├── config.py            # Pydantic settings (env vars)
│   ├── chatwoot_client.py   # Chatwoot API wrapper (httpx + retry)
│   ├── database.py          # asyncpg pool, schema, queries
│   ├── routers/
│   │   ├── kanban.py        # Board, tasks, cron, stats
│   │   ├── webhooks.py      # Webhook receiver
│   │   ├── conversations.py # Debug/exploration endpoints
│   │   └── api.py           # Proxy endpoints
│   ├── schemas/
│   │   └── chatwoot.py      # Pydantic models
│   └── templates/
│       ├── kanban.html      # Kanban SPA
│       └── dashboard.html   # Dashboard SPA
├── tests/
│   ├── conftest.py          # Fixtures & mocks
│   ├── test_health.py
│   ├── test_kanban.py
│   └── test_webhooks.py
├── docs/
│   ├── adr/                 # Architecture Decision Records
│   ├── format/              # Code conventions
│   └── sesiones/            # Development session log
└── .github/workflows/       # CI/CD pipelines
```

## Questions?

Open an issue or start a discussion on GitHub.

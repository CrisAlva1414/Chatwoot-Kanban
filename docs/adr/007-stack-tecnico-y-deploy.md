# ADR-007 — Stack técnico y estrategia de deploy

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-07-09 |
| **Actualizado** | 2026-07-13 |
| **Proyecto** | kanban.ruki-bot.com |
| **Decidido por** | Sesión de factibilidad técnica inicial |

---

## Contexto

El proyecto es un monorepo privado con backend + frontend que se despliega
en un servidor propio. La imagen se construye vía GitHub Actions y se
almacena en GHCR. Arcane gestiona el deploy en el servidor.

## Decisiones de stack

### Backend

**Python 3.12 + FastAPI 0.139.0 + PostgreSQL 16**

Fundamento:
- El desarrollador principal tiene experiencia en Python — prioriza
  comprensión y mantenibilidad sobre velocidad de ejecución.
- FastAPI provee validación de tipos automática vía Pydantic, crítica
  para validar defensivamente los payloads de Chatwoot.
- Para el volumen de tráfico esperado (equipo < 10 agentes), Python no
  es el cuello de botella.
- PostgreSQL ya estaba disponible en el entorno de producción.

### Dependencias principales

```
fastapi==0.139.0
uvicorn[standard]==0.30.6
httpx==0.27.2
pydantic-settings==2.5.2
asyncpg==0.29.0
```

### Estrategia de deploy

**GitHub Actions → GHCR → Arcane → docker compose en el NAS.**

Flujo:
1. Push a `main` dispara el workflow de GitHub Actions.
2. GitHub Actions construye la imagen multi-arch (amd64 + arm64) y la
   publica en GHCR (`ghcr.io/i-labs-chile/ruki-plugins-kanban`).
3. Arcane detecta la nueva imagen en GHCR y ejecuta el pull + restart.
4. La app se conecta a PostgreSQL (contenedor `ruki-kanban-postgres`).

### Estructura de servicios (docker-compose.yml)

```
services:
  ruki-kanban-postgres:  PostgreSQL 16 Alpine
  ruki-kanban-kanban:    FastAPI (puerto 8000, no expuesto)
```

El servicio de la app se ejecuta como usuario no-root (`appuser`) con
Dockerfile multi-stage. No hay `ports:` en docker-compose — la exposición
es vía Cloudflare Tunnel.

### Variables de entorno

Todas las configuraciones sensibles van en `.env` en el servidor (nunca
en el repositorio). `.env.example` en el repo documenta las keys sin
valores. Variables requeridas:

```bash
# Chatwoot
CHATWOOT_BASE_URL=https://chatwoot.ruki-bot.com
CHATWOOT_ACCOUNT_ID=
CHATWOOT_BOT_TOKEN=

# Postgres
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}

# Cloudflare Access
CF_ACCESS_TEAM_DOMAIN=
CF_ACCESS_AUD=

# App
ENV=production
```

## Estructura de repo

```
ruki-plugins-kanban/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── chatwoot_client.py
│   ├── routers/
│   │   ├── api.py
│   │   ├── conversations.py
│   │   ├── kanban.py
│   │   └── webhooks.py
│   ├── schemas/
│   │   └── chatwoot.py
│   └── templates/
│       └── kanban.html
├── tests/
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
├── requirements-dev.txt
└── .github/
    └── workflows/
        └── docker_publish.yml
```

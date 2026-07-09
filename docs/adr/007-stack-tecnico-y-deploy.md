# ADR-007 — Stack técnico y estrategia de deploy

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-07-09 |
| **Proyecto** | kanban.ruki-bot.com |
| **Decidido por** | Sesión de factibilidad técnica inicial |

---

## Contexto

El proyecto es un monorepo privado con backend + frontend que debe desplegarse en un servidor propio, sin exponer el código fuente a registries externos (GHCR, Docker Hub) ni depender de GitHub Actions para el pipeline de despliegue.

## Decisiones de stack

### Backend

**Python 3.12 + FastAPI + PostgreSQL 16**

Fundamento:
- El desarrollador principal tiene experiencia en Python — prioriza comprensión y mantenibilidad sobre velocidad de ejecución o ecosistema de librerías.
- FastAPI provee validación de tipos automática vía Pydantic, crítica para validar defensivamente los payloads de Chatwoot (shapes inconsistentes documentados en issues de la plataforma).
- Para el volumen de tráfico esperado (equipo < 10 agentes), Python no es el cuello de botella. El rate limit de la API de Chatwoot lo será antes.
- PostgreSQL ya estaba disponible en el entorno de producción.

Alternativa evaluada — Node.js (Express/Fastify): descartada por no aportar ventaja técnica real en este contexto y sacrificar comprensión del desarrollador principal.

### Dependencias principales

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
httpx==0.27.2
pydantic-settings==2.5.2
asyncpg==0.29.0
```

### Estrategia de deploy

**Build en el servidor vía SSH + deploy key. Sin CI/CD externo. Arcane como UI de gestión.**

Flujo:
1. Push al repositorio privado (GitHub, acceso vía deploy key desde el servidor).
2. SSH al servidor → `git pull` → `docker compose build` → `docker compose up -d`.
3. Arcane gestiona el estado de los contenedores, visualiza logs y permite actualizaciones desde UI.

Alternativas descartadas:
- **GitHub Actions + GHCR:** descartado porque el codebase es privado y el equipo prefiere no exponer imágenes a registries externos. GitHub Actions requeriría secrets adicionales y agrega una dependencia de disponibilidad externa.
- **Build local + push al servidor:** descartado por agregar un paso extra sin beneficio para un equipo de este tamaño.

### Estructura de servicios (compose.yml)

```
services:
  app:    FastAPI (puerto 8000)
  db:     PostgreSQL 16 Alpine
```

El servicio `app` se expone detrás de Cloudflare Proxy (HTTPS via `kanban.ruki-bot.com`), igual que el resto de servicios de ruki-bot.com. Cloudflare Access se pone delante a nivel de DNS/proxy — el contenedor de la app no necesita manejar TLS directamente.

### Variables de entorno

Todas las configuraciones sensibles van en `.env` en el servidor (nunca en el repositorio). `.env.example` en el repo documenta las keys sin valores. Variables requeridas:

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
chatwoot-integration/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── chatwoot_client.py
│   ├── routers/
│   │   └── conversations.py
│   └── schemas/
│       └── chatwoot.py          # a completar en Etapa 1 con shapes reales
├── Dockerfile
├── compose.yml
├── .env.example
├── requirements.txt
└── .gitignore
```

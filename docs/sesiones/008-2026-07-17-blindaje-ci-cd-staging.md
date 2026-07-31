# Sesión 008 — Blindaje CI/CD y entorno staging

- **Fecha:** 2026-07-17
- **Propósito:** Proteger `main` con branch protection, crear entorno de staging
  con Arcane GitOps, pipeline de testing en PRs, y documentación del flujo
  de trabajo diario.

## Contexto

El proyecto está en producción (kanban.example.com) con deploy manual vía
Arcane. No hay branch protection, no hay testing automatizado, y no hay
entorno de staging separado. El usuario desarrolla directamente en `main`
y deploya manualmente. Con la aplicación sirviendo a usuarios reales, se
necesita:

1. Proteger `main` de merges accidentales
2. Un entorno de staging para probar antes de producción
3. Tests automáticos en cada PR
4. Documentación del flujo de trabajo para sesiones futuras

## Cambios realizados

### 1. Branch model (ADR-013)

**Decisión:** Modelo main/develop con branch protection.

- `main`: producción, protegida con required check `test` + 1 approval
- `develop`: staging, base de trabajo diaria
- `feat/<nombre>`: para features grandes

El usuario trabaja directamente en `develop` para cambios pequeños, o crea
feature branches para cambios grandes. El merge a `main` requiere PR con
tests verdes y approval manual.

### 2. Entorno de staging (ADR-014)

**Archivo:** `developer-compose.yml`

Compose completo (no override) que se configura como proyecto separado
en Arcane. Diferencias con producción:

| Aspecto | Producción | Staging |
|---------|------------|---------|
| Compose | `docker-compose.yml` | `developer-compose.yml` |
| Tag imagen | `:main` | `:develop` |
| Container DB | `chatwoot-kanban-db` | `chatwoot-kanban-staging-db` |
| Container app | `chatwoot-kanban-app` | `chatwoot-kanban-staging-app` |
| Volumen DB | `kanban_pgdata` | `kanban_staging_pgdata` |
| DB name | `kanban` (de `.env`) | `kanban_staging` (override) |

Ambos comparten `.env` (credenciales Chatwoot, password Postgres).

**Configuración en Arcane:** Crear proyecto desde Git Repo, branch
`develop`, compose file `developer-compose.yml`, Auto Sync ON.

### 3. Pipeline CI (ADR-015)

**Workflows creados:**

| Workflow | Trigger | Jobs |
|----------|---------|------|
| `test.yml` | PR a main/develop | lint (ruff) + test (pytest + PG efímero) |
| `docker_publish_develop.yml` | Push a develop | Build `:develop` (arm64) → GHCR |

**Workflow existente modificado:**
- `docker_publish.yml`: platforms cambiado a `linux/arm64` (NAS es OrangePi5 ARM)

**Deploy:** Arcane GitOps maneja el deploy automáticamente. No hay
workflow de deploy; Arcane detecta cambios en GHCR y redeploya.

### 4. Documentación actualizada

- `AGENTS.md`: flujo de trabajo diario, estructura de proyecto actualizada
- `docs/format/git.md`: modelo de ramas, proceso de PRs
- `docs/adr/README.md`: índices de ADRs 012, 013, 015
- ADRs creados: 013 (branching model), 015 (CI/CD pipeline)

### 5. Decisiones pendientes (usuario)

- [ ] Autenticar `gh` CLI para branch protection
- [ ] Crear rama `develop` y push
- [ ] Configurar branch protection en GitHub
- [ ] Configurar proyecto de staging en Arcane
- [ ] Configurar Cloudflare Tunnel para `devkanban.example.com`

## Archivos creados/modificados

| Archivo | Acción |
|---------|--------|
| `developer-compose.yml` | Creado |
| `.github/workflows/test.yml` | Creado |
| `.github/workflows/docker_publish_develop.yml` | Creado |
| `.github/workflows/docker_publish.yml` | Modificado (arm64) |
| `docs/adr/013-modelo-ramas-y-gate-proteccion.md` | Creado |
| `docs/adr/015-pipeline-ci-cd.md` | Creado |
| `docs/adr/README.md` | Modificado (agregados 012, 013, 015) |
| `docs/format/git.md` | Reescrito (modelo de ramas) |
| `AGENTS.md` | Reescrito (flujo de trabajo) |

## Siguiente paso

1. Autenticar `gh` CLI
2. Crear rama `develop` y configurar branch protection
3. Configurar proyecto de staging en Arcane
4. Probar pipeline completo push → build → deploy

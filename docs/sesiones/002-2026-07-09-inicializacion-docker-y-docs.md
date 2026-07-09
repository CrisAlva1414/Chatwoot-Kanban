# Sesión 002 — Inicialización, Docker y documentación

- **Fecha:** 2026-07-09
- **Propósito:** Poner en producción el plugin Kanban y establecer la
  estructura de documentación para trabajar con opencode.

## Contexto

El proyecto existía como un esqueleto FastAPI con Dockerfile y workflow de
GHCR. No tenía docker-compose, ni documentación, ni configuración de
entorno productivo. La sesión 001 (Opus 4.8) definió la arquitectura y
alcance; esta sesión implementa la infraestructura.

## Qué se hizo

1. **Docker Compose productivo** con PostgreSQL 16, sin puertos expuestos,
   container naming `ruki-<proyecto>-<servicio>`, red externa `ruki_shared`.
2. **`.env.example`** con todas las variables de configuración.
3. **`.gitignore`** para `.env` y `__pycache__`.
4. **Fusión de documentación:** los ADRs y sesión de Opus 4.8 (raíz `adr/`,
   `sessions/`) se movieron a `docs/` y se numeraron junto con ADRs nuevos.
5. **Convenciones de desarrollo:** `ruff.toml`, `pyproject.toml`, format docs.
6. **`AGENTS.md`** poblado con contexto del proyecto.

## Archivos tocados

- `docker-compose.yml` (creado)
- `.env.example` (creado)
- `.gitignore` (creado)
- `ruff.toml` + `pyproject.toml` (creados)
- `AGENTS.md` (poblado)
- `docs/` completo (fusionado con archivos de Opus 4.8)

## Decisiones tomadas

- ADR-008: ADR como registro de decisiones
- ADR-009: Estructura del repositorio
- ADR-010: Deploy y exposición (Docker + GHCR + Tunnel + Cloudflare Access)
- ADR-011: Integración con Chatwoot por etapas

Los ADR-001 a ADR-007 vienen de la sesión de factibilidad (Opus 4.8).

## Próximo paso

Configurar Cloudflare Access en la app (validación de JWT) para cerrar
el circuito de seguridad antes de avanzar a la Etapa 2 (Kanban visual).

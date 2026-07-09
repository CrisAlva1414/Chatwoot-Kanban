# ADR-009: Estructura del repositorio

- **Fecha:** 2026-07-09
- **Estado:** Aceptado

## Contexto

El repositorio debe ser navegable tanto para humanos como para el LLM. La
estructura debe separar app, config, docs y CI claramente.

## Decisión

```
├── AGENTS.md ← contexto que opencode lee automáticamente
├── app/      ← código fuente de la API
├── docs/     ← documentación (ADR, formatos, sesiones)
├── .github/  ← CI/CD
│   root/*    ← config (docker-compose, Dockerfile, pyproject.toml, ruff.toml, .env.example)
```

## Consecuencias

- `app/` solo contiene Python, sin archivos de config ni docs.
- `docs/` no toca el código; el LLM lo consulta según necesidad.
- Las sesiones en `docs/sesiones/` se numeran secuencialmente e incluyen fecha.

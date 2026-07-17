# Documentación del proyecto

Índice de toda la documentación técnica del plugin Kanban para Chatwoot.

## Arquitectura (ADRs)

| # | Tema | Estado | Archivo |
|---|------|--------|---------|
| 001 | Dashboard App como superficie de integración | Aceptado | [adr/001-dashboard-app-como-superficie-de-integracion.md](adr/001-dashboard-app-como-superficie-de-integracion.md) |
| 002 | Bot-user único para token Chatwoot | Aceptado | [adr/002-bot-user-unico-token-chatwoot.md](adr/002-bot-user-unico-token-chatwoot.md) |
| 003 | Cloudflare Access como auth de agentes | Aceptado | [adr/003-cloudflare-access-auth-agentes.md](adr/003-cloudflare-access-auth-agentes.md) |
| 004 | Audit log aplicativo como atribución real | Aceptado | [adr/004-audit-log-aplicativo-atribucion.md](adr/004-audit-log-aplicativo-atribucion.md) |
| 005 | Modelo de datos de tareas (BD propia) | Aceptado | [adr/005-modelo-datos-tareas.md](adr/005-modelo-datos-tareas.md) |
| 006 | Kanban pipeline sobre custom_attributes | Aceptado | [adr/006-kanban-pipeline-custom-attributes.md](adr/006-kanban-pipeline-custom-attributes.md) |
| 007 | Stack técnico y deploy | Aceptado | [adr/007-stack-tecnico-y-deploy.md](adr/007-stack-tecnico-y-deploy.md) |
| 008 | ADR como registro de decisiones | Aceptado | [adr/008-adr-como-registro.md](adr/008-adr-como-registro.md) |
| 009 | Estructura del repositorio | Aceptado | [adr/009-estructura-del-repositorio.md](adr/009-estructura-del-repositorio.md) |
| 010 | Deploy y exposición (Docker + Tunnel) | Aceptado | [adr/010-deploy-y-exposicion.md](adr/010-deploy-y-exposicion.md) |
| 011 | Integración con Chatwoot por etapas | Aceptado | [adr/011-integracion-con-chatwoot.md](adr/011-integracion-con-chatwoot.md) |
| 012 | Operaciones de escritura y sistema de tareas | Aceptado | [adr/012-operaciones-escritura-kanban.md](adr/012-operaciones-escritura-kanban.md) |

## Convenciones

| Ámbito | Archivo |
|--------|---------|
| Git (commits, ramas, PRs) | [format/git.md](format/git.md) |
| Python (Ruff, tipado, estilo) | [format/python.md](format/python.md) |
| Comentarios (docstrings, inline) | [format/comentarios.md](format/comentarios.md) |

## Sesiones

Bitácora de trabajo para que el LLM retome contexto rápidamente:

| # | Fecha | Tema | Archivo |
|---|-------|------|---------|
| 001 | 2026-07-09 | Factibilidad arquitectura Kanban/Tareas (Opus 4.8) | [sesiones/001-2026-07-09-factibilidad-arquitectura-kanban-tareas.md](sesiones/001-2026-07-09-factibilidad-arquitectura-kanban-tareas.md) |
| 002 | 2026-07-09 | Inicialización Docker, docs, lint | [sesiones/002-2026-07-09-inicializacion-docker-y-docs.md](sesiones/002-2026-07-09-inicializacion-docker-y-docs.md) |
| 003 | 2026-07-13 | Fix producción, tests, seguridad Docker | [sesiones/003-2026-07-13-fix-produccion-y-seguridad-docker.md](sesiones/003-2026-07-13-fix-produccion-y-seguridad-docker.md) |
| 004 | 2026-07-15 | Drag & drop fix, sistema de tareas, dashboard | [sesiones/004-2026-07-15-drag-drop-tareas-dashboard.md](sesiones/004-2026-07-15-drag-drop-tareas-dashboard.md) |
| 005 | 2026-07-16 | Frontend Chatwoot-consistente y client robusto | [sesiones/005-2026-07-16-frontend-tokens-y-client-robusto.md](sesiones/005-2026-07-16-frontend-tokens-y-client-robusto.md) |

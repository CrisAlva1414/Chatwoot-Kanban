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
| 013 | Modelo de ramas y gate de protección | Aceptado | [adr/013-modelo-ramas-y-gate-proteccion.md](adr/013-modelo-ramas-y-gate-proteccion.md) |
| 015 | Pipeline de CI/CD y deploy | Aceptado | [adr/015-pipeline-ci-cd.md](adr/015-pipeline-ci-cd.md) |
| 016 | Migración conversation-based → contact-based | Aceptado | [adr/016-migracion-conversation-a-contact-based.md](adr/016-migracion-conversation-a-contact-based.md) |
| 017 | Desvinculación y apertura open source | Aceptado | [adr/017-desvinculacion-y-apertura-open-source.md](adr/017-desvinculacion-y-apertura-open-source.md) |
| 018 | Demo autocontenida con mock de Chatwoot | Aceptado | [adr/018-demo-mockup-chatwoot.md](adr/018-demo-mockup-chatwoot.md) |

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
| 006 | 2026-07-16 | Sync Chatwoot y badge visual de tareas | [sesiones/006-2026-07-16-sync-chatwoot-badge-visual.md](sesiones/006-2026-07-16-sync-chatwoot-badge-visual.md) |
| 007 | 2026-07-17 | Fix fechas, estado, drag & drop y polling | [sesiones/007-2026-07-17-fix-fechas-estado-dragdrop-polling.md](sesiones/007-2026-07-17-fix-fechas-estado-dragdrop-polling.md) |
| 008 | 2026-07-17 | Blindaje CI/CD y staging | [sesiones/008-2026-07-17-blindaje-ci-cd-staging.md](sesiones/008-2026-07-17-blindaje-ci-cd-staging.md) |
| 009 | 2026-07-23 | Performance de board: pooling y cache | [sesiones/009-2026-07-23-performance-board-pooling-cache.md](sesiones/009-2026-07-23-performance-board-pooling-cache.md) |
| 010 | 2026-07-26 | Migración contact-based | [sesiones/010-2026-07-26-migracion-contact-based.md](sesiones/010-2026-07-26-migracion-contact-based.md) |
| 011 | 2026-07-26 | Operaciones no bloqueantes y optimizaciones | [sesiones/011-2026-07-26-non-blocking-optimizaciones.md](sesiones/011-2026-07-26-non-blocking-optimizaciones.md) |
| 012 | 2026-07-31 | Desvinculación, limpieza y open source | [sesiones/012-2026-07-31-desvinculacion-limpieza-open-source.md](sesiones/012-2026-07-31-desvinculacion-limpieza-open-source.md) |
| 013 | 2026-08-30 | Demo autocontenida y capturas para el README | [sesiones/013-2026-08-30-demo-mockup-readme.md](sesiones/013-2026-08-30-demo-mockup-readme.md) |

# ADR-011: Integración con Chatwoot (etapas)

- **Fecha:** 2026-07-09
- **Estado:** Aceptado
- **Suplanta:** ADR-007 (etapas definidas originalmente en sesión de factibilidad)

## Contexto

Chatwoot expone una API REST con filtros, custom attributes, y webhooks.
No tenemos acceso al frontend de Chatwoot (solo iframe). La integración
debe construirse por etapas para validar el shape real de los datos antes
de modelar el dominio.

La sesión de factibilidad (Opus 4.8) definió 5 etapas. Este ADR las
formaliza y las mapea a los endpoints concretos.

## Decisión

Evolucionar en 5 etapas progresivas:

| Etapa | Objetivo | Endpoints / Componentes |
|-------|----------|------------------------|
| 0 | Cloudflare Access + validación JWT + tabla `agentes` | `GET /health` + middleware JWT |
| 1 | Exploración read-only de Chatwoot | `GET /debug/custom-attribute-definitions`<br>`POST /debug/conversations/filter` |
| 2 | Escritura puntual y validación de webhook | `POST /custom_attributes` + webhook `conversation_updated` |
| 3 | Feature 1: Kanban completo con drag & drop | Frontend Kanban + sincronización entre agentes |
| 4 | Feature 2: Tareas (creación, cron, bloqueo 1-activa, panel histórico) | CRUD tareas + cron 23:30 + audit log |

Reglas:
- Cada etapa produce un ADR o actualización del existente si cambia la dirección.
- No se salta a la siguiente sin validar la actual.
- Las etapas 0 y 1 pueden solaparse (infraestructura + exploración).

## Consecuencias

- Los schemas Pydantic del dominio Kanban se definen al inicio de la Etapa 3,
  una vez conocido el shape real de Chatwoot.
- `chatwoot_client.py` ya tiene métodos de escritura listos (Etapa 2+).
- La UI del Kanban será HTML/JS plano servido por FastAPI, sin framework
  frontend pesado.
- Etapa 0 se implementa como middleware FastAPI que valida el JWT de
  Cloudflare Access.

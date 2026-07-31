# ADR-001 — Dashboard App como superficie de integración con Chatwoot

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-07-09 |
| **Proyecto** | kanban.example.com |
| **Decidido por** | Sesión de factibilidad técnica inicial |

---

## Contexto

Chatwoot (self-hosted en `chatwoot.example.com`) ofrece una funcionalidad llamada Dashboard App que permite embeber una URL externa como `<iframe>` dentro de la vista de conversación de cada agente. El objetivo era determinar si esta superficie es suficiente para construir un Kanban de pipeline y un sistema de tareas.

## Decisión

Usar el Dashboard App de Chatwoot como punto de entrada visual (iframe), pero no como canal de comunicación ni de autenticación. Todo el trabajo real se hace contra la **API REST de Chatwoot**, independiente del iframe.

## Fundamento técnico

El Dashboard App provee dos mecanismos:

1. **`postMessage` pasivo (Chatwoot → iframe):** entrega `appContext` con `conversation`, `contact` y `currentAgent` para la conversación abierta en ese momento. No está firmado criptográficamente ni es verificable por un backend externo.
2. **Flag `hmac_verified`:** existe en el payload pero aplica a la verificación de identidad del contacto en el widget de chat público, no a la autenticación de agentes internos. No sirve para este caso.

El canal inverso (iframe → Chatwoot) no existe vía `postMessage`. Cualquier escritura de datos en Chatwoot (custom attributes, mensajes) debe hacerse vía API REST con un token válido.

## Consecuencias

- El `postMessage` se usa **solo como contexto de UX** (saber qué conversación está mirando el agente en ese momento), nunca como credencial.
- La aplicación es en práctica una **mini-SPA con su propio backend** que vive dentro del iframe y se comunica directamente con la API REST de Chatwoot.
- No hay canal push nativo desde la app hacia Chatwoot, salvo hacer llamadas REST.

## Alternativas descartadas

- **Confiar en `postMessage` como credencial:** descartado porque cualquier página puede simular ese mensaje sin verificación de origen criptográfica.
- **Usar exclusivamente el dashboard nativo de Chatwoot:** descartado porque Chatwoot no tiene Kanban por pipeline ni sistema de tareas nativo.

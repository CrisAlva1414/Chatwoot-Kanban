# ADR-002 — Bot-user único como mecanismo de autenticación hacia Chatwoot

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-07-09 |
| **Proyecto** | kanban.example.com |
| **Decidido por** | Sesión de factibilidad técnica inicial |

---

## Contexto

Para realizar llamadas a la API REST de Chatwoot desde el backend propio, se necesita un `api_access_token` válido. Chatwoot no dispone de tokens con scope reducido (issue #12590, abierto en la comunidad): cualquier token hereda todos los permisos del usuario al que pertenece, independientemente de su rol.

Cada agente, incluso con rol básico, tiene acceso a su propio Personal Access Token desde su perfil sin aprobación de admin. Esto multiplica la superficie de ataque linealmente con el tamaño del equipo y no existe un panel centralizado donde un administrador vea todos los tokens activos de la cuenta.

## Decisión

Usar un único **bot-user dedicado** (ej. `api-bot@example.com`) con rol de Agente, cuyo token vive exclusivamente en las variables de entorno del backend. El token nunca se expone al frontend ni a ningún agente humano.

## Fundamento técnico

| Opción | Surface de riesgo | Operación | Decisión |
|---|---|---|---|
| Token por agente humano | Alta — crece con el equipo, sin visibilidad centralizada | Alta — requiere onboarding por agente y riesgo de tokens huérfanos al salir personal | Descartado |
| Bot-user único en backend | Baja — un solo token, controlado, nunca en cliente | Baja — un solo token que rotar si se compromete | **Elegido** |

El riesgo residual aceptado es que el token del bot-user tiene scope de cuenta completa (limitación de plataforma, no resoluble hoy). Se mitiga porque:
- El token nunca sale del backend.
- El backend solo expone al frontend los endpoints específicos que el Kanban y las tareas necesitan.
- Si el token se compromete, el blast radius está contenido a quien tenga acceso al servidor.

## Nota sobre lifecycle

A diferencia de lo que podría asumirse, si se desactiva un usuario en Chatwoot su token queda inválido (no huérfano activo). Esto hace que un token por agente humano sea además un punto de falla operacional: si el agente que generó el token deja la empresa, la integración se rompe. El bot-user no depende de ningún humano.

## Consecuencias

- El backend actúa como proxy controlado entre el frontend y la API de Chatwoot.
- La atribución real de quién hizo cada acción no puede venir de Chatwoot (todas las acciones aparecen como hechas por el bot-user en el dashboard nativo). Se resuelve en capa propia — ver ADR-004.
- El `sender_id` en mensajes/notas creados vía API se deriva del token que llama; no es parametrizable. Confirmado: el endpoint `POST .../messages` no acepta `sender_id` arbitrario en el body.

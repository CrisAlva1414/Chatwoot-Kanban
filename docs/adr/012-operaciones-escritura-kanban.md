# ADR-012 — Operaciones de escritura en el Kanban y sistema de tareas

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-07-15 |
| **Proyecto** | kanban.ruki-bot.com |
| **Decidido por** | Sesión 004 |

---

## Contexto

El Kanban actual solo lee datos de Chatwoot. El drag & drop envía el cambio directamente a la API de Chatwoot sin pasar por el backend, lo que impide:
- Registro de quién hizo el cambio (audit trail)
- Consistencia entre la BD propia y Chatwoot
- Sistema de tareas con trazabilidad

Se necesita definir cómo el backend toma control de las escrituras, implementa el sistema de tareas 1:1 con conversaciones, y mantiene sincronizado el espejo en Chatwoot.

## Decisión

### 1. Drag & drop: el backend es intermediario

El frontend **nunca** llama directo a la API de Chatwoot. Todas las escrituras pasan por endpoints propios que:
1. Extraen el actor de la sesión autenticada
2. Escriben en `task_audit_log` (fuente de verdad de atribución)
3. Llaman a la API de Chatwoot
4. Si Chatwoot falla → registran `chatwoot_call_ok = false` y propagan el error

**Nuevo endpoint:** `PATCH /kanban/board/{conversation_id}/stage`

### 2. Sistema de tareas: relación 1:1 con conversación

Cada conversación tiene **exactamente 1 tarea activa**. Si se crea una nueva tarea para una conversación que ya tiene una activa, se sobrescribe (UPDATE). Cualquier agente puede crear, editar o cerrar cualquier tarea (pool rotativo).

**Custom attributes en Chatwoot** (espejo para idempotencia):

| Key | Tipo | Propósito |
|-----|------|-----------|
| `tarea_estado` | `List` | Estado actual de la tarea |
| `tarea_vencimiento` | `Date` | Fecha límite |

**BD propia** (fuente de verdad): tabla `tareas` ya existente.

**Sobrescribir una tarea** genera un audit log con `action='task_overwritten'` que incluye en `previous_state` los datos de la tarea reemplazada y quién la creó.

### 3. Sync: writes → BD → Chatwoot

Cada operación de escritura sigue el patrón:
1. Escribir en BD (canonical)
2. POST custom_attribute a Chatwoot
3. Si falla → `sync_pendiente = true`
4. Reintentar en el siguiente cron tick o en la siguiente operación sobre esa tarea

### 4. Cron: transiciones automáticas

Endpoint `POST /kanban/cron/tick` ejecutado por un cron externo a las **23:30** diarias:
- `tarea_activa` → `tarea_hoy` cuando `fecha_vencimiento <= hoy`
- `tarea_hoy` → `tarea_vencida` (no se cerraron a tiempo)
- Reintenta filas con `sync_pendiente = true`

Cada transición escribe audit log con `source='cron'`.

### 5. Dashboard de agentes

Página separada (`/kanban/dashboard`) con botón "Volver al Kanban". Muestra métricas por agente calculadas desde `task_audit_log`:
- Tareas creadas, cerradas, sobreescritas
- Tasa de cierre a tiempo
- Tiempo promedio de resolución
- Historial de últimas tareas con trazabilidad completa

## Fundamento técnico

- **Custom attributes como espejo:** Permiten que Chatwoot siga funcionando si el backend cae. El agente puede ver `tarea_estado` y `tarea_vencimiento` directamente en Chatwoot.
- **BD propia como canonical:** Resuelve el problema de audit trail, permite métricas complejas, y desacopla la lógica de negocio del schema de Chatwoot.
- **1:1 por conversación:** El `UNIQUE` en `conversation_id` garantiza integridad a nivel de DB. No se necesitan locks ni transiciones complejas.
- **Cron único a las 23:30:** Simplifica la operación. Un solo punto de ejecución maneja todas las transiciones diarias.

## Consecuencias

- El frontend se simplifica: solo habla con endpoints propios, nunca con Chatwoot directamente.
- Si el backend cae, Chatwoot sigue mostrando el estado actual de las tareas (espejo).
- El audit log permite reconstruir la historia completa de cada conversación: quién movió la card, quién creó/cerró la tarea, quién la sobre-escribió.
- El cron es un endpoint HTTP que se llama desde un cron externo, no un scheduler embebido. Más simple de monitorear y depurar.

## Alternatives considered

| Alternativa | Por qué se descartó |
|-------------|---------------------|
| Scheduler embebido (APScheduler) | Complejidad innecesaria. Un endpoint HTTP + cron del NAS es más simple y observable. |
| Webhooks de Chatwoot para sync | Los webhooks de Chatwoot tienen bugs históricos de duplicación (#7402). No son confiables como fuente primaria de sync. |
| Relación 1:N (tareas múltiples por conversación) | Complica el modelo sin beneficio. El negocio maneja 1 misión por lead a la vez. |
| Todo en Chatwoot custom attributes | Imposible hacer métricas complejas, audit trail, o dashboard sin parsear texto libre. |

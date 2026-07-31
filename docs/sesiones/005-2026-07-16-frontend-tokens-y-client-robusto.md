# Sesión 005 — Frontend Chatwoot-consistente, client robusto y sistema de tareas UI

- **Fecha:** 2026-07-16
- **Propósito:** Alinear el frontend con el theme de Chatwoot (light/dark via
  `prefers-color-scheme`), pulir la barra de controles, ocultar scrollbars,
  robustecer el chatwoot client con connection pooling y retry, e implementar
  la UI del sistema de tareas (modal crear/editar/cerrar).

## Contexto

El Kanban y Dashboard funcionaban correctamente pero visualmente no se
integraban con el theme de Chatwoot. El frontend usaba colores hardcoded
(`#fff`, `#f7f7f7`, `#ececec`) sin soporte dark mode nativo, el header
tenía un label "Kanban" redundante, y los selects/botones tenían alturas
desiguales. Además, el chatwoot_client creaba un `httpx.AsyncClient` nuevo
por cada llamada (sin pooling) y no tenía reintentos. El sistema de tareas
tenía endpoints en el backend pero ninguna UI para crear, editar o cerrar
tareas desde el Kanban.

## Cambios realizados

### 1. Sistema de CSS tokens (kanban.html + dashboard.html)

Nuevo sistema de variables CSS con formato RGB espaciado para composición
con opacidad:

```css
:root {
  --bg-page: 254 254 254;
  --text-primary: 28 32 36;
  --text-secondary: 96 100 108;
  --border: 240 240 243;
  --bg-card: 254 254 254;
  --accent: 39 129 246;
  ...
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg-page: 20 21 23;
    --text-primary: 237 238 240;
    --border: 40 42 46;
    --bg-card: 28 29 32;
    ...
  }
}
```

- Dark mode detectado vía `prefers-color-scheme`, sin JS ni postMessage
- Eliminado el bloque `.dark .column { ... }` hardcoded
- Eliminado `class="light"` del `<html>`
- Body background: `rgb(var(--bg-page))` (nunca blanco/negro puro)
- Font stack: `system-ui, -apple-system, BlinkMacSystemFont, ...`

### 2. Header del Kanban

- Eliminado `<h1>Kanban</h1>` (redundante con la pestaña de Chatwoot)
- Selector de etapas ahora es el primer elemento
- "Todas las etapas" como primer `<option>` (default en carga limpia)
- Clase `.btn` unificada para botones y links (mismo padding, font-size,
  line-height)
- Flexbox `align-items: center` para alineación vertical

### 3. Scrollbars ocultas

```css
.board, .column-body { scrollbar-width: none; }
.board::-webkit-scrollbar, .column-body::-webkit-scrollbar { display: none; }
```

Contenido sigue siendo desplazable sin mostrar la barra nativa.

### 4. Cards y columnas — sutileza

- Cards: borde `rgb(var(--border))`, hover solo cambia border (sin sombra)
- Columnas: fondo `rgb(var(--bg-surface))` (se distingue del page sutilmente)
- Border-radius: 8px (moderado)
- Bordes casi imperceptibles, nunca grises de Tailwind por defecto

### 5. Chatwoot client robusto (chatwoot_client.py)

- **Connection pooling:** `httpx.AsyncClient` se crea una vez en `init()`,
  se reutiliza en cada request, se cierra en `close()`
- **Retry con backoff:** hasta 3 reintentos en errores 5xx o de red,
  con delays exponenciales (0.5s, 1s, 2s). Errores 4xx no se reintentan
- **Método `_request()` centralizado:** reemplaza la duplicación de código
  en los 3 métodos del client
- **Lifespan actualizado:** `main.py` llama `chatwoot_client.init()` y
  `chatwoot_client.close()` en el lifespan de FastAPI

### 6. Dashboard actualizado

Mismo sistema de tokens y dark mode que el Kanban. Eliminado Tailwind CDN
(no se usaba). Badges, tablas, stat-cards — todo con tokens.

### 7. Modal de tareas (kanban.html)

Click en una card del Kanban ahora abre un modal con gestión de tareas en
vez de abrir Chatwoot directamente. El modal incluye:

**Sin tarea existente:**
- Formulario con mensaje (textarea) y fecha de vencimiento (date input)
- Botón "Crear tarea" que llama `POST /kanban/tasks`
- Link "Abrir en Chatwoot" para acceder a la conversación

**Con tarea activa:**
- Info de la tarea: estado, mensaje, vencimiento, creada por
- Formulario pre-llenado para editar mensaje y fecha
- Botones "Guardar" (`PATCH /kanban/tasks/{id}`) y "Cerrar tarea"
  (`PATCH /kanban/tasks/{id}/close`)

**Con tarea cerrada:**
- Solo muestra info de la tarea (estado Cerrada)
- Botón "Cerrar" para dismiss

**UX:**
- Overlay con click fuera para cerrar
- Botón X en la esquina
- Toast de confirmación después de cada acción
- Board se refresca automáticamente después de crear/editar/cerrar
- Botones se deshabilitan durante la请求 para evitar doble-click
- Tokens CSS consistentes (modal, botones, badges de estado)

## Archivos tocados

**Modificados:**
- `app/templates/kanban.html` — CSS tokens, header, scrollbars, dark mode,
  modal de tareas (CSS + JS completo)
- `app/templates/dashboard.html` — CSS tokens, dark mode, eliminado Tailwind
- `app/chatwoot_client.py` — connection pooling, retry con backoff
- `app/main.py` — lifespan con init/close del chatwoot client
- `tests/conftest.py` — mock de chatwoot_client.init/close en lifespan

## Tests

29 tests pasando (sin cambios en la suite, solo actualizado el fixture de
lifespan para mockear init/close del chatwoot client).

## Commits

| # | Hash | Descripción |
|---|------|-------------|
| 1 | `c37bd9e` | style: correct the frontend tokens and make the client more robust |
| 2 | `5090e0f` | feat(kanban): add task modal for create, edit and close from UI |

**Estado:** Desplegado en producción (kanban.example.com).

## Próximo paso

- Conectar Cloudflare Access para atribución real de agentes
- Configurar cron job en el NAS (23:30 diarias, `POST /kanban/cron/tick`)
- Evaluar: sync entre agentes vía webhook `conversation_updated`

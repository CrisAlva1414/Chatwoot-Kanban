# Pipeline Kanban — Dashboard App para Chatwoot

Kanban para visualizar y mover la "Etapa del embudo" de las conversaciones de
Chatwoot, embebido como Dashboard App. Diseñado para el patrón de despliegue
de Ruki-System: proyecto Docker independiente, sin puertos al host, expuesto
solo vía Cloudflare Tunnel.

Servicio: `kanban_plugins` · Proyecto Arcane: `plugins-kanban` · Red: `ruki_plugins_kanban`

## Arquitectura

```
Internet → Cloudflare Edge → cloudflared (en ruki_plugins_kanban) → kanban_plugins:3000
                                                                          ↓ api_access_token
                                                                     API de Chatwoot
```

El token de Chatwoot vive solo en `.env` del servidor, nunca en el navegador.
El navegador solo conoce `PLUGIN_SECRET`, usado como header `x-plugin-key`
para que el backend valide que la petición viene del propio Dashboard App.

Sin acceso al socket Docker / `ruki-socket-proxy` — este servicio no gestiona
contenedores, solo habla HTTP con Chatwoot. Aislamiento máximo intencional
(superficie de ataque mínima).

## 1. Configurar Chatwoot

1. Settings → Custom Attributes → crear `Etapa del embudo` (tipo List,
   applies to Conversation): Prospección, Contactado, Cotización enviada,
   Negociación, Ganado, Perdido.
2. Click en el atributo y anota el **attribute key** generado (ej.
   `etapa_del_embudo`) → va en `CHATWOOT_ETAPA_ATTRIBUTE_KEY`.
3. Profile → Access Token (o crear un Agent Bot dedicado).
4. Account ID en la URL: `/app/accounts/{ID}/...`.

## 2. Red Docker compartida con cloudflared

Siguiendo ADR-003 (ICC off + redes explícitas), `cloudflared` necesita estar
en la misma red que este servicio para resolverlo por nombre. Si la red no
existe aún:

```bash
docker network create ruki_plugins_kanban
```

Luego, en el proyecto de `cloudflared` en Arcane, agregar `ruki_plugins_kanban`
a sus `networks:` (igual que ya está en `ruki_chatwoot`, `ruki_arcane`, etc.).

## 3. Variables de entorno

En el servidor (nunca por chat — ver `docs/setup.md`):

```bash
cp .env.example .env
nano .env
echo "PLUGIN_SECRET generado: $(openssl rand -hex 32)"  # pegar en .env
```

## 4. Desplegar desde Arcane (Git Sync)

Este repo es exclusivo para el plugin — `compose.yaml` vive en la raíz junto
al `Dockerfile`, `backend/` y `frontend/`. Arcane clona el directorio completo.

1. **Customize → Git Repositories → Add Repository** — URL del repo +
   autenticación (PAT o SSH key).
2. **Projects → dropdown junto a "Create Project" → From Git Repo.**
3. **Sync Name:** `plugins-kanban`
4. **Repository / Branch:** este repo, `main`.
5. **Compose File Path:** `compose.yaml` (raíz).
6. **Auto Sync:** activar — un `git push` futuro redepliega solo (nota: solo
   redepliega si el proyecto ya está corriendo).
7. **Create Sync.**

El `compose.yaml` queda **read-only** desde la UI (se edita vía Git). El
`.env` sí queda editable directo en Arcane — ahí completas
`CHATWOOT_API_TOKEN`, `CHATWOOT_ACCOUNT_ID` y `PLUGIN_SECRET` (nunca van al
repo).

Después de crear el sync, Arcane hace `build` con el `Dockerfile` del repo
— no se necesita registry ni imagen pre-construida.

## 5. Ruta pública en Cloudflare Tunnel

En el dashboard de Cloudflare Zero Trust, agregar Public Hostname:

| Subdominio | Servicio interno |
|---|---|
| `plugins.ruki-bot.com` (o subruta `/kanban`) | `http://kanban_plugins:3000` |

El nombre de host interno (`kanban_plugins`) es el nombre del servicio en
`compose.yaml` — Docker lo resuelve dentro de `ruki_plugins_kanban`.
Si Compose le agrega sufijo de réplica (`kanban_plugins-1`), usar ese nombre
exacto en la ruta de Cloudflare (revisar con `docker ps`).

## 6. Probar antes de conectar a Chatwoot

Desde dentro de la red (ej. exec en el propio contenedor o desde cloudflared):

```bash
curl -H "x-plugin-key: TU_PLUGIN_SECRET" http://kanban_plugins:3000/api/kanban/conversations
```

O ya con el dominio público una vez la ruta de Cloudflare esté activa:

```bash
curl -H "x-plugin-key: TU_PLUGIN_SECRET" https://plugins.ruki-bot.com/api/kanban/conversations
```

Debe devolver JSON con `etapas` y `conversations`. 401/403 → revisar que el
header coincida con `PLUGIN_SECRET` en `.env`.

## 7. Configurar el Dashboard App en Chatwoot

Settings → Integrations → Dashboard Apps → Configure → Add new Dashboard App:

- **Title:** Pipeline
- **URL:** `https://plugins.ruki-bot.com/?k=TU_PLUGIN_SECRET`

Abrir cualquier conversación → debería aparecer la pestaña "Pipeline".

## Notas de seguridad / próximos pasos honestos

- `PLUGIN_SECRET` en la URL es la primera capa, no es perfecta (queda en
  logs de Cloudflare/historial del navegador). Mejora futura sin rehacer
  nada: JWT de corta duración via un endpoint de login propio.
- `CHATWOOT_FRAME_ANCESTOR` fija el único dominio que puede embeber este
  iframe — si no coincide con `chat.ruki-bot.com`, el iframe no carga.
- Rotar `PLUGIN_SECRET` y `CHATWOOT_API_TOKEN` periódicamente: cambiar en
  `.env`, `docker compose -p plugins-kanban -f compose.yaml up -d` (recrea el contenedor),
  actualizar la URL en el Dashboard App de Chatwoot.
- Este patrón (frontend estático + backend Express con `requirePluginKey`,
  sin socket Docker, red propia) es la base para los próximos plugins bajo
  `plugins.ruki-bot.com` — duplicar la carpeta, nuevo nombre de servicio
  bajo el mismo proyecto `plugins_*`, nueva red si se quiere aislar, y
  cambiar la lógica de negocio en su propio cliente de API.
- Si en algún momento un plugin futuro SÍ necesita gestionar contenedores
  Docker, conectarlo a `ruki_socket_proxy` explícitamente — no por defecto.

## Comandos útiles

```bash
docker compose -p plugins-kanban -f compose.yaml restart kanban_plugins   # tras cambiar .env
docker compose -p plugins-kanban -f compose.yaml down                     # apagar
docker compose -p plugins-kanban -f compose.yaml logs -f                  # logs en vivo
docker compose -p plugins-kanban -f compose.yaml pull && docker compose -p plugins-kanban -f compose.yaml up -d --build  # actualizar
```

# Demo con datos de ejemplo

Tooling local de desarrollo para explorar la interfaz sin una instancia real
de Chatwoot y para regenerar las capturas que se muestran en el README.
Levanta el stack real de la app (FastAPI + PostgreSQL) y lo conecta a un
**mock de la API de Chatwoot** que sirve datos de contacto de ejemplo.

> **Nota:** todo lo que está bajo `demo/` y el `docker-compose.demo.yml`
> están en `.gitignore` — es una herramienta de desarrollo y **no se
> publica** en el repositorio. Las capturas `docs/demo/*.png` sí se
> versionan porque se muestran en el README.

## Qué incluye

```
demo/
├── mock_chatwoot.py    ← API mock de Chatwoot (contactos, filtros, atributos, avatares)
├── seed_db.py          ← Siembra la BD local (agentes + auditoría) para el dashboard
├── screenshot.py       ← Genera los PNG de docs/demo con Playwright
├── Dockerfile          ← Imagen del mock de Chatwoot
└── requirements.txt

docker-compose.demo.yml ← Orquesta mock + postgres + app + seed
docs/demo/*.png         ← Capturas usadas en el README
```

## Levantar la demo

```bash
docker compose -f docker-compose.demo.yml up -d --build
```

| Servicio            | URL                          | Rol                                    |
|---------------------|------------------------------|----------------------------------------|
| `app`               | http://localhost:8000/kanban | Tablero Kanban (iframe de Chatwoot)    |
| `app`               | http://localhost:8000/kanban/dashboard | Dashboard de agentes         |
| `mock-chatwoot`     | http://localhost:8095        | API fake de Chatwoot                   |
| `postgres`          | localhost:5433               | BD PostgreSQL de la demo               |

Detener y borrar todo:

```bash
docker compose -f docker-compose.demo.yml down -v
```

## Cómo funciona el mock

`mock_chatwoot.py` reimplementa **solo** los endpoints que usa el cliente
HTTP de la app (`ChatwootClient`):

- `GET /api/v1/accounts/1/custom_attribute_definitions`
- `POST /api/v1/accounts/1/contacts/filter`
- `GET|PATCH /api/v1/accounts/1/contacts/{contact_id}`
- `GET /avatars/{seed}.svg` (avatares generados en tiempo real)

Los `pipeline_01_etapas`, `kanban_view_mensaje` y
`kanban_view_fecha_termino` viven en los `custom_attributes` de cada
contacto, igual que en un Chatwoot real. Las fechas de vencimiento se
calculan en relación a la fecha actual, por lo que el tablero siempre
muestra tareas activas, "vence hoy" y vencidas independientemente del día
en que se corra la demo.

`seed_db.py` puebla la BD local (vía `docker compose` service `db-seed`)
con agentes y eventos de auditoría para que el dashboard muestre estadísticas
realistas. Es idempotente: no vuelve a sembrar si ya lo hizo.

## Regenerar las capturas del README

```bash
pip install playwright && playwright install chromium
python demo/screenshot.py
```

Las imágenes se escriben en `docs/demo/` (light y dark).

## Notas

- Los avatares los sirve el propio mock (SVG con iniciales), así que el
  demo funciona sin acceso a Internet.
- El mock conserva el estado en memoria: mover un contacto de columna
  (drag & drop) o editar una tarea actualiza el contacto dentro del proceso.
- Si tu cliente de Docker negocia una API vieja, prueba
  `DOCKER_API_VERSION=1.44 docker compose -f docker-compose.demo.yml up -d`.
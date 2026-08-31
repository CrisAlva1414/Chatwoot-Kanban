# ADR-018: Demo autocontenida con mock de Chatwoot

- **Fecha:** 2026-08-30
- **Estado:** Aceptado
- **Autor(es):** opencode (asistido)
- **Suplanta:** —

## Contexto

El proyecto no tiene frontend propio y la interfaz (kanban + dashboard) se
visualiza embebida en Chatwoot. La app depende de dos piezas externas: la
API REST de Chatwoot y PostgreSQL. Para mostrar el proyecto en el README (o
a un cliente) haría falta una instancia real de Chatwoot con contactos,
custom attributes y un bot token, lo cual no es viable para una demo.

## Decisión

Incorporar una **demo autocontenida** en `demo/` que levanta el stack real
de la app pero conectándolo a un **mock de la API de Chatwoot**:

- `demo/mock_chatwoot.py` — reimplementa los endpoints que usa
  `ChatwootClient` (`custom_attribute_definitions`, `contacts/filter`,
  `contacts/{id}` GET/PATCH) servidos desde un FastAPI ligero con contactos
  seed en memoria. Las fechas de vencimiento se generan relativas a *hoy*
  para que el tablero siempre muestre tareas activas, de hoy y vencidas.
- `demo/seed_db.py` — siembra la BD local (agentes + auditoría) para que el
  dashboard tenga estadísticas realistas. Idempotente.
- `docker-compose.demo.yml` — orquesta `postgres`, `mock-chatwoot` (:8095),
  `db-seed` y `app` (:8000).
- `demo/screenshot.py` — genera las capturas de `docs/demo/` con Playwright.

La demo **no modifica el código de la app**: solo apunta
`CHATWOOT_BASE_URL` al mock. La app no distingue entre un Chatwoot real y el
mock más allá de la URL.

El tooling de la demo (`demo/` y `docker-compose.demo.yml`) está en
`.gitignore`: es una herramienta de desarrollo local para regenerar las
capturas; no se publica. Las capturas `docs/demo/*.png` sí se versionan
porque el README las referencia.

## Consecuencias

- **Positivas:**
  - Demo reproducible con un comando, sin credenciales ni instancia de
    Chatwoot, incluso sin Internet (los avatares los genera el propio mock).
  - Ejercita el stack completo (FastAPI + asyncpg + PostgreSQL), no una
    UI falseada.
  - Las capturas del README se regeneran con el mismo `docker-compose.demo.yml`
    que la demo.
- **Negativas:**
  - El mock conserva estado solo en memoria: cada `up` reinicia los contactos.
  - No cubre webhooks (el flujo `contact_updated`/`conversation_updated`),
    ni paginación profunda (solo 28 contactos).
- **Riesgos:**
  - Si el mock se usa para demostrar "en vivo", cambios de columna/ediciones
    no persisten entre reinicios de contenedor.
  - Mantener el set de datos teaser puede quedar desactualizado si la app
    cambia de keys de custom attributes.

## Alternativas consideradas

| Opción | Pros | Contras | ¿Por qué no? |
| ------ | ---- | ------- | ------------ |
| Mock server HTTP separado (elegida) | App intacta, stack completo, sin tocar código prod | Otro servidor de red que mantener | — |
| Modo "demo" dentro de la app (env flag) | Sin servicio extra | Invasivo: toca `chatwoot_client`, `database`, routers y tests | Mayor acoplamiento y riesgo de regresiones |
| SQLite en vez de Postgres en demo | Sin servicio de BD | El código usa JSONB, `RETURNING`, índices parciales de Postgres | Reescritura de `app/database.py` |
| Levantar una instancia real de Chatwoot (docker) | Máxima fidelidad | Pesado, requiere seed vía API, versiones, migraciones | Demasiado costoso para mostrar una UI |
# ADR-015 — Pipeline de integración continua y deploy

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-07-17 |
| **Proyecto** | kanban.ruki-bot.com |
| **Decidido por** | Sesión 008 |

---

## Contexto

El proyecto tiene un único workflow de CI (`docker_publish.yml`) que buildea y publica la imagen en GHCR al hacer push a `main`. No hay testing automatizado, no hay pipeline para staging, y el deploy es manual via Arcane.

Con la adición del entorno de staging y la branch protection, necesitamos:
1. Tests automáticos en cada PR
2. Build de la imagen para staging (`:develop`)
3. Deploy automático a ambos entornos via Arcane GitOps

## Decisión

### Pipeline de testing (`test.yml`)

Trigger: PR a `main` **y** PR a `develop`.

**Jobs:**
- **lint**: `ruff check` + `ruff format --check`
- **test**: pytest con Postgres 16 efímero como servicio del job

**Por qué no mypy:** El proyecto tiene ~1800 líneas de Python, Ruff ya tipa bastante, y 29 tests existentes cubren los flujos críticos. Integrar mypy sería overhead sin beneficio real en esta etapa.

### Pipeline de build (`docker_publish_develop.yml`)

Copia del workflow de producción con:
- Trigger: push a `develop`
- Tag: `:develop` (no `:main`)
- Platforms: `linux/arm64` solo (NAS es OrangePi5 ARM)
- Mismo registry, misma cache GHA

### Deploy: Arcane GitOps (sin SSH)

**Decisión clave:** El deploy NO usa SSH desde GitHub Actions. Arcane GitOps maneja el ciclo completo.

**Configuración en Arcane:**
1. Dos Git-syncs apuntando al mismo repo (`I-Labs-Chile/Ruki-Plugins-Kanban`)
2. Sync producción: branch `main`, compose file `docker-compose.yml`
3. Sync staging: branch `develop`, compose file `developer-compose.yml`
4. Auto Sync habilitado en ambos (polling cada 1-2 minutos)

**Flujo:**
```
Push a main/develop → GitHub Actions build → GHCR tag → Arcane detecta cambio → Pull + Redeploy
```

### `docker_publish.yml` de producción

Se mantiene intacto excepto:
- Platforms se cambia a `linux/arm64` (el NAS es ARM)
- La branch protection exige `test.yml` como required status check

### Webhook vs Auto Sync

Arcane tiene Auto Sync (polling). Para deploys instantáneos, se puede configurar un webhook en GitHub que llame a la API de Arcane para forzar sync. Esto queda como mejora futura; Auto Sync con intervalo corto es suficiente por ahora.

## Consecuencias

- **Positivas:** Testing automatizado, deploy automático a staging, gate de calidad para producción
- **Negativas:** Sin SSH, no hay deploy programático desde CI (dependemos de Arcane polling)
- **Riesgos:** Si Arcane cae, el deploy automático se detiene (manualmente se puede hacer `docker compose pull && up -d`)

## Alternativas consideradas

| Opción | Pros | Contras | ¿Por qué no? |
|--------|------|---------|---------------|
| Deploy via SSH desde Actions | Control total, instantáneo | Requiere SSH expuesto, deploy keys, attack surface | NAS sin SSH público, complejidad innecesaria |
| Self-hosted runner en NAS | Deploy local, sin SSH | Mantener runner, seguridad del runner | Overhead para 1 persona |
| Solo Arcane (sin GitHub Actions) | Todo en un lugar | Sin testing en CI, sin build automatizado | No hay gate de calidad |
| Arcane + webhook de GitHub | Deploy instantáneo | Configuración adicional de webhook | Auto Sync es suficiente por ahora |

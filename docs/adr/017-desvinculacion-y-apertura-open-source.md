# 017: Desvinculación y apertura como open source

- **Fecha:** 2026-07-31
- **Estado:** Aceptado
- **Autor:** Cristian Alvarez
- **Suplanta:** N/A
- **Suplantado por:** N/A

## Contexto

El proyecto fue desarrollado originalmente como plugin interno para la instancia
Chatwoot de la empresa, bajo el namespace `I-Labs-Chile/Ruki-Plugins-Kanban`. La
empresa decidió no utilizar el plugin y el proyecto quedó sin mantenimiento activo.

El repositorio fue transferido al perfil personal `CrisAlva1414` para su
liberación como open source, desvinculándolo completamente de la empresa original
y abriendo la posibilidad de contribuciones externas.

## Decisión

### Limpieza de referencias

Se eliminaron todas las referencias a la empresa original del código fuente,
infraestructura y documentación histórica:

| Elemento original | Reemplazo |
|---|---|
| `ruki-plugins-kanban` | `chatwoot-kanban` |
| `ruki-kanban-postgres` / `ruki-kanban-kanban` | `chatwoot-kanban-db` / `chatwoot-kanban-app` |
| `ruki_cloudflared` | `chatwoot_shared` |
| `ruki-bot.com` / `chatwoot.ruki-bot.com` | `example.com` (placeholders) |
| `@i-labs.cl` / `bot@i-labs.cl` | `@example.com` / variable `CHATWOOT_BOT_EMAIL` |
| `i-labs` / `i-labs-chile` | `the-company` (docs históricos) |
| `ghcr.io/i-labs-chile/...` | `ghcr.io/crisalva1414/...` |
| `I-Labs-Chile` | `CrisAlva1414` |

### Valores hardcodeados → configurables

- `bot@i-labs.cl` → `settings.chatwoot_bot_email` (desde `.env`)
- URLs de Chatwoot en el frontend → `CHATWOOT_FRONTEND_URL` (desde `.env`)
- `postgres_host` default → `"postgres"` en lugar de `"ruki-kanban-postgres"`

### Licencia

MIT — misma licencia que Chatwoot, maximizando compatibilidad y adopción.

### Documentación open source

Se crearon los archivos estándar para un proyecto open source con contribuciones:

- `README.md` — descripción, arquitectura, quick start, endpoints
- `CONTRIBUTING.md` — setup, convenciones, proceso de PR
- `LICENSE` — MIT
- `SECURITY.md` — política de reporte de vulnerabilidades
- `CODE_OF_CONDUCT.md` — Contributor Covenant 2.1
- `CHANGELOG.md` — keep a changelog

### Conservación de ADRs históricos

Los ADRs (001–016) y sesiones de desarrollo se conservan con referencias
genéricas ("la empresa", "example.com") en lugar de eliminarlos. Proveen
contexto valioso sobre las decisiones arquitectónicas del proyecto.

## Consecuencias

### Positivas

- El proyecto puede recibir contribuciones externas.
- La identidad del proyecto es autónoma, sin dependencia de la empresa original.
- La documentación sigue estándares open source reconocidos.
- La configuración es portable (sin valores hardcodeados de la infraestructura anterior).

### Negativas

- Los pipelines CI/CD de la organización original (`I-Labs-Chile`) dejan de
  funcionar; deben configurarse bajo `CrisAlva1414`.
- El registro GHCR anterior (`ghcr.io/i-labs-chile/...`) queda obsoleto.

### Riesgos

- Si algún archivo contiene referencias no detectadas a la empresa original,
  deberá limpiarse en un follow-up.
- Las URLs de documentación histórica apuntan a `example.com` como placeholder;
  quien despliegue el proyecto debe reemplazarlas con sus URLs reales.

## Alternativas consideradas

| Opción | Pros | Contras | ¿Por qué no? |
|--------|------|---------|--------------|
| Borrar todos los ADRs y sesiones | Repo más limpio | Pierde historial arquitectónico valioso | La historia de decisiones es útil para nuevos contribuyentes |
| Dejar referencias originales intactas | Menos trabajo | El proyecto sigue atado a la empresa | Rompe el principio de desvinculación |
| Crear repo desde cero | Sin riesgo de leaks | Pierde todo el historial de git y documentación | El valor del proyecto está en su historial y decisiones documentadas |

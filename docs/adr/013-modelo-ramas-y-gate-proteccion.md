# ADR-013 — Modelo de ramas y gate de protección

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-07-17 |
| **Proyecto** | kanban.ruki-bot.com |
| **Decidido por** | Sesión 008 |

---

## Contexto

El proyecto está en producción con deploy manual vía Arcane. No hay branch protection, no hay testing en CI, y los cambios se hacen directamente en `main`. Con la aplicación sirviendo a usuarios reales, necesitamos un modelo que:

1. Proteja `main` de merges accidentales
2. Permita iterar sin riesgo para producción
3. mantenga el flujo simple para un equipo de 1 persona

## Decisión

### Modelo main/develop

| Rama | Propósito | Protección |
|------|-----------|------------|
| `main` | Producción. Solo se actualiza vía PR desde `develop` | Branch protection: required status check (`test`), 1 approval mínimo |
| `develop` | Staging/integración. Base de trabajo diaria | Sin protección (se trabaja directo) |
| `feat/<nombre>` | Features grandes que requieren aislamiento | Se crea desde `develop`, PR a `develop` cuando está listo |

### Flujo diario

```
1. Trabajar en develop directamente (cambios pequeños)
2. Push a develop → tests pasan → build :develop → Arcane auto-deploya staging
3. Probar manualmente en devkanban.ruki-bot.com
4. Para producción: PR develop → main → tests pasan → approve manual → merge
5. Arcane auto-deploya a producción
```

### Para features grandes

```
1. git checkout -b feat/<nombre> develop
2. Desarrollar, commitear
3. PR feat/<nombre> → develop → tests → merge
4. Staging se actualiza automáticamente
5. Cuando está validado → PR develop → main
```

### Gate de producción

El merge a `main` solo se completa si el check de `test.yml` está en verde. Esto se implementa via branch protection rule en GitHub:

```bash
gh api repos/{owner}/{repo}/branches/main/protection \
  --method PUT \
  --input branch-protection.json
```

## Consecuencias

- **Positivas:** `main` siempre está deployable, los bugs se detectan en staging antes de producción
- **Negativas:** Un paso extra para llegar a producción (PR + approval)
- **Riesgos:** Para un equipo de 1 persona, el approval manual es un gate que puede ser ignorado en urgencias (con `enforce_admins: false`)

## Alternativas consideradas

| Opción | Pros | Contras | ¿Por qué no? |
|--------|------|---------|---------------|
| Trabajar directo en `main` | Simple | Sin gate de calidad, deploy directo a prod | Modelo actual, insuficiente para producción |
| Gitflow completo (hotfix, release) | Estructurado | Complejidad innecesaria para 1 persona | Overhead sin beneficio real |
| Trunk-based development | Extremadamente simple | Sin staging, todo llega a prod junto | No hay QA intermedio |
| Solo feature branches | Aislamiento | Sin rama de integración | Los cambios pequeños son engorrosos |

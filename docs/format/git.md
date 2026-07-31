# Convenciones de Git

## Commits

Formato **Conventional Commits**:

```
<tipo>(<ámbito opcional>): <descripción en presente>

[body opcional]
```

Tipos:
- `feat:` — nueva funcionalidad
- `fix:` — corrección de bug
- `docs:` — cambios en documentación
- `style:` — formato, lint, whitespace (sin cambio lógico)
- `refactor:` — refactor sin cambio funcional
- `perf:` — mejora de rendimiento
- `test:` — agregar o corregir tests
- `chore:` — tooling, CI, config

Reglas:
- Descripción en **imperativo presente** ("add endpoint", no "added" ni "adds")
- Sin punto final en la descripción
- Usar body solo si el commit requiere explicación del "por qué"
- Sin emojis en el mensaje

## Ramas

| Rama | Propósito | Protección |
|------|-----------|------------|
| `main` | Producción. Solo se actualiza vía PR desde `develop` | Branch protection: required check `test`, 1 approval |
| `develop` | Staging/integración. Base de trabajo diaria | Sin protección |
| `feat/<nombre>` | Features grandes que requieren aislamiento | Se crea desde `develop`, PR a `develop` |
| `fix/<nombre>` | Correcciones puntuales | Se crea desde `develop`, PR a `develop` |
| `docs/<nombre>` | Cambios en documentación | Se crea desde `develop`, PR a `develop` |

## Flujo de trabajo

### Cambios pequeños (directo en develop)
```
1. git checkout develop
2. Trabajar, commitear
3. git push origin develop
4. Tests corren → build :develop → Arcane auto-deploya staging
5. Probar en devkanban.example.com
6. Cuando esté validado → PR develop → main → approve → merge → producción
```

### Features grandes
```
1. git checkout -b feat/<nombre> develop
2. Desarrollar, commitear
3. PR feat/<nombre> → develop → tests → merge
4. Staging se actualiza automáticamente
5. Cuando esté validado → PR develop → main
```

## PRs

- Título del PR = mensaje de commit principal
- Incluir referencias a ADRs o issues si aplica
- PRs a `main` requieren: check `test` verde + 1 approval mínimo
- PRs a `develop` no tienen protección (se mergean directamente)

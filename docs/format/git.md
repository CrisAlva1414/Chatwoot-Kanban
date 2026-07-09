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

- `main` — lista para producción
- `feat/<nombre>` — funcionalidades nuevas
- `fix/<nombre>` — correcciones
- `docs/<nombre>` — documentación

## PRs

- Título del PR = mensaje de commit principal
- Incluir referencias a ADRs o issues si aplica

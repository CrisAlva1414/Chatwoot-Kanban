# Convenciones de Python

## Linting

El proyecto usa **Ruff** con las siguientes reglas activadas (ver `ruff.toml`
y `pyproject.toml` en la raíz):

- `E`, `F` — errores estándar y pycodestyle
- `I` — orden de imports (isort)
- `N` — naming convention
- `UP` — pyupgrade (modernizar sintaxis)
- `B` — bugbear (errores comunes)
- `SIM` — simplificaciones de código
- `ARG` — argumentos no usados
- `RUF100` — noqa innecesarios

Se ejecuta con:

```bash
ruff check . && ruff format --check .
```

## Formato

- Línea máxima: **88 caracteres** (default de Ruff)
- Identación: 4 espacios
- Sin trailing whitespace
- Una línea en blanco al final del archivo

## Tipado

- Todas las funciones públicas deben tener type hints completos (args + return)
- Usar `| None` en vez de `Optional[T]`
- Preferir `Sequence` / `Mapping` sobre `List` / `Dict` en interfaces públicas
- Los `self` y `cls` no llevan type hint

## Imports

Orden: primero stdlib, luego terceros, luego locales. Separados por una
línea en blanco. Ruff los ordena automáticamente.

```python
import asyncio
from collections.abc import Sequence

import httpx

from app.config import settings
```

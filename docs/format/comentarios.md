# Convenciones de comentarios

## Principio general

El código debe ser autoexplicativo. Los comentarios existen solo cuando el
código no puede expresar el "por qué".

## Docstrings

Solo en **módulos públicos** y **funciones públicas** cuando su propósito no
sea obvio. Estilo Google:

```python
"""Fetch conversations filtered by custom attribute.

Args:
    attribute_key: The custom attribute key to filter by.
    value: The value to match.

Returns:
    Raw JSON response from Chatwoot API.
"""
```

Reglas:
- Sin docstring en métodos privados (`_`), a menos que tengan lógica
  no trivial.
- Sin docstring en tests (los nombres descriptivos bastan).
- Una línea si alcanza: `"""Return the user's full name."""`.

## Comentarios inline

Solo se permiten para explicar un **"por qué" no obvio**:

```python
# Chatwoot rechaza conexiones sin este header específico
headers["X-Special"] = "value"
```

No usar comentarios para:
- Describir *qué* hace el código (se lee solo)
- Separar secciones ("# ── Init ──")
- Código comentado (se borra)

"""
Endpoints de la Etapa 1 -- exploración read-only.

El objetivo de estos endpoints NO es ser la API final del Kanban.
Es dejarnos ver, contra el Chatwoot real, el shape exacto de:
  - las definiciones de custom attributes que ya configuraste
  - una respuesta real de /conversations/filter

Con eso confirmamos los Pydantic schemas antes de construir el Kanban.
"""

from fastapi import APIRouter, HTTPException

from app.chatwoot_client import chatwoot_client

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/custom-attribute-definitions")
async def custom_attribute_definitions():
    """
    Trae tal cual la respuesta de Chatwoot. Úsalo primero para confirmar
    que 'tarea_estado' (y los attribute_key de pipeline) existen
    y ver su 'attribute_key' exacto -- Chatwoot es case-sensitive aquí.
    """
    try:
        return await chatwoot_client.get_custom_attribute_definitions()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/conversations/filter")
async def filter_conversations(attribute_key: str, value: str):
    """
    Ejemplo de uso:
      POST /debug/conversations/filter?attribute_key=tarea_estado&value=tarea_activa

    Devuelve el JSON crudo de Chatwoot -- por ahora sin parsear a un
    schema propio, justamente para inspeccionar el shape real primero.
    """
    payload = {
        "payload": [
            {
                "attribute_key": attribute_key,
                "filter_operator": "equal_to",
                "values": [value],
                "query_operator": None,
            }
        ]
    }
    try:
        return await chatwoot_client.filter_conversations(payload)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

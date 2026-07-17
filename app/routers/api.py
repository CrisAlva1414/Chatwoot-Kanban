from fastapi import APIRouter, HTTPException

from app.chatwoot_client import chatwoot_client
from app.schemas.chatwoot import UpdateCustomAttributesRequest

router = APIRouter(prefix="/api/conversations", tags=["api"])


@router.post("/{conversation_id}/custom-attributes")
async def update_custom_attributes(
    conversation_id: int, body: UpdateCustomAttributesRequest
):
    try:
        return await chatwoot_client.safe_update_custom_attributes(
            conversation_id, body.custom_attributes
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

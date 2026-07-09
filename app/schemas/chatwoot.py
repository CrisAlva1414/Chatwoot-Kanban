from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CustomAttributeDefinition(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    attribute_display_name: str
    attribute_display_type: str
    attribute_description: str | None = None
    attribute_key: str
    attribute_values: list[str] = []
    attribute_model: str
    default_value: str | None = None
    created_at: datetime
    updated_at: datetime


class UpdateCustomAttributesRequest(BaseModel):
    custom_attributes: dict


class UpdateCustomAttributesResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | None = None
    custom_attributes: dict = {}


class WebhookEvent(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    event: str | None = None
    account_id: int | None = None
    conversation: dict | None = None
    changed_attributes: list | None = None

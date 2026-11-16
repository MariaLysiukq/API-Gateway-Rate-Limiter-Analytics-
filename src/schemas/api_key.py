import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class APIKeyCreate(BaseModel):
    email: str = Field(
        ...,
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        description="Owner's email. The user is created if it does not exist yet.",
    )
    name: Optional[str] = Field(None, max_length=100, description="Label for the key")
    rate_limit: int = Field(60, ge=1, le=100_000, description="Allowed requests per minute")


class APIKeyOut(BaseModel):
    id: uuid.UUID
    name: Optional[str]
    rate_limit: int
    is_active: bool
    user_email: str
    created_at: datetime


class APIKeyCreated(APIKeyOut):
    api_key: str = Field(..., description="The raw key. It is shown only once and never stored.")

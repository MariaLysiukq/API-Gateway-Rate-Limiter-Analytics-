import secrets
import uuid
from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status

from src.api.dependencies import get_api_key_repository, get_user_repository
from src.core.config import settings
from src.db.models import APIKey
from src.repositories.api_key import APIKeyRepository
from src.repositories.user import UserRepository
from src.schemas.api_key import APIKeyCreate, APIKeyCreated, APIKeyOut
from src.services.auth import AuthService


async def verify_admin_token(
    x_admin_token: str = Header(..., description="Admin token (ADMIN_TOKEN setting)"),
) -> None:
    if not settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API is disabled. Set ADMIN_TOKEN to enable it.",
        )
    if not secrets.compare_digest(x_admin_token, settings.ADMIN_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
        )


router = APIRouter(prefix="/admin", dependencies=[Depends(verify_admin_token)])


def _to_out(api_key: APIKey) -> APIKeyOut:
    return APIKeyOut(
        id=api_key.id,
        name=api_key.name,
        rate_limit=api_key.rate_limit,
        is_active=api_key.is_active,
        user_email=api_key.user.email,
        created_at=api_key.created_at,
    )


@router.post(
    "/keys",
    response_model=APIKeyCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Create an API key (the raw key is returned only once)",
)
async def create_api_key(
    payload: APIKeyCreate,
    user_repo: UserRepository = Depends(get_user_repository),
    api_key_repo: APIKeyRepository = Depends(get_api_key_repository),
) -> APIKeyCreated:
    user = await user_repo.get_or_create(payload.email)

    raw_key = f"gw_{secrets.token_urlsafe(32)}"
    api_key = await api_key_repo.create(
        key_hash=AuthService.hash_key(raw_key),
        name=payload.name,
        rate_limit=payload.rate_limit,
        user_id=user.id,
    )

    return APIKeyCreated(
        id=api_key.id,
        name=api_key.name,
        rate_limit=api_key.rate_limit,
        is_active=api_key.is_active,
        user_email=user.email,
        created_at=api_key.created_at,
        api_key=raw_key,
    )


@router.get("/keys", response_model=List[APIKeyOut], summary="List API keys")
async def list_api_keys(
    api_key_repo: APIKeyRepository = Depends(get_api_key_repository),
) -> List[APIKeyOut]:
    return [_to_out(key) for key in await api_key_repo.list_all()]


@router.delete(
    "/keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke an API key",
)
async def revoke_api_key(
    key_id: uuid.UUID,
    api_key_repo: APIKeyRepository = Depends(get_api_key_repository),
) -> Response:
    api_key = await api_key_repo.get_with_user(key_id)
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    await api_key_repo.deactivate(api_key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

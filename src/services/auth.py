import hashlib
from fastapi import Header, HTTPException, status, Depends
from src.repositories.api_key import APIKeyRepository
from src.api.dependencies import get_api_key_repository
from src.db.models import APIKey


class AuthService:

    @staticmethod
    def hash_key(raw_key: str) -> str:
        """Cache raw API-key (SHA-256)."""
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


async def verify_api_key(
    x_api_key: str = Header(..., description="API Key for client identification"),
    api_key_repo: APIKeyRepository = Depends(get_api_key_repository),
) -> APIKey:
    hashed_key = AuthService.hash_key(x_api_key)
    key_obj = await api_key_repo.get_active_key_by_hash(hashed_key)

    if not key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API Key",
        )

    return key_obj

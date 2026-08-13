from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db_session
from src.repositories.api_key import APIKeyRepository


async def get_api_key_repository(
    db: AsyncSession = Depends(get_db_session),
) -> APIKeyRepository:
    """Dependency for getting APIKeyRepository."""
    return APIKeyRepository(db)

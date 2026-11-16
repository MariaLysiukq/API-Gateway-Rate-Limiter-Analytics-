from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db_session
from src.repositories.api_key import APIKeyRepository
from src.repositories.user import UserRepository


async def get_api_key_repository(
    db: AsyncSession = Depends(get_db_session),
) -> APIKeyRepository:
    """Dependency for getting APIKeyRepository."""
    return APIKeyRepository(db)


async def get_user_repository(
    db: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    """Dependency for getting UserRepository."""
    return UserRepository(db)

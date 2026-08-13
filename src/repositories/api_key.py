from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import APIKey
from src.repositories.base import BaseRepository


class APIKeyRepository(BaseRepository[APIKey]):
    """Repository for interaction with API keys"""

    def __init__(self, db_session: AsyncSession):
        super().__init__(APIKey, db_session)

    async def get_active_key_by_hash(self, key_hash: str) -> Optional[APIKey]:
        """Get sctive API-key with user data from cache."""
        query = (
            select(APIKey)
            .options(selectinload(APIKey.user))
            .where(APIKey.key_hash == key_hash, APIKey.is_active.is_(True))
        )
        result = await self.db.execute(query)
        return result.scalars().first()

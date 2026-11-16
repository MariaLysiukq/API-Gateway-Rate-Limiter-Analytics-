from typing import Any, List, Optional
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

    async def list_all(self) -> List[APIKey]:
        """List all API keys with their owners, newest first."""
        query = (
            select(APIKey)
            .options(selectinload(APIKey.user))
            .order_by(APIKey.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_with_user(self, key_id: Any) -> Optional[APIKey]:
        query = select(APIKey).options(selectinload(APIKey.user)).where(APIKey.id == key_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def deactivate(self, api_key: APIKey) -> APIKey:
        """Revoke a key. Revoked keys are rejected by the gateway immediately."""
        api_key.is_active = False
        await self.db.commit()
        await self.db.refresh(api_key)
        return api_key

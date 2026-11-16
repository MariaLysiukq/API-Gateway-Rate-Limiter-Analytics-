from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for interaction with users"""

    def __init__(self, db_session: AsyncSession):
        super().__init__(User, db_session)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_or_create(self, email: str) -> User:
        user = await self.get_by_email(email)
        if user is None:
            user = await self.create(email=email)
        return user

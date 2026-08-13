from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository for base CRUD operation."""

    def __init__(self, model: Type[ModelType], db_session: AsyncSession):
        self.model = model
        self.db = db_session

    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """Getting a record by primary key."""
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()

    async def create(self, **kwargs) -> ModelType:
        """Creating the new key."""
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

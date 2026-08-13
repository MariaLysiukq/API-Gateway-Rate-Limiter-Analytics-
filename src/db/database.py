from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.core.config import settings

# SQLAlchemy
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

#Async Session
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Базовий клас для всіх ORM моделей."""
    pass


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для отримання асинхронної сесії БД у FastAPI."""
    async with AsyncSessionLocal() as session:
        yield session

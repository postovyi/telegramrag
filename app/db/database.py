from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(settings.db.database_url)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)



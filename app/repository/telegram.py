from .base import SQLAlchemyRepository
from app.models.telegram import TelegramChannel, TelegramPost, TelegramPostMedia
from sqlalchemy import select
from app.core.config import settings

class TelegramChannelRepository(SQLAlchemyRepository[TelegramChannel]):
    pass

class TelegramPostRepository(SQLAlchemyRepository[TelegramPost]):
    async def find_by_embedding(self, embedding: list[float]) -> list[TelegramPost]:
        statement = select(TelegramPost).order_by(1 - TelegramPost.embedding.cosine_distance(embedding)).limit(settings.rag.top_k)
        return await self.execute(statement=statement, action=lambda result: result.scalars().all())

class TelegramPostMediaRepository(SQLAlchemyRepository[TelegramPostMedia]):
    async def find_by_embedding(self, embedding: list[float]) -> list[TelegramPostMedia]:
        statement = select(TelegramPostMedia).order_by(1 - TelegramPostMedia.embedding.cosine_distance(embedding)).limit(settings.rag.top_k)
        return await self.execute(statement=statement, action=lambda result: result.scalars().all())
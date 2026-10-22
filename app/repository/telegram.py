from uuid import UUID

from sqlalchemy import select

from app.core.config import settings
from app.models.telegram import TelegramChannel, TelegramPost, TelegramPostMedia

from .base import SQLAlchemyRepository


class TelegramChannelRepository(SQLAlchemyRepository[TelegramChannel]):
    model = TelegramChannel


class TelegramPostRepository(SQLAlchemyRepository[TelegramPost]):
    model = TelegramPost

    async def find_by_embedding(
        self, embedding: list[float], limit: int | None = None
    ) -> list[tuple[TelegramPost, float]]:
        distance = TelegramPost.embedding.cosine_distance(embedding).label('distance')
        statement = (
            select(TelegramPost, distance)
            .where(TelegramPost.embedding.is_not(None))
            .order_by(distance)
            .limit(settings.rag.top_k if limit is None else limit)
        )
        return await self.execute(statement=statement, action=lambda result: [(row[0], row[1]) for row in result.all()])


class TelegramPostMediaRepository(SQLAlchemyRepository[TelegramPostMedia]):
    model = TelegramPostMedia

    async def find_by_embedding(self, embedding: list[float]) -> list[tuple[TelegramPostMedia, float]]:
        """Closest images within `media_max_distance`, at most `media_top_k` (text-to-image distances run higher)."""
        distance = TelegramPostMedia.embedding.cosine_distance(embedding).label('distance')
        statement = (
            select(TelegramPostMedia, distance)
            .where(distance <= settings.rag.media_max_distance)
            .order_by(distance)
            .limit(settings.rag.media_top_k)
        )
        return await self.execute(statement=statement, action=lambda result: [(row[0], row[1]) for row in result.all()])

    async def get_data(self, media_id: UUID) -> tuple[bytes, str] | None:
        statement = select(TelegramPostMedia.data, TelegramPostMedia.mime_type).where(TelegramPostMedia.id == media_id)
        return await self.execute(
            statement=statement,
            action=lambda result: (lambda row: (row.data, row.mime_type) if row else None)(result.first()),
        )

import logging
from typing import TypeVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.telegram import TelegramChannel, TelegramPost, TelegramPostMedia
from app.repository import TelegramPostMediaRepository, TelegramPostRepository
from app.schemas import RetrievedItemSchema

logger = logging.getLogger(__name__)

ModelT = TypeVar('ModelT')


class RAGStrategy:
    def __init__(self, post_repository: TelegramPostRepository, media_repository: TelegramPostMediaRepository) -> None:
        self.post_repository = post_repository
        self.media_repository = media_repository

    async def _search(self, embedding: list[float]) -> list[RetrievedItemSchema]:
        """Search post texts and post images with one query vector.

        Text-to-image distances run systematically higher than text-to-text ones, so a plain distance merge would never
        surface an image. Images get reserved slots (``media_top_k``, within ``media_max_distance``); posts fill the
        rest of ``top_k``. The combined list is ordered by distance.
        """
        media_hits = (await self.media_repository.find_by_embedding(embedding))[: settings.rag.top_k]
        post_hits = await self.post_repository.find_by_embedding(embedding, limit=settings.rag.top_k - len(media_hits))

        candidates: list[tuple[float, TelegramPost | TelegramPostMedia]] = [
            *((distance, post) for post, distance in post_hits),
            *((distance, media) for media, distance in media_hits),
        ]
        candidates.sort(key=lambda candidate: candidate[0])

        session = self.post_repository.session
        posts: dict[UUID, TelegramPost] = {}
        channels: dict[UUID, TelegramChannel] = {}
        items: list[RetrievedItemSchema] = []
        for distance, hit in candidates:
            post = (
                hit
                if isinstance(hit, TelegramPost)
                else await self._get_cached(session, posts, TelegramPost, hit.post_id)
            )
            channel = await self._get_cached(session, channels, TelegramChannel, post.channel_id)
            is_image = isinstance(hit, TelegramPostMedia)
            items.append(
                RetrievedItemSchema(
                    kind='image' if is_image else 'post',
                    post_id=post.id,
                    media_id=hit.id if is_image else None,
                    media_url=f'/telegram/media/{hit.id}' if is_image else None,
                    content=post.content,
                    posted_at=post.posted_at,
                    channel_url=channel.url,
                    url=post.url,
                    distance=distance,
                )
            )

        logger.debug('retrieved top-k: %s', [(item.kind, round(item.distance, 4)) for item in items])
        return items

    @staticmethod
    async def _get_cached(session: AsyncSession, cache: dict[UUID, ModelT], model: type[ModelT], key: UUID) -> ModelT:
        if key not in cache:
            cache[key] = await session.get(model, key)
        return cache[key]

    async def retrieve(self, query: str, media: bytes | None = None) -> list[RetrievedItemSchema]:
        raise NotImplementedError

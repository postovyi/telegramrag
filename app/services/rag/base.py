import numpy as np

from app.core.config import settings
from app.models.telegram import TelegramChannel, TelegramPost
from app.repository import TelegramPostMediaRepository, TelegramPostRepository
from app.schemas import TelegramPostSchema
from app.services.rag.embeddings import EmbeddingService


class RAGStrategy:
    def __init__(
        self, post_repository: TelegramPostRepository, post_media_repository: TelegramPostMediaRepository
    ) -> None:
        self.post_repository = post_repository
        self.post_media_repository = post_media_repository

    async def _build_query_embedding(self, text_embedding: np.ndarray, media: bytes | None) -> np.ndarray:
        if media:
            embedding_media = await EmbeddingService.embed_image(media)
        else:
            embedding_media = np.zeros(settings.rag.embedding_n_dim)

        return text_embedding + embedding_media

    async def _to_post_schemas(self, posts: list[TelegramPost]) -> list[TelegramPostSchema]:
        schemas: list[TelegramPostSchema] = []
        for post in posts:
            channel = await self.post_repository.session.get(TelegramChannel, post.channel_id)
            schemas.append(
                TelegramPostSchema(
                    id=post.id,
                    content=post.content,
                    posted_at=post.posted_at,
                    channel_url=channel.url,
                    url=post.url,
                )
            )
        return schemas

    async def retrieve(self, query: str, media: bytes | None = None) -> list[TelegramPostSchema]:
        raise NotImplementedError

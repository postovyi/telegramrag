from app.schemas import TelegramPostSchema
from app.services.rag.base import RAGStrategy
from app.services.rag.embeddings import EmbeddingService


class NaiveRAGStrategy(RAGStrategy):
    async def retrieve(self, query: str, media: bytes | None = None) -> list[TelegramPostSchema]:
        embedding_text = await EmbeddingService.embed_text(query)

        posts = await self.post_repository.find_by_embedding(embedding_text.tolist())
        return await self._to_post_schemas(posts)

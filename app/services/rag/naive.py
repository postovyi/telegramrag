from app.schemas import TelegramPostSchema
from app.services.rag.base import RAGStrategy
from app.services.rag.embeddings import EmbeddingService


class NaiveRAGStrategy(RAGStrategy):
    async def retrieve(self, query: str, media: bytes | None = None) -> list[TelegramPostSchema]:
        embedding_text = await EmbeddingService.embed_text(query)
        post_embedding = await self._build_query_embedding(embedding_text, media)

        posts = await self.post_repository.find_by_embedding(post_embedding.tolist())
        return await self._to_post_schemas(posts)

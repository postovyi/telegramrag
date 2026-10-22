from app.schemas import RetrievedItemSchema
from app.services.rag.base import RAGStrategy
from app.services.rag.embeddings import EmbeddingService


class NaiveRAGStrategy(RAGStrategy):
    async def retrieve(self, query: str, media: bytes | None = None) -> list[RetrievedItemSchema]:
        embedding_text = await EmbeddingService.embed_text(query)

        return await self._search(embedding_text.tolist())

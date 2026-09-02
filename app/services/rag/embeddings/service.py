import numpy as np

from app.core.config import settings
from app.services.rag.embeddings.base import EmbeddingProvider
from app.services.rag.embeddings.google_provider import GoogleEmbeddingProvider
from app.services.rag.embeddings.openai_provider import OpenAIEmbeddingProvider
from app.services.rag.embeddings.sentence_transformers_provider import SentenceTransformerEmbeddingProvider


def _build_provider() -> EmbeddingProvider:
    provider = settings.rag.embedding_provider

    if provider == 'sentence_transformers':
        return SentenceTransformerEmbeddingProvider()

    if provider == 'openai':
        if not settings.rag.embedding_api_key:
            raise ValueError('EMBEDDING_API_KEY is required when EMBEDDING_PROVIDER=openai')
        return OpenAIEmbeddingProvider()

    if provider == 'google':
        if not settings.rag.embedding_api_key:
            raise ValueError('EMBEDDING_API_KEY is required when EMBEDDING_PROVIDER=google')
        return GoogleEmbeddingProvider()

    raise ValueError(f'Unsupported EMBEDDING_PROVIDER: {provider!r}')


class EmbeddingService:
    PROVIDER = _build_provider()

    @classmethod
    async def embed_text(cls, text: str) -> np.ndarray:
        return await cls.PROVIDER.embed_text(text)

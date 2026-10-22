import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.services.rag.embeddings.base import ImageEmbeddingNotSupportedError


class SentenceTransformerEmbeddingProvider:
    def __init__(self) -> None:
        self.embedding_model = SentenceTransformer(settings.rag.embedding_model)

    async def embed_text(self, text: str) -> np.ndarray:
        return self.embedding_model.encode(text, convert_to_numpy=True)

    async def embed_image(self, data: bytes, mime_type: str) -> np.ndarray:
        raise ImageEmbeddingNotSupportedError('Image embedding is not supported by the sentence_transformers provider')

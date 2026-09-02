import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings


class SentenceTransformerEmbeddingProvider:
    EMBEDDING_MODEL = SentenceTransformer(settings.rag.embedding_model)

    async def embed_text(self, text: str) -> np.ndarray:
        return self.EMBEDDING_MODEL.encode(text, convert_to_numpy=True)

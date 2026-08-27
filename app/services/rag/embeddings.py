import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings


class EmbeddingService:
    EMBEDDING_MODEL = SentenceTransformer(settings.rag.embedding_model)

    @classmethod
    async def embed_text(cls, text: str) -> np.ndarray:
        return cls.EMBEDDING_MODEL.encode(text, convert_to_numpy=True)

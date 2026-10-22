import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings


class SentenceTransformerEmbeddingProvider:
    def __init__(self) -> None:
        self.embedding_model = SentenceTransformer(settings.rag.embedding_model)

    async def embed_text(self, text: str) -> np.ndarray:
        return self.embedding_model.encode(text, convert_to_numpy=True)

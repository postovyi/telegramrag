from typing import Any

from PIL import Image
from sentence_transformers import SentenceTransformer
import numpy as np

from app.core.config import settings


class EmbeddingService:
    EMBEDDING_MODEL = SentenceTransformer(settings.rag.embedding_model)

    @classmethod
    async def embed_text(cls, text: str) -> np.ndarray:
        return cls.EMBEDDING_MODEL.encode(text)

    @classmethod
    async def embed_image(cls, image: Any) -> np.ndarray:
        img = Image.open(image)
        return cls.EMBEDDING_MODEL.encode(img)
from io import BytesIO
from typing import Any

import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer

from app.core.config import settings


class EmbeddingService:
    EMBEDDING_MODEL = SentenceTransformer(settings.rag.embedding_model)

    @classmethod
    async def embed_text(cls, text: str) -> np.ndarray:
        return cls.EMBEDDING_MODEL.encode(text, convert_to_numpy=True)

    @classmethod
    async def embed_image(cls, image: Any) -> np.ndarray:
        img = Image.open(BytesIO(image) if isinstance(image, bytes) else image)
        return cls.EMBEDDING_MODEL.encode(img, convert_to_numpy=True)

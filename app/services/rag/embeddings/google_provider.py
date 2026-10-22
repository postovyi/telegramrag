import numpy as np
from google import genai

from app.core.config import settings
from app.services.rag.embeddings.base import ImageEmbeddingNotSupportedError


class GoogleEmbeddingProvider:
    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.rag.embedding_api_key)

    async def embed_text(self, text: str) -> np.ndarray:
        response = await self.client.aio.models.embed_content(model=settings.rag.embedding_model, contents=text)
        return np.array(response.embeddings[0].values)

    async def embed_image(self, data: bytes, mime_type: str) -> np.ndarray:
        raise ImageEmbeddingNotSupportedError('Image embedding is not supported by the google provider')

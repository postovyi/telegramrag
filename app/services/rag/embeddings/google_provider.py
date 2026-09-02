import numpy as np
from google import genai

from app.core.config import settings


class GoogleEmbeddingProvider:
    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.rag.embedding_api_key)

    async def embed_text(self, text: str) -> np.ndarray:
        response = await self.client.aio.models.embed_content(model=settings.rag.embedding_model, contents=text)
        return np.array(response.embeddings[0].values)

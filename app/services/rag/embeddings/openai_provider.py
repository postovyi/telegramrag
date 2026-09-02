import numpy as np
from openai import AsyncOpenAI

from app.core.config import settings


class OpenAIEmbeddingProvider:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.rag.embedding_api_key)

    async def embed_text(self, text: str) -> np.ndarray:
        response = await self.client.embeddings.create(model=settings.rag.embedding_model, input=text)
        return np.array(response.data[0].embedding)

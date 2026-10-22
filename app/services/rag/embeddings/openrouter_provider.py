import base64

import numpy as np
from openai import AsyncOpenAI

from app.core.config import settings


class OpenRouterEmbeddingProvider:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.rag.embedding_api_key, base_url='https://openrouter.ai/api/v1')

    async def embed_text(self, text: str) -> np.ndarray:
        response = await self.client.embeddings.create(
            model=settings.rag.embedding_model,
            input=text,
            dimensions=settings.rag.embedding_n_dim,
        )
        return np.array(response.data[0].embedding)

    async def embed_image(self, data: bytes, mime_type: str) -> np.ndarray:
        data_url = f'data:{mime_type};base64,{base64.b64encode(data).decode()}'
        response = await self.client.embeddings.create(
            model=settings.rag.embedding_model,
            input=[{'content': [{'type': 'image_url', 'image_url': {'url': data_url}}]}],
            dimensions=settings.rag.embedding_n_dim,
            encoding_format='float',
        )
        return np.array(response.data[0].embedding)

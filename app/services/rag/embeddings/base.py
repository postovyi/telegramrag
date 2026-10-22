from typing import Protocol

import numpy as np


class ImageEmbeddingNotSupportedError(NotImplementedError):
    """Raised when the configured embedding provider cannot embed images."""


class EmbeddingProvider(Protocol):
    async def embed_text(self, text: str) -> np.ndarray: ...

    async def embed_image(self, data: bytes, mime_type: str) -> np.ndarray: ...

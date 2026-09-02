from typing import Protocol

import numpy as np


class EmbeddingProvider(Protocol):
    async def embed_text(self, text: str) -> np.ndarray: ...

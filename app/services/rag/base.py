from typing import Protocol

from app.repository import TelegramPostMediaRepository, TelegramPostRepository

class RAGStrategy(Protocol):

    def __init__(self, post_repository: TelegramPostRepository, post_media_repository: TelegramPostMediaRepository) -> None:
        self.post_repository = post_repository
        self.post_media_repository = post_media_repository
        

    async def retrieve(self, query: str, media: bytes | None = None) -> list[str]:
        ...


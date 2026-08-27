from app.models.telegram import TelegramChannel, TelegramPost
from app.repository import TelegramPostRepository
from app.schemas import TelegramPostSchema


class RAGStrategy:
    def __init__(self, post_repository: TelegramPostRepository) -> None:
        self.post_repository = post_repository

    async def _to_post_schemas(self, posts: list[TelegramPost]) -> list[TelegramPostSchema]:
        schemas: list[TelegramPostSchema] = []
        for post in posts:
            channel = await self.post_repository.session.get(TelegramChannel, post.channel_id)
            schemas.append(
                TelegramPostSchema(
                    id=post.id,
                    content=post.content,
                    posted_at=post.posted_at,
                    channel_url=channel.url,
                    url=post.url,
                )
            )
        return schemas

    async def retrieve(self, query: str, media: bytes | None = None) -> list[TelegramPostSchema]:
        raise NotImplementedError

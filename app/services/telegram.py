from uuid import UUID

from app.models.telegram import TelegramChannel
from app.repository import (
    TelegramChannelRepository,
    TelegramPostMediaRepository,
    TelegramPostRepository,
)
from app.schemas import (
    CreateTelegramChannelSchema,
    CreateTelegramPostSchema,
    PyrogramImportChannelsSchema,
    PyrogramImportPostsSchema,
    RAGInputSchema,
    TelegramChannelSchema,
    TelegramPostInputSchema,
    TelegramPostMediaInputSchema,
    TelegramPostSchema,
)
from app.services.pyrogram import PyrogramService
from app.services.rag.base import RAGStrategy

from .rag import EmbeddingService


class TelegramService:
    def __init__(
        self,
        channel_repository: TelegramChannelRepository,
        post_repository: TelegramPostRepository,
        post_media_repository: TelegramPostMediaRepository,
        pyrogram_service: PyrogramService,
    ) -> None:
        self.channel_repository = channel_repository
        self.post_repository = post_repository
        self.post_media_repository = post_media_repository
        self.pyrogram_service = pyrogram_service

    async def get_channel(self, channel_id: UUID) -> TelegramChannelSchema:
        channel = await self.channel_repository.get_one(id=channel_id)
        return TelegramChannelSchema.model_validate(channel, extra="ignore")

    async def get_post(self, post_id: UUID) -> TelegramPostSchema:
        post = await self.post_repository.get_one(id=post_id)

        return TelegramPostSchema(
            id=post.id,
            content=post.content,
            posted_at=post.posted_at,
            channel_url=post.channel.url,
            url=post.url
        )

    async def get_channels(self) -> list[TelegramChannelSchema]:
        channels = await self.channel_repository.get_all()
        return [TelegramChannelSchema.model_validate(channel, extra="ignore") for channel in channels]


    async def create_channel(self, channel: CreateTelegramChannelSchema) -> TelegramChannelSchema:
        channel = await self.channel_repository.create(channel)
        return TelegramChannelSchema.model_validate(channel, extra="ignore")

    async def create_post(self, post: CreateTelegramPostSchema) -> TelegramPostSchema:
        db_post = await self.post_repository.create(
            TelegramPostInputSchema(
                content=post.content,
                posted_at=post.posted_at,
                channel_id=post.channel_id,
                url=post.url,
                embedding=await EmbeddingService.embed_text(post.content)
            )
        )
        if post.media:
            for media in post.media:
                await self.post_media_repository.create(
                    TelegramPostMediaInputSchema(
                        post_id=db_post.id,
                        embedding=await EmbeddingService.embed_image(media.content)
                    )
                )
        return TelegramPostSchema.model_validate(post, extra="ignore")

    async def _get_or_create_channel(self, channel: CreateTelegramChannelSchema) -> TelegramChannel:
        existing = await self.channel_repository.get_one_or_none(username=channel.username)
        if existing is not None:
            return existing
        return await self.channel_repository.create(
            channel
        )

    async def import_channels(self, data: PyrogramImportChannelsSchema) -> list[TelegramChannelSchema]:
        async with self.pyrogram_service:
            scraped = await self.pyrogram_service.search_channels(data.keywords, limit=data.limit)

        results: list[TelegramChannelSchema] = []
        for channel in scraped:
            db_channel = await self._get_or_create_channel(channel)
            results.append(TelegramChannelSchema.model_validate(db_channel, extra="ignore"))
        return results

    async def import_posts(self, data: PyrogramImportPostsSchema) -> list[TelegramPostSchema]:
        db_channel = await self.channel_repository.get_one(id=data.channel_id)  # raises if not found
        async with self.pyrogram_service:
            scraped = await self.pyrogram_service.fetch_posts(
                db_channel.username, data.start_date, data.end_date, download_media=data.download_media
            )

        stored: list[TelegramPostSchema] = []
        for post in scraped:
            if not post.content:
                continue
            stored.append(await self.create_post(CreateTelegramPostSchema(
                content=post.content,
                posted_at=post.posted_at,
                channel_id=db_channel.id,
                url=post.url,
                media=post.media,
            )))
        return stored


class TelegramRAGService:
    def __init__(self, strategy: RAGStrategy) -> None:
        self.strategy = strategy

    async def retrieve(self, data: RAGInputSchema) -> list[TelegramPostSchema]:
        return await self.strategy.retrieve(data.query, data.media)
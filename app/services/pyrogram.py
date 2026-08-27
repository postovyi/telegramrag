from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from types import TracebackType

from pyrogram import Client, enums
from pyrogram.raw.functions.contacts import Search
from pyrogram.raw.types import Channel as RawChannel
from pyrogram.types import Chat, Message

from app.core.config import settings
from app.schemas import CreateTelegramChannelSchema, ScrapedTelegramPostSchema, TelegramMedia


class PyrogramService:
    """Scrapes Telegram channels and posts through Pyrofork (imported as ``pyrogram``).

    The service is intentionally persistence-free: it returns plain schemas that map
    onto ``TelegramService`` inputs, leaving any database writes to the caller.

    Note:
        ``search_channels`` relies on ``Client.search_chats``, which matches against the
        titles and usernames of chats known to the server. For full-text or global
        discovery, ``search_global``/``search_public_messages_by_tag`` would be needed.
    """

    def __init__(self) -> None:
        self.client = Client(
            name=settings.telegram.session_name,
            api_id=settings.telegram.api_id,
            api_hash=settings.telegram.api_hash,
            session_string=settings.telegram.session_string,
            in_memory=True,
        )

    async def __aenter__(self) -> PyrogramService:
        await self.client.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.client.stop()

    async def search_channels(self, keywords: str, limit: int = 10) -> list[CreateTelegramChannelSchema]:
        """Globally search public Telegram channels whose title or username matches ``keywords``.

        Uses the raw ``contacts.search`` API instead of ``search_global``/``search_chats``,
        which are limited to chats the account is already a member of.
        """
        found = await self.client.invoke(Search(q=keywords, limit=limit))

        channels: list[CreateTelegramChannelSchema] = []
        for chat in found.chats:
            if not isinstance(chat, RawChannel) or not chat.broadcast or not chat.username:
                continue
            channels.append(
                CreateTelegramChannelSchema(
                    name=chat.title,
                    username=chat.username,
                    url=f"https://t.me/{chat.username}",
                )
            )

        return channels

    async def get_channel(self, username: str) -> CreateTelegramChannelSchema:
        """Fetch a single channel's info by username/link."""
        chat = await self.client.get_chat(username)
        return self._to_channel_schema(chat)

    async def fetch_posts(
        self,
        channel: str,
        start_date: datetime,
        end_date: datetime,
        download_media: bool = True,
    ) -> list[ScrapedTelegramPostSchema]:
        """Fetch posts of ``channel`` posted within ``[start_date, end_date]``.

        ``get_chat_history`` yields messages newest-first, so iteration starts at
        ``end_date`` and stops once a message older than ``start_date`` is reached.
        """
        posts: list[ScrapedTelegramPostSchema] = []
        start_date = start_date.astimezone(timezone.utc).replace(tzinfo=None)
        end_date = end_date.astimezone(timezone.utc).replace(tzinfo=None)

        async for message in self.client.get_chat_history(channel, offset_date=end_date):
            if message.date is None:
                continue
            if message.date > end_date:
                continue
            if message.date < start_date:
                break

            posts.append(await self._to_post_schema(message, channel, download_media))

        return posts

    @staticmethod
    def _to_channel_schema(chat: Chat) -> CreateTelegramChannelSchema:
        return CreateTelegramChannelSchema(
            name=chat.title or chat.username,
            username=chat.username,
            url=f"https://t.me/{chat.username}",
        )

    async def _to_post_schema(
        self,
        message: Message,
        channel: str,
        download_media: bool,
    ) -> ScrapedTelegramPostSchema:
        username = self._resolve_username(message, channel)
        media: list[TelegramMedia] = []

        if download_media and message.photo is not None:
            buffer = await self.client.download_media(message, in_memory=True)
            if isinstance(buffer, BytesIO):
                media.append(TelegramMedia(content=buffer.getvalue()))

        return ScrapedTelegramPostSchema(
            content=message.text or message.caption,
            posted_at=message.date,
            channel_username=username,
            url=f"https://t.me/{username}/{message.id}",
            media=media,
        )

    @staticmethod
    def _resolve_username(message: Message, channel: str) -> str:
        if message.chat is not None and message.chat.username:
            return message.chat.username
        return channel.lstrip("@")

from datetime import datetime
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, Text, func
from sqlalchemy.orm import Mapped, deferred, mapped_column, relationship

from app.core.config import settings

from .base import BaseId


class TelegramChannel(BaseId):
    __tablename__ = 'telegram_channel'

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    posts: Mapped[list[TelegramPost]] = relationship(back_populates='channel')


class TelegramPost(BaseId):
    __tablename__ = 'telegram_post'

    content: Mapped[str] = mapped_column(Text, nullable=True)
    posted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    channel_id: Mapped[UUID] = mapped_column(ForeignKey('telegram_channel.id'), nullable=False)
    embedding: Mapped[Vector | None] = mapped_column(Vector(settings.rag.embedding_n_dim), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    channel: Mapped[TelegramChannel] = relationship(back_populates='posts')
    media: Mapped[list[TelegramPostMedia]] = relationship(  # noqa: F821
        back_populates='post', cascade='all, delete-orphan', passive_deletes=True
    )


class TelegramPostMedia(BaseId):
    __tablename__ = 'telegram_post_media'

    post_id: Mapped[UUID] = mapped_column(
        ForeignKey('telegram_post.id', ondelete='CASCADE'), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    data: Mapped[bytes] = deferred(mapped_column(LargeBinary, nullable=False))
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding: Mapped[Vector] = mapped_column(Vector(settings.rag.embedding_n_dim), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    post: Mapped[TelegramPost] = relationship(back_populates='media')

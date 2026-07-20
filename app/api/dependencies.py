from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import async_session_maker
from app.repository import (
    TelegramChannelRepository,
    TelegramPostMediaRepository,
    TelegramPostRepository,
)
from app.services.pyrogram import PyrogramService
from app.services.rag.hyde import HyDEStrategy
from app.services.rag.selfrag import SelfRAGStrategy
from app.services.telegram import TelegramRAGService, TelegramService

# Create a singleton PyrogramService instance to reuse client and session resources
pyrogram_service_instance = PyrogramService()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields a database session wrapped in a transaction context.

    This ensures that all DB operations in an endpoint are committed on successful completion,
    or rolled back if an exception occurs.
    """
    async with async_session_maker() as session, session.begin():
        yield session


def get_pyrogram_service() -> PyrogramService:
    """Dependency to retrieve the PyrogramService instance."""
    return pyrogram_service_instance


def get_telegram_service(
    session: AsyncSession = Depends(get_db),
    pyrogram_service: PyrogramService = Depends(get_pyrogram_service),
) -> TelegramService:
    """Dependency that creates and returns a TelegramService with all required repositories."""
    channel_repo = TelegramChannelRepository(session)
    post_repo = TelegramPostRepository(session)
    post_media_repo = TelegramPostMediaRepository(session)
    return TelegramService(
        channel_repository=channel_repo,
        post_repository=post_repo,
        post_media_repository=post_media_repo,
        pyrogram_service=pyrogram_service,
    )


def get_telegram_rag_service(
    session: AsyncSession = Depends(get_db),
) -> TelegramRAGService:
    """Dependency that creates and returns a TelegramRAGService with the specified strategy."""
    post_repo = TelegramPostRepository(session)
    post_media_repo = TelegramPostMediaRepository(session)
    if settings.rag.rag_strategy == "selfag":
        strategy = SelfRAGStrategy(post_repo, post_media_repo)
    else:
        strategy = HyDEStrategy(post_repo, post_media_repo)
    return TelegramRAGService(strategy)

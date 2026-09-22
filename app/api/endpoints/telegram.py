from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import NoResultFound

from app.api.dependencies import get_telegram_service
from app.schemas import (
    CreateTelegramChannelSchema,
    CreateTelegramPostSchema,
    FetchTelegramChannelsByUsernamesSchema,
    PyrogramImportChannelsSchema,
    PyrogramImportPostsSchema,
    ScrapedTelegramPostSchema,
    TelegramChannelPreviewSchema,
    TelegramChannelSchema,
    TelegramPostSchema,
)
from app.services.telegram import TelegramService

router = APIRouter(prefix='/telegram', tags=['telegram'])


@router.get('/channels', response_model=list[TelegramChannelSchema])
async def list_channels(
    service: TelegramService = Depends(get_telegram_service),
) -> list[TelegramChannelSchema]:
    """Retrieve all stored Telegram channels."""
    return await service.get_channels()


@router.post('/channels', response_model=TelegramChannelSchema, status_code=status.HTTP_201_CREATED)
async def create_channel(
    channel_in: CreateTelegramChannelSchema,
    service: TelegramService = Depends(get_telegram_service),
) -> TelegramChannelSchema:
    """Manually add/create a Telegram channel to the database."""
    return await service.create_channel(channel_in)


@router.get('/channels/by-username', response_model=TelegramChannelSchema)
async def get_channel_by_username(
    username: str,
    service: TelegramService = Depends(get_telegram_service),
) -> TelegramChannelSchema:
    """Fetch a single Telegram channel by username, scraping and storing it if not already in the database."""
    try:
        return await service.get_or_fetch_channel_by_username(username)
    except NoResultFound as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Telegram channel with username {username!r} not found.',
        ) from err


@router.post('/channels/by-usernames', response_model=list[TelegramChannelSchema])
async def get_channels_by_usernames(
    usernames_in: FetchTelegramChannelsByUsernamesSchema,
    service: TelegramService = Depends(get_telegram_service),
) -> list[TelegramChannelSchema]:
    """Fetch multiple Telegram channels by username, best-effort (failing usernames are skipped)."""
    return await service.get_or_fetch_channels_by_usernames(usernames_in.usernames)


@router.get('/channels/search-by-keywords', response_model=list[TelegramChannelPreviewSchema])
async def search_channels_by_keywords(
    keywords: str,
    service: TelegramService = Depends(get_telegram_service),
) -> list[TelegramChannelPreviewSchema]:
    """Search public Telegram channels by keyword, live, without persisting to the database.

    Returns name/username/subscriber count, sorted by subscriber count descending, capped by
    the server-side ``TELEGRAM_CHANNEL_SEARCH_LIMIT`` config value.
    """
    return await service.search_channels_preview(keywords)


@router.get('/channels/{channel_id}', response_model=TelegramChannelSchema)
async def get_channel(
    channel_id: UUID,
    service: TelegramService = Depends(get_telegram_service),
) -> TelegramChannelSchema:
    """Retrieve details of a single Telegram channel by its ID."""
    try:
        return await service.get_channel(channel_id)
    except NoResultFound as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Telegram channel with ID {channel_id} not found.',
        ) from err


@router.get('/posts/by-username', response_model=list[ScrapedTelegramPostSchema])
async def get_posts_by_username(
    username: str,
    start_date: datetime,
    end_date: datetime,
    service: TelegramService = Depends(get_telegram_service),
) -> list[ScrapedTelegramPostSchema]:
    """Scrape a channel's posts within a date range by username, live, without persisting to the database."""
    try:
        return await service.fetch_posts_by_username(username, start_date, end_date)
    except NoResultFound as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Telegram channel with username {username!r} not found.',
        ) from err


@router.get('/posts/{post_id}', response_model=TelegramPostSchema)
async def get_post(
    post_id: UUID,
    service: TelegramService = Depends(get_telegram_service),
) -> TelegramPostSchema:
    """Retrieve details of a single Telegram post by its ID."""
    try:
        return await service.get_post(post_id)
    except NoResultFound as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Telegram post with ID {post_id} not found.',
        ) from err


@router.post('/posts', response_model=TelegramPostSchema, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_in: CreateTelegramPostSchema,
    service: TelegramService = Depends(get_telegram_service),
) -> TelegramPostSchema:
    """Manually add/create a Telegram post to the database, including media embeddings if provided."""
    return await service.create_post(post_in)


@router.post('/import/channels', response_model=list[TelegramChannelSchema], status_code=status.HTTP_201_CREATED)
async def import_channels(
    import_in: PyrogramImportChannelsSchema,
    service: TelegramService = Depends(get_telegram_service),
) -> list[TelegramChannelSchema]:
    """Scrape and import Telegram channels by keywords using Pyrogram."""
    return await service.import_channels(import_in)


@router.post('/import/posts', response_model=list[TelegramPostSchema], status_code=status.HTTP_201_CREATED)
async def import_posts(
    import_in: PyrogramImportPostsSchema,
    service: TelegramService = Depends(get_telegram_service),
) -> list[TelegramPostSchema]:
    """Scrape and import posts of a specific channel within a given date range using Pyrogram."""
    try:
        return await service.import_posts(import_in)
    except NoResultFound as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Source Telegram channel with ID {import_in.channel_id} not found in database.',
        ) from err

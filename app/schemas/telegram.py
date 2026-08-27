from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TelegramMedia(BaseModel):
    content: bytes

class TelegramChannelSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    username: str
    url: str

class TelegramPostSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    content: str | None = None
    posted_at: datetime
    channel_url: str
    url: str

class ScrapedTelegramPostSchema(BaseModel):
    content: str | None = None
    posted_at: datetime
    channel_username: str
    url: str
    media: list[TelegramMedia] = []


class CreateTelegramChannelSchema(BaseModel):
    name: str
    username: str
    url: str

class CreateTelegramPostSchema(BaseModel):
    content: str | None = None
    posted_at: datetime
    channel_id: UUID
    url: str
    media: list[TelegramMedia] | None = None

class TelegramPostInputSchema(CreateTelegramPostSchema):
    embedding: list[float]


class PyrogramImportChannelsSchema(BaseModel):
    keywords: str
    limit: int = 10

class PyrogramImportPostsSchema(BaseModel):
    channel_id: UUID
    start_date: datetime
    end_date: datetime
    download_media: bool = True
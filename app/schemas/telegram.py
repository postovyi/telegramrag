import base64
import binascii
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class TelegramMedia(BaseModel):
    content: bytes
    mime_type: str = 'image/jpeg'

    @field_validator('content', mode='before')
    @classmethod
    def decode_base64_content(cls, value: object) -> object:
        """JSON cannot carry raw bytes: accept a base64 string and decode it (raw bytes pass through)."""
        if isinstance(value, str):
            try:
                return base64.b64decode(value, validate=True)
            except binascii.Error as err:
                raise ValueError('content must be valid base64') from err
        return value


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


class RetrievedItemSchema(BaseModel):
    kind: Literal['post', 'image']
    post_id: UUID
    media_id: UUID | None = None
    media_url: str | None = None
    content: str | None = None
    posted_at: datetime
    channel_url: str
    url: str
    distance: float


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


class TelegramChannelPreviewSchema(BaseModel):
    name: str
    username: str
    subscribers_count: int


class CreateTelegramPostSchema(BaseModel):
    content: str | None = None
    posted_at: datetime
    channel_id: UUID
    url: str
    media: list[TelegramMedia] | None = None


class TelegramPostInputSchema(CreateTelegramPostSchema):
    embedding: list[float] | None = None


class PyrogramImportChannelsSchema(BaseModel):
    keywords: str
    limit: int = 10


class FetchTelegramChannelsByUsernamesSchema(BaseModel):
    usernames: list[str]


class PyrogramImportPostsSchema(BaseModel):
    channel_id: UUID
    start_date: datetime
    end_date: datetime
    download_media: bool = True

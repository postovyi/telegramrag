from pydantic import Field

from .base import BaseConfig


class TelegramConfig(BaseConfig):
    api_id: int = Field(..., alias='TELEGRAM_API_ID')
    api_hash: str = Field(..., alias='TELEGRAM_API_HASH')
    session_string: str = Field(..., alias='TELEGRAM_SESSION_STRING')
    session_name: str = Field(default='telegramrag', alias='TELEGRAM_SESSION_NAME')
    channel_search_limit: int = Field(default=5, alias='TELEGRAM_CHANNEL_SEARCH_LIMIT')

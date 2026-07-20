from .db import DBConfig
from .rag import RAGConfig
from .telegram import TelegramConfig


class Settings:
    db: DBConfig = DBConfig()
    rag: RAGConfig = RAGConfig()
    telegram: TelegramConfig = TelegramConfig()


settings = Settings()
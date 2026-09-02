"""Delete all telegram_post rows so switching EMBEDDING_PROVIDER/EMBEDDING_MODEL/EMBEDDING_N_DIM
does not leave stale vectors of the wrong dimension in the database.

telegram_post.embedding is NOT NULL, so clearing embeddings requires deleting the rows outright;
run a re-import afterwards to repopulate posts with the new provider's embeddings.

Usage: uv run python scripts/clear_embeddings.py
"""

import asyncio

from sqlalchemy import delete

from app.db.database import async_session_maker
from app.models.telegram import TelegramPost


async def clear_embeddings() -> None:
    async with async_session_maker() as session, session.begin():
        result = await session.execute(delete(TelegramPost))
        print(f'Deleted {result.rowcount} post(s).')


if __name__ == '__main__':
    asyncio.run(clear_embeddings())

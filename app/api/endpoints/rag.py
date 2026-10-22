from typing import Annotated

from fastapi import APIRouter, Depends, File, Form

from app.api.dependencies import get_telegram_rag_service
from app.schemas import RAGInputSchema, RetrievedItemSchema
from app.services.telegram import TelegramRAGService

router = APIRouter(prefix='/rag', tags=['rag'])


@router.post('/retrieve', response_model=list[RetrievedItemSchema])
async def retrieve(
    query: Annotated[str, Form(description='The query string for RAG retrieval.')],
    media: Annotated[bytes | None, File(description='Optional media file content.')] = None,
    service: TelegramRAGService = Depends(get_telegram_rag_service),
) -> list[RetrievedItemSchema]:
    """Retrieve relevant Telegram posts and post images using a RAG strategy (e.g., HyDE or Self-RAG).

    Items are `post` or `image` hits merged by similarity. Every item carries `post_id`; `image` items also carry
    `media_id`/`media_url` — fetch the picture itself from `GET /telegram/media/{media_id}`.
    """
    input_data = RAGInputSchema(query=query, media=media)
    return await service.retrieve(input_data)

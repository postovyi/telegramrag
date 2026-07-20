from typing import Annotated

from fastapi import APIRouter, Depends, File, Form

from app.api.dependencies import get_telegram_rag_service
from app.schemas import RAGInputSchema, TelegramPostSchema
from app.services.telegram import TelegramRAGService

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/retrieve", response_model=list[TelegramPostSchema])
async def retrieve(
    query: Annotated[str, Form(description="The query string for RAG retrieval.")],
    media: Annotated[bytes | None, File(description="Optional media file content.")] = None,
    service: TelegramRAGService = Depends(get_telegram_rag_service),
) -> list[TelegramPostSchema]:
    """Retrieve relevant Telegram posts using a RAG strategy (e.g., HyDE or Self-RAG).

    Supports optional image media file upload for multimodal embedding.
    """
    input_data = RAGInputSchema(query=query, media=media)
    return await service.retrieve(input_data)

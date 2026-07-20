from fastapi import APIRouter

from .rag import router as rag_router
from .telegram import router as telegram_router

main_router = APIRouter()
main_router.include_router(telegram_router)
main_router.include_router(rag_router)



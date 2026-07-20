from fastapi import FastAPI

from app.api.endpoints import main_router
import uvicorn

app = FastAPI(
    title="Telegram RAG Service API",
    description="API for scraping, searching, and managing Telegram channels/posts for RAG systems.",
    version="0.1.0",
)

app.include_router(main_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

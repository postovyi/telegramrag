# TelegramRAG

A FastAPI service that scrapes Telegram channels and posts, embeds their text, and lets you
retrieve the most relevant posts for a query through a RAG (Retrieval-Augmented Generation)
pipeline.

- **Scraping** — Telegram channels/posts are pulled via [Pyrofork](https://github.com/Mayuri-Chan/pyrofork).
- **Embedding** — post text is embedded via a configurable provider: local `sentence-transformers`
  (default, `BAAI/bge-m3`), OpenAI, or Google (`EMBEDDING_PROVIDER` env var).
- **Storage** — posts and their vector embeddings live in Postgres with [pgvector](https://github.com/pgvector/pgvector).
- **Retrieval** — three interchangeable RAG strategies: `naive` (default, embeds the query
  directly), `HyDE`, and `Self-RAG` (both LLM-backed, built on `atomic-agents` + `instructor`,
  against a configurable LLM provider: OpenAI, Google, or any OpenAI-compatible server — Ollama,
  LM Studio, MLX — via `LLM_PROVIDER`).
- **MCP server** — a standalone local MCP server (`mcp_server/`) exposes RAG retrieval as an
  MCP tool for use from Claude Desktop, Claude Code, or any other MCP client.

> Image embedding was removed — media is scraped and stored, but only text is indexed/searched.

## Architecture

Layering is strict: **API → Service → Repository → Model**.

```
app/
├── api/          FastAPI routers (telegram.py, rag.py) + dependency injection wiring
├── services/      TelegramService, TelegramRAGService, PyrogramService, RAG strategies
├── repository/    Generic SQLAlchemy repository + pgvector similarity search
├── models/        SQLAlchemy models (TelegramChannel, TelegramPost)
├── schemas/       Pydantic schemas (DB-facing, API-facing, scraping-facing)
└── core/config/   pydantic-settings, one class per concern (db, rag, telegram)

scripts/
└── clear_embeddings.py   Deletes stored posts before switching embedding provider/model/dimension
```

See [`CLAUDE.md`](./CLAUDE.md) for the full architecture breakdown, conventions, and known
gotchas.

## Quick start

**Requirements:** Python >=3.14, [`uv`](https://docs.astral.sh/uv/), Docker (optional, for the
full containerized stack), a Postgres instance with the `pgvector` extension.

1. Copy `.env.example` to `.env` and fill in `DB_*`, `EMBEDDING_MODEL`, `EMBEDDING_N_DIM`, and
   `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` / `TELEGRAM_SESSION_STRING` at minimum. To use OpenAI
   or Google instead of the local defaults, also set `LLM_PROVIDER`/`LLM_API_KEY` and/or
   `EMBEDDING_PROVIDER`/`EMBEDDING_API_KEY` — see the comments in `.env.example`.
2. Install dependencies and run migrations:

   ```bash
   uv sync
   uv run alembic upgrade head
   ```

3. Start the API:

   ```bash
   uv run uvicorn app.main:app --reload
   ```

   The API is now available at `http://localhost:8000`, with interactive docs at
   `http://localhost:8000/docs`.

### Or run everything with Docker

```bash
docker compose up --build
```

This starts the app and a `pgvector`-enabled Postgres container together. If you're using a
local Ollama instance for HyDE/Self-RAG, see the Docker networking note in `CLAUDE.md`.

## API

- `POST /telegram/import/channels` — scrape and import channels by keyword search.
- `POST /telegram/import/posts` — scrape and import a channel's posts within a date range.
- `GET/POST /telegram/channels`, `GET /telegram/channels/{id}` — channel CRUD/lookup.
- `GET/POST /telegram/posts`, `GET /telegram/posts/{id}` — post CRUD/lookup.
- `POST /rag/retrieve` — retrieve the most relevant posts for a text query, using whichever
  RAG strategy is configured (`RAG_STRATEGY` env var: `naive` / `hyde` / `selfrag`).

Full request/response schemas are available at `/docs` once the app is running.

## MCP server

`mcp_server/` is a separate, standalone MCP server that wraps `POST /rag/retrieve` as a single
MCP tool, `retrieve_posts(query: str)`, for local use with Claude Desktop, Claude Code, or any
other MCP client — see [`mcp_server/README.md`](./mcp_server/README.md) for setup and usage.

## Development

```bash
uv run ruff check --fix     # lint
uv run ruff format          # format
uv run alembic revision --autogenerate -m "message"   # create a migration from model changes
uv run alembic upgrade head                            # apply migrations
uv run python scripts/clear_embeddings.py               # delete all posts before switching
                                                          # EMBEDDING_PROVIDER/MODEL/N_DIM
```
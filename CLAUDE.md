# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

FastAPI service that scrapes Telegram channels/posts (via Pyrofork), embeds them (text + image via
sentence-transformers), stores them in Postgres/pgvector, and retrieves relevant posts through RAG strategies
(HyDE, Self-RAG) built on `atomic-agents` + `instructor`, backed by a configurable LLM (default `ollama/gemma4`).

## Commands

Dependency management is `uv` (see `uv.lock`, Python `>=3.14`).

```bash
uv sync                                    # install dependencies
uv run uvicorn app.main:app --reload       # run the API locally (http://localhost:8000)
uv run ruff check --fix                    # lint
uv run ruff format                         # format
uv run alembic revision --autogenerate -m "message"   # create a migration from model changes
uv run alembic upgrade head                # apply migrations
docker compose up --build                  # run app + postgres/pgvector together
```

There is no test suite in the repo currently.

Configuration is env-driven via `.env` (see `.env.example`), loaded through `pydantic-settings`
(`app/core/config/*`). Required at minimum: `DB_*`, `EMBEDDING_MODEL`, `EMBEDDING_N_DIM`,
`TELEGRAM_API_ID`/`TELEGRAM_API_HASH`/`TELEGRAM_SESSION_STRING`.

## Architecture

Layering is strict: **API → Service → Repository → Model**, each only talking to the layer directly below.

- `app/api/endpoints/` — FastAPI routers (`telegram.py`, `rag.py`), thin: validate input via schemas, call a
  service, translate service exceptions (e.g. `NoResultFound`) to `HTTPException`.
- `app/api/dependencies.py` — wires up the DI graph per-request: opens a DB session/transaction (`get_db`),
  constructs repositories, and builds services (`TelegramService`, `TelegramRAGService`). This is the place to
  look to see how everything is actually assembled. Also holds the singleton `PyrogramService` instance (one
  Telegram client/session reused across requests) and the `RAG_STRATEGY` switch (`hyde` vs `selfrag`) that picks
  which `RAGStrategy` implementation `TelegramRAGService` gets.
- `app/services/telegram.py` — `TelegramService` (CRUD + Pyrogram-backed import of channels/posts) and
  `TelegramRAGService` (thin wrapper delegating `retrieve()` to whichever `RAGStrategy` it was given).
- `app/services/pyrogram.py` — `PyrogramService`, a persistence-free wrapper around Pyrofork for scraping
  channels/posts; used as an async context manager (`__aenter__`/`__aexit__` start/stop the client). Returns
  plain schemas that map onto `TelegramService` create inputs — no DB access here.
- `app/services/rag/` — RAG strategies implementing the `RAGStrategy` protocol (`base.py`): `hyde.py` generates a
  hypothetical document via an LLM agent then embeds/searches on it; `selfrag.py` refines the query via an LLM
  agent first. Both combine text + (optional) image embeddings before calling
  `TelegramPostRepository.find_by_embedding`. `embeddings.py` holds `EmbeddingService`, a thin wrapper around a
  single shared `SentenceTransformer` instance for text/image embedding.
- `app/repository/base.py` — generic `SQLAlchemyRepository[ModelType]` used by all repositories. Filtering uses
  Django-style kwargs: `field__op=value` (e.g. `posted_at__ge=...`), where `op` maps through `action_map` to a
  SQLAlchemy column method (`gt`, `lt`, `ge`, `le`, `in`, `contains`, `eq`, `ne`); a bare `field=value` implies
  `__eq`. `get_multi(offset, limit, **filters)` takes `offset`/`limit` as positional-only; `limit=None` returns
  all matching rows unpaginated.
- `app/repository/telegram.py` — concrete repositories; `TelegramPostRepository`/`TelegramPostMediaRepository`
  add `find_by_embedding()` (pgvector cosine-distance ordering, capped at `settings.rag.top_k`).
- `app/models/` — SQLAlchemy declarative models (`TelegramChannel`, `TelegramPost`, `TelegramPostMedia`), all
  UUID-keyed via `BaseId`. Posts and media store `pgvector` `Vector` columns sized by `settings.rag.embedding_n_dim`.
- `app/schemas/` — Pydantic schemas, split between DB-facing (`TelegramPostInputSchema`, etc.), API-facing
  (`TelegramPostSchema`, `CreateTelegramChannelSchema`, ...), and Pyrogram-scraping schemas
  (`ScrapedTelegramPostSchema`, `PyrogramImportChannelsSchema`, ...).
- `app/core/config/` — one `pydantic-settings` class per concern (`db.py`, `rag.py`, `telegram.py`), all reading
  from `.env`, aggregated into a single `settings` singleton in `settings.py`.
- `alembic/` — migrations; `env.py` pulls the DB URL from `settings.db.database_url` and metadata from
  `app.models.Base`, so `.env` must be populated before running alembic commands.

## Conventions

- Lint/format via `ruff` (line length 120, single quotes, `py39`-compatible syntax target despite the project
  itself requiring `>=3.14`). Rule set includes bandit (`S`), bugbear (`B`), annotations (`ANN`), isort (`I`) —
  run `ruff check --fix` before considering work done.
- Repositories raise/propagate SQLAlchemy exceptions (e.g. `NoResultFound`, `IntegrityError`) directly; it's the
  API layer's job to catch and convert them to HTTP responses, not the service layer's.

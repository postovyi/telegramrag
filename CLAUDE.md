# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

FastAPI service that scrapes Telegram channels/posts (via Pyrofork), embeds post text (via `BAAI/bge-m3` through
sentence-transformers), stores them in Postgres/pgvector, and retrieves relevant posts through RAG strategies
(`naive`, HyDE, Self-RAG) — HyDE/Self-RAG built on `atomic-agents` + `instructor`, backed by a configurable LLM
(default `ollama/gemma4`). Post photos are embedded too (multimodal model, e.g. `google/gemini-embedding-2` via OpenRouter) and stored as
media rows; retrieval returns posts and images in one list (images get reserved slots).

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
  Telegram client/session reused across requests) and the `RAG_STRATEGY` switch (`hyde` / `selfrag` / default
  `naive`) that picks which `RAGStrategy` implementation `TelegramRAGService` gets.
- `app/services/telegram.py` — `TelegramService` (CRUD + Pyrogram-backed import of channels/posts) and
  `TelegramRAGService` (thin wrapper delegating `retrieve()` to whichever `RAGStrategy` it was given).
- `app/services/pyrogram.py` — `PyrogramService`, a persistence-free wrapper around Pyrofork for scraping
  channels/posts; used as an async context manager (`__aenter__`/`__aexit__` start/stop the client). Returns
  plain schemas that map onto `TelegramService` create inputs — no DB access here. Channel search
  (`search_channels`) uses the raw `contacts.search` Telegram API, not `search_global`/`search_chats` — those
  only search chats the account already belongs to.
- `app/services/rag/` — `RAGStrategy` base class (`base.py`) holds shared helpers (`_search`: unified
  post+image top-k). Three concrete strategies: `naive.py` (default — embeds the raw query directly, no LLM call),
  `hyde.py` (LLM generates a hypothetical document, embeds that), `selfrag.py` (LLM refines the query first).
  All end in `_search` → `TelegramPostRepository.find_by_embedding` + `TelegramPostMediaRepository.find_by_embedding`
  (pgvector cosine distance, ascending = most similar first; both return `(row, distance)` pairs).
  `embeddings/` holds `EmbeddingService`, dispatching to one of `SentenceTransformerEmbeddingProvider` /
  `OpenAIEmbeddingProvider` / `GoogleEmbeddingProvider` / `OpenRouterEmbeddingProvider` per
  `settings.rag.embedding_provider` (`embed_text` everywhere; `embed_image` only on the `openrouter` provider —
  others raise `ImageEmbeddingNotSupportedError`; OpenRouter gets `dimensions=EMBEDDING_N_DIM`). `llm_client.py` similarly builds the
  `instructor` client for HyDE/Self-RAG per `settings.rag.llm_provider` (`openai` / `google` /
  `openai_compatible` / `openrouter` — `openai_compatible` covers Ollama, LM Studio, MLX server, anything
  OpenAI-compat, via `LLM_BASE_URL`; `instructor` has no native `mlx` provider string; `openrouter` uses
  `instructor`'s own native `openrouter` provider branch — one API key/base URL routing to many hosted models,
  `LLM_MODEL`/`EMBEDDING_MODEL` take OpenRouter's `provider/model` naming, e.g. `openai/gpt-4o-mini`).
- `app/repository/base.py` — generic `SQLAlchemyRepository[ModelType]` used by all repositories. Filtering uses
  Django-style kwargs: `field__op=value` (e.g. `posted_at__ge=...`), where `op` maps through `action_map` to a
  SQLAlchemy column method (`gt`, `lt`, `ge`, `le`, `in`, `contains`, `eq`, `ne`); a bare `field=value` implies
  `__eq`. `get_multi(offset, limit, **filters)` takes `offset`/`limit` as positional-only; `limit=None` returns
  all matching rows unpaginated. `create()` filters the input dict down to the model's actual table columns
  before `insert().values()` — passing extra fields (e.g. from a schema with unrelated fields) silently corrupts
  the generated SQL otherwise.
- `app/repository/telegram.py` — `find_by_embedding()` on the post and media repositories (pgvector cosine-distance
  ascending, capped at `settings.rag.top_k`, rows returned with their distance); `get_data(media_id)` reads image bytes.
- `app/models/` — SQLAlchemy declarative models (`TelegramChannel`, `TelegramPost`, `TelegramPostMedia`), UUID-keyed via `BaseId`.
  `TelegramPost.embedding` and `TelegramPostMedia.embedding` are `pgvector` `Vector` columns sized by
  `settings.rag.embedding_n_dim`; the post vector is nullable (image-only posts). `TelegramPostMedia` holds the photo
  `data` (bytea, `deferred` — never loaded by searches), `mime_type`, `position`, and `post_id` FK (`ON DELETE CASCADE`).
  Image bytes are served by `GET /telegram/media/{media_id}`; retrieval only returns `media_id`/`media_url`.
- `app/schemas/` — Pydantic schemas, split between DB-facing (`TelegramPostInputSchema`, etc.), API-facing
  (`TelegramPostSchema`, `CreateTelegramChannelSchema`, ...), and Pyrogram-scraping schemas
  (`ScrapedTelegramPostSchema`, `PyrogramImportChannelsSchema`, ...). API-facing schemas need
  `model_config = ConfigDict(from_attributes=True)` to validate directly from ORM objects.
- `app/core/config/` — one `pydantic-settings` class per concern (`db.py`, `rag.py`, `telegram.py`), all reading
  from `.env`, aggregated into a single `settings` singleton in `settings.py`.
- `alembic/` — migrations run on the async engine (`async_engine_from_config` + `connection.run_sync`, not a
  sync `engine_from_config`) since the DB URL is `postgresql+asyncpg://`. `env.py` pulls the URL from
  `settings.db.database_url` and metadata from `app.models.Base`, so `.env` must be populated before running
  alembic commands. `0001_init_telegram` is the squashed base; `0002_post_media` adds the media table and makes the post vector
  nullable (it also deletes post rows and resizes the vector column to the current `EMBEDDING_N_DIM`).

## Conventions

- Lint/format via `ruff` (line length 120, single quotes, `py39`-compatible syntax target despite the project
  itself requiring `>=3.14`). Rule set includes bandit (`S`), bugbear (`B`), annotations (`ANN`), isort (`I`) —
  run `ruff check --fix` before considering work done.
- Repositories raise/propagate SQLAlchemy exceptions (e.g. `NoResultFound`, `IntegrityError`) directly; it's the
  API layer's job to catch and convert them to HTTP responses, not the service layer's.

## Docker / dev environment gotchas

- `alembic/` is **not** volume-mounted into the `app` container (only `./app` is). Editing a migration file on
  the host has no effect inside the running container until you `docker compose cp <file> app:/app/<path>` or
  rebuild the image.
- Adding/removing a Python dependency requires `uv lock` on the host, then `docker compose up -d --build app`
  (image rebuild) — `docker compose exec app uv sync` alone won't pick up a `pyproject.toml` change reliably.
- `.env` / `.env.example` are blocked from direct file-tool access in this environment (permission-denied) —
  ask the user to edit env values themselves.
- Ollama running on the host is reachable from the `app` container via `http://host.docker.internal:11434/v1`
  (`LLM_BASE_URL` env var) — Linux Docker needs the explicit `extra_hosts: host.docker.internal:host-gateway`
  entry in `docker-compose.yml`; it's not automatic like Docker Desktop.
- `instructor.from_provider("ollama/...")` ignores `OLLAMA_API_BASE`/env vars — pass `base_url=` explicitly.
  `atomic_agents.AgentConfig` also defaults `model=` to `"gpt-5-mini"` if not set explicitly — always pass
  `model=settings.rag.llm_model.split("/", 1)[-1]` (or equivalent) when constructing one.
- Any `atomic_agents.AtomicAgent` response schema must subclass `BaseIOSchema`, not plain pydantic `BaseModel` —
  a plain `BaseModel` fails deep inside the agent's message-history validation with a confusing pydantic error.
- `TELEGRAM_SESSION_STRING` must come from Pyrogram/Pyrofork's own `Client.export_session_string()` — a
  Telethon-generated `StringSession` uses a different binary format and fails with a cryptic
  `struct.error: unpack requires a buffer of N bytes`.
- SQLAlchemy ORM relationship attributes (e.g. `post.channel`) must not be lazy-accessed under the async
  session — raises `MissingGreenlet`. Fetch related rows explicitly (`session.get(Model, id)`).
- pgvector `cosine_distance()`: smaller = more similar. Never `order_by(1 - cosine_distance(...))` — that sorts
  least-similar first.
- `TelegramPostMedia.embedding` is `NOT NULL`; `scripts/clear_embeddings.py` (run when switching
  `EMBEDDING_PROVIDER`/`EMBEDDING_MODEL`/`EMBEDDING_N_DIM` on an existing DB) deletes media rows and then post rows
  outright, not just the vectors. The vector column dimension itself changes only via a migration run after the
  new `EMBEDDING_N_DIM` is in `.env` (`alembic downgrade -1 && alembic upgrade head` re-sizes `0002`).
- Gemini embedding via OpenRouter: image input is `input=[{'content': [{'type': 'image_url', 'image_url': {'url':
  'data:image/jpeg;base64,...'}}]}]` with `encoding_format='float'`; text and image vectors share one space, but
  cross-modal distance (~0.55-0.66 relevant, 0.73+ irrelevant) is systematically higher than text-text, so a plain
  distance merge would never surface an image. `_search` therefore gives images reserved slots (`MEDIA_TOP_K`, default 3)
  within `MEDIA_MAX_DISTANCE` (default 0.68, calibrated on few samples — retune after changing the embedding model),
  and fills the rest of `TOP_K` with posts.
- Images are handled in memory only (Pyrogram `in_memory=True` → embed → bytea); a client such as Claude Code that
  wants to *see* an image saves `/telegram/media/{id}` to a temp file and opens it.
- Scripts under `scripts/` aren't on the container's import path from cwd `/` — run them as
  `docker compose exec app sh -c "cd /app && python scripts/foo.py"` (or `uv run python scripts/foo.py` on host).
- `uv run python -c "..."` locally raises `Extra inputs are not permitted` pydantic-settings errors on `settings` —
  this is pre-existing/expected outside Docker; verify config-dependent code inside the `app` container instead.
- After `docker compose up -d` (uvicorn `--reload` mode), the port accepts connections ~10-15s after the
  container shows "Up" — an immediate curl gets `Empty reply from server` / exit 52, not a real failure.

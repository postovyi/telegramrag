# telegramrag-mcp-server

Local MCP server exposing telegramrag's RAG retrieval and live Telegram preview endpoints as MCP tools.

## Requirements

- The telegramrag API running and reachable (default `http://localhost:8000`) — see the main repo's `CLAUDE.md` for how to start it (`uv run uvicorn app.main:app --reload` or `docker compose up --build`).

## Setup

```bash
cd mcp_server
uv sync
```

## Configuration

- `RAG_API_BASE_URL` — base URL of the telegramrag API. Defaults to `http://localhost:8000`.
- `MCP_MAX_OUTPUT_CHARS` — max length (characters) of text returned by tools. Output is cut on a post boundary, silently (no notice). Defaults to `80000`; `0` disables the cap. Does not apply to `search_channels_by_keywords` (structured list).

- `MCP_TRANSPORT` — `stdio` (default) or `streamable-http`.
- `MCP_HOST` / `MCP_PORT` — bind address for `streamable-http`. Default `127.0.0.1:8002`; endpoint is `http://<host>:<port>/mcp`.

## Running over HTTP

```bash
cd mcp_server
MCP_TRANSPORT=streamable-http RAG_API_BASE_URL=http://localhost:8001 uv run rag-mcp-server
# -> http://127.0.0.1:8002/mcp
```

Register in Claude Code: `claude mcp add --transport http telegramrag-http http://127.0.0.1:8002/mcp`

## Running standalone (for debugging)

```bash
cd mcp_server
uv run mcp dev rag_mcp/server.py
```

## Registering with Claude Desktop / Claude Code

Add to your MCP client's config (e.g. `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "telegramrag": {
      "command": "uv",
      "args": ["run", "--project", "/absolute/path/to/telegramrag/mcp_server", "rag-mcp-server"],
      "env": {
        "RAG_API_BASE_URL": "http://localhost:8000",
        "MCP_MAX_OUTPUT_CHARS": "80000"
      }
    }
  }
}
```

## Tools

All tools below call the telegramrag API's `/telegram/preview/...` endpoints — live Telegram lookups, never persisted to the database.

- `fetch_posts_by_username(username: str, start_date: str, end_date: str)` — scrapes a channel's posts (text only) within a date range live via Telegram.
- `fetch_posts_by_usernames(usernames: list[str], start_date: str, end_date: str)` — scrapes posts (text only) within a date range across multiple channels live via Telegram. A username that fails to resolve is silently skipped.
- `fetch_post_by_link(url: str)` — fetches a single post (text only) by its public `t.me/<username>/<message_id>` link, live via Telegram.
- `search_channels_by_keywords(keywords: str)` — searches public Telegram channels by keyword live via Telegram, returns name/username/subscriber count sorted by subscriber count descending. Result count is fixed server-side (`TELEGRAM_CHANNEL_SEARCH_LIMIT`).
- `fetch_channel_by_username(username: str)` — fetches a single channel's name/username/subscriber count live via Telegram.

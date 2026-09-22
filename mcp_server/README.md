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
        "RAG_API_BASE_URL": "http://localhost:8000"
      }
    }
  }
}
```

## Tools

- `retrieve_posts(query: str)` — returns Telegram posts relevant to `query`, retrieved via the configured RAG strategy on the telegramrag API. Reads from the database.
- `fetch_posts_by_username(username: str, start_date: str, end_date: str)` — scrapes a channel's posts (text only) within a date range live via Telegram. Not persisted to the database, unrelated to `retrieve_posts`.
- `search_channels_by_keywords(keywords: str)` — searches public Telegram channels by keyword live via Telegram, returns name/username/subscriber count sorted by subscriber count descending. Result count is fixed server-side (`TELEGRAM_CHANNEL_SEARCH_LIMIT`). Not persisted to the database.

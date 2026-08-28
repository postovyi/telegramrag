# rag-mcp-server

Local MCP server exposing telegramrag's RAG retrieval (`POST /rag/retrieve`) as a single MCP tool, `retrieve_posts`.

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

## Tool

- `retrieve_posts(query: str)` — returns Telegram posts relevant to `query`, retrieved via the configured RAG strategy on the telegramrag API.

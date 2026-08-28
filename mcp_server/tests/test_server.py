import pytest

from rag_mcp import server
from rag_mcp.client import RagApiError


async def test_retrieve_posts_tool_formats_results(monkeypatch):
    async def fake_retrieve_posts(query, base_url):
        assert query == "cats"
        assert base_url == "http://localhost:8000"
        return [
            {
                "id": "1",
                "content": "post about cats",
                "posted_at": "2026-08-01T12:00:00Z",
                "channel_url": "https://t.me/pets",
                "url": "https://t.me/pets/42",
            }
        ]

    monkeypatch.setattr(server, "retrieve_posts", fake_retrieve_posts)

    result = await server.retrieve_posts_tool("cats")

    assert "post about cats" in result
    assert "https://t.me/pets/42" in result


async def test_retrieve_posts_tool_handles_empty_results(monkeypatch):
    async def fake_retrieve_posts(query, base_url):
        return []

    monkeypatch.setattr(server, "retrieve_posts", fake_retrieve_posts)

    result = await server.retrieve_posts_tool("nothing matches")

    assert result == "No relevant posts found."


async def test_retrieve_posts_tool_surfaces_api_errors(monkeypatch):
    async def fake_retrieve_posts(query, base_url):
        raise RagApiError("Could not reach RAG API at http://localhost:8000. Is it running?")

    monkeypatch.setattr(server, "retrieve_posts", fake_retrieve_posts)

    result = await server.retrieve_posts_tool("cats")

    assert result.startswith("Error: Could not reach RAG API")


def test_base_url_defaults_to_localhost(monkeypatch):
    monkeypatch.delenv("RAG_API_BASE_URL", raising=False)

    assert server._base_url() == "http://localhost:8000"


def test_base_url_reads_env_override(monkeypatch):
    monkeypatch.setenv("RAG_API_BASE_URL", "http://localhost:9000")

    assert server._base_url() == "http://localhost:9000"

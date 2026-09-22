import pytest

from rag_mcp import server
from rag_mcp.client import RagApiError


async def test_retrieve_posts_tool_formats_results(monkeypatch):
    async def fake_retrieve_posts(query, base_url):
        assert query == 'cats'
        assert base_url == 'http://localhost:8000'
        return [
            {
                'id': '1',
                'content': 'post about cats',
                'posted_at': '2026-08-01T12:00:00Z',
                'channel_url': 'https://t.me/pets',
                'url': 'https://t.me/pets/42',
            }
        ]

    monkeypatch.setattr(server, 'retrieve_posts', fake_retrieve_posts)

    result = await server.retrieve_posts_tool('cats')

    assert 'post about cats' in result
    assert 'https://t.me/pets/42' in result


async def test_retrieve_posts_tool_formats_null_content(monkeypatch):
    async def fake_retrieve_posts(query, base_url):
        return [
            {
                'id': '1',
                'content': None,
                'posted_at': '2026-08-01T12:00:00Z',
                'channel_url': 'https://t.me/pets',
                'url': 'https://t.me/pets/42',
            }
        ]

    monkeypatch.setattr(server, 'retrieve_posts', fake_retrieve_posts)

    result = await server.retrieve_posts_tool('cats')

    assert '(no text)' in result
    assert 'None' not in result


async def test_retrieve_posts_tool_handles_empty_results(monkeypatch):
    async def fake_retrieve_posts(query, base_url):
        return []

    monkeypatch.setattr(server, 'retrieve_posts', fake_retrieve_posts)

    result = await server.retrieve_posts_tool('nothing matches')

    assert result == 'No relevant posts found.'


async def test_retrieve_posts_tool_surfaces_api_errors(monkeypatch):
    async def fake_retrieve_posts(query, base_url):
        raise RagApiError('Could not reach RAG API at http://localhost:8000. Is it running?')

    monkeypatch.setattr(server, 'retrieve_posts', fake_retrieve_posts)

    result = await server.retrieve_posts_tool('cats')

    assert result.startswith('Error: Could not reach RAG API')


def test_base_url_defaults_to_localhost(monkeypatch):
    monkeypatch.delenv('RAG_API_BASE_URL', raising=False)

    assert server._base_url() == 'http://localhost:8000'


def test_base_url_reads_env_override(monkeypatch):
    monkeypatch.setenv('RAG_API_BASE_URL', 'http://localhost:9000')

    assert server._base_url() == 'http://localhost:9000'


async def test_fetch_posts_by_username_tool_formats_results(monkeypatch):
    async def fake_fetch_posts_by_username(username, start_date, end_date, base_url):
        assert username == 'telegram'
        assert start_date == '2024-01-01'
        assert end_date == '2024-01-02'
        assert base_url == 'http://localhost:8000'
        return [
            {
                'content': 'hello world',
                'posted_at': '2024-01-01T12:00:00',
                'channel_username': 'telegram',
                'url': 'https://t.me/telegram/1',
                'media': [],
            }
        ]

    monkeypatch.setattr(server, 'fetch_posts_by_username', fake_fetch_posts_by_username)

    result = await server.fetch_posts_by_username_tool('telegram', '2024-01-01', '2024-01-02')

    assert 'hello world' in result
    assert 'https://t.me/telegram/1' in result


async def test_fetch_posts_by_username_tool_formats_null_content(monkeypatch):
    async def fake_fetch_posts_by_username(username, start_date, end_date, base_url):
        return [
            {
                'content': None,
                'posted_at': '2024-01-01T12:00:00',
                'channel_username': 'telegram',
                'url': 'https://t.me/telegram/1',
                'media': [],
            }
        ]

    monkeypatch.setattr(server, 'fetch_posts_by_username', fake_fetch_posts_by_username)

    result = await server.fetch_posts_by_username_tool('telegram', '2024-01-01', '2024-01-02')

    assert '(no text)' in result
    assert 'None' not in result


async def test_fetch_posts_by_username_tool_handles_empty_results(monkeypatch):
    async def fake_fetch_posts_by_username(username, start_date, end_date, base_url):
        return []

    monkeypatch.setattr(server, 'fetch_posts_by_username', fake_fetch_posts_by_username)

    result = await server.fetch_posts_by_username_tool('telegram', '2024-01-01', '2024-01-02')

    assert result == 'No posts found in that range.'


async def test_fetch_posts_by_username_tool_surfaces_api_errors(monkeypatch):
    async def fake_fetch_posts_by_username(username, start_date, end_date, base_url):
        raise RagApiError('Could not reach RAG API at http://localhost:8000. Is it running?')

    monkeypatch.setattr(server, 'fetch_posts_by_username', fake_fetch_posts_by_username)

    result = await server.fetch_posts_by_username_tool('telegram', '2024-01-01', '2024-01-02')

    assert result.startswith('Error: Could not reach RAG API')


async def test_search_channels_by_keywords_tool_returns_raw_list(monkeypatch):
    async def fake_search_channels_by_keywords(keywords, base_url):
        assert keywords == 'news'
        assert base_url == 'http://localhost:8000'
        return [{'name': 'News Channel', 'username': 'newschannel', 'subscribers_count': 1000}]

    monkeypatch.setattr(server, 'search_channels_by_keywords', fake_search_channels_by_keywords)

    result = await server.search_channels_by_keywords_tool('news')

    assert result == [{'name': 'News Channel', 'username': 'newschannel', 'subscribers_count': 1000}]


async def test_search_channels_by_keywords_tool_propagates_api_errors(monkeypatch):
    async def fake_search_channels_by_keywords(keywords, base_url):
        raise RagApiError('Could not reach RAG API at http://localhost:8000. Is it running?')

    monkeypatch.setattr(server, 'search_channels_by_keywords', fake_search_channels_by_keywords)

    with pytest.raises(RagApiError, match='Could not reach RAG API'):
        await server.search_channels_by_keywords_tool('news')

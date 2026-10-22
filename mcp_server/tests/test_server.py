import pytest

from rag_mcp import server
from rag_mcp.client import RagApiError


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


async def test_fetch_post_by_link_tool_formats_result(monkeypatch):
    async def fake_fetch_post_by_link(url, base_url):
        assert url == 'https://t.me/telegram/1'
        assert base_url == 'http://localhost:8000'
        return {
            'content': 'hello world',
            'posted_at': '2024-01-01T12:00:00',
            'channel_username': 'telegram',
            'channel_name': 'Telegram News',
            'url': 'https://t.me/telegram/1',
            'media': [],
        }

    monkeypatch.setattr(server, 'fetch_post_by_link', fake_fetch_post_by_link)

    result = await server.fetch_post_by_link_tool('https://t.me/telegram/1')

    assert 'hello world' in result
    assert 'https://t.me/telegram/1' in result
    assert 'Telegram News' in result


async def test_fetch_post_by_link_tool_falls_back_to_username_when_name_missing(monkeypatch):
    async def fake_fetch_post_by_link(url, base_url):
        return {
            'content': 'hello world',
            'posted_at': '2024-01-01T12:00:00',
            'channel_username': 'telegram',
            'channel_name': None,
            'url': 'https://t.me/telegram/1',
            'media': [],
        }

    monkeypatch.setattr(server, 'fetch_post_by_link', fake_fetch_post_by_link)

    result = await server.fetch_post_by_link_tool('https://t.me/telegram/1')

    assert 'telegram' in result


async def test_fetch_post_by_link_tool_formats_null_content(monkeypatch):
    async def fake_fetch_post_by_link(url, base_url):
        return {
            'content': None,
            'posted_at': '2024-01-01T12:00:00',
            'channel_username': 'telegram',
            'channel_name': 'Telegram News',
            'url': 'https://t.me/telegram/1',
            'media': [],
        }

    monkeypatch.setattr(server, 'fetch_post_by_link', fake_fetch_post_by_link)

    result = await server.fetch_post_by_link_tool('https://t.me/telegram/1')

    assert '(no text)' in result
    assert 'None' not in result


async def test_fetch_post_by_link_tool_surfaces_api_errors(monkeypatch):
    async def fake_fetch_post_by_link(url, base_url):
        raise RagApiError('RAG API returned error 404: not found')

    monkeypatch.setattr(server, 'fetch_post_by_link', fake_fetch_post_by_link)

    result = await server.fetch_post_by_link_tool('https://t.me/telegram/1')

    assert result.startswith('Error: RAG API returned error 404')


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


async def test_fetch_channel_by_username_tool_formats_result(monkeypatch):
    async def fake_fetch_channel_by_username(username, base_url):
        assert username == 'telegram'
        assert base_url == 'http://localhost:8000'
        return {'name': 'Telegram', 'username': 'telegram', 'subscribers_count': 1000}

    monkeypatch.setattr(server, 'fetch_channel_by_username', fake_fetch_channel_by_username)

    result = await server.fetch_channel_by_username_tool('telegram')

    assert 'Telegram' in result
    assert '@telegram' in result
    assert '1000' in result


async def test_fetch_channel_by_username_tool_surfaces_api_errors(monkeypatch):
    async def fake_fetch_channel_by_username(username, base_url):
        raise RagApiError('RAG API returned error 404: not found')

    monkeypatch.setattr(server, 'fetch_channel_by_username', fake_fetch_channel_by_username)

    result = await server.fetch_channel_by_username_tool('telegram')

    assert result.startswith('Error: RAG API returned error 404')


async def test_fetch_posts_by_usernames_tool_formats_results(monkeypatch):
    async def fake_fetch_posts_by_usernames(usernames, start_date, end_date, base_url):
        assert usernames == ['telegram', 'durov']
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

    monkeypatch.setattr(server, 'fetch_posts_by_usernames', fake_fetch_posts_by_usernames)

    result = await server.fetch_posts_by_usernames_tool(['telegram', 'durov'], '2024-01-01', '2024-01-02')

    assert 'hello world' in result
    assert 'telegram' in result
    assert 'https://t.me/telegram/1' in result


async def test_fetch_posts_by_usernames_tool_formats_null_content(monkeypatch):
    async def fake_fetch_posts_by_usernames(usernames, start_date, end_date, base_url):
        return [
            {
                'content': None,
                'posted_at': '2024-01-01T12:00:00',
                'channel_username': 'telegram',
                'url': 'https://t.me/telegram/1',
                'media': [],
            }
        ]

    monkeypatch.setattr(server, 'fetch_posts_by_usernames', fake_fetch_posts_by_usernames)

    result = await server.fetch_posts_by_usernames_tool(['telegram'], '2024-01-01', '2024-01-02')

    assert '(no text)' in result
    assert 'None' not in result


async def test_fetch_posts_by_usernames_tool_handles_empty_results(monkeypatch):
    async def fake_fetch_posts_by_usernames(usernames, start_date, end_date, base_url):
        return []

    monkeypatch.setattr(server, 'fetch_posts_by_usernames', fake_fetch_posts_by_usernames)

    result = await server.fetch_posts_by_usernames_tool(['telegram'], '2024-01-01', '2024-01-02')

    assert result == 'No posts found in that range.'


async def test_fetch_posts_by_usernames_tool_surfaces_api_errors(monkeypatch):
    async def fake_fetch_posts_by_usernames(usernames, start_date, end_date, base_url):
        raise RagApiError('Could not reach RAG API at http://localhost:8000. Is it running?')

    monkeypatch.setattr(server, 'fetch_posts_by_usernames', fake_fetch_posts_by_usernames)

    result = await server.fetch_posts_by_usernames_tool(['telegram'], '2024-01-01', '2024-01-02')

    assert result.startswith('Error: Could not reach RAG API')


async def _echo(text):
    return text


def test_max_output_chars_defaults_when_unset_or_invalid(monkeypatch):
    monkeypatch.delenv('MCP_MAX_OUTPUT_CHARS', raising=False)
    assert server._max_output_chars() == 80000
    monkeypatch.setenv('MCP_MAX_OUTPUT_CHARS', '')
    assert server._max_output_chars() == 80000
    monkeypatch.setenv('MCP_MAX_OUTPUT_CHARS', 'abc')
    assert server._max_output_chars() == 80000


async def test_limit_output_leaves_short_output_unchanged(monkeypatch):
    monkeypatch.setenv('MCP_MAX_OUTPUT_CHARS', '100')

    assert await server.limit_output(_echo)('- [a] x\n  hi') == '- [a] x\n  hi'


async def test_limit_output_cuts_on_entry_boundary(monkeypatch):
    monkeypatch.setenv('MCP_MAX_OUTPUT_CHARS', '35')
    text = '- [1] aaaa\n  one\n- [2] bbbb\n  two\n- [3] cccc\n  three'

    result = await server.limit_output(_echo)(text)

    assert result == '- [1] aaaa\n  one\n- [2] bbbb\n  two'
    assert len(result) <= 35


async def test_limit_output_cuts_oversized_single_entry_by_chars(monkeypatch):
    monkeypatch.setenv('MCP_MAX_OUTPUT_CHARS', '10')

    assert await server.limit_output(_echo)('- [1] ' + 'x' * 50) == '- [1] xxxx'


async def test_limit_output_zero_disables_cap(monkeypatch):
    monkeypatch.setenv('MCP_MAX_OUTPUT_CHARS', '0')
    text = 'x' * 200000

    assert await server.limit_output(_echo)(text) == text


async def test_limit_output_uses_default_cap_when_unset(monkeypatch):
    monkeypatch.delenv('MCP_MAX_OUTPUT_CHARS', raising=False)

    assert len(await server.limit_output(_echo)('x' * 90000)) == 80000


async def test_limit_output_passes_non_str_through(monkeypatch):
    monkeypatch.setenv('MCP_MAX_OUTPUT_CHARS', '1')
    data = [{'name': 'n', 'username': 'u', 'subscribers_count': 1}]

    assert await server.limit_output(_echo)(data) == data


def test_limit_output_preserves_signature_and_docstring():
    wrapped = server.limit_output(server.fetch_posts_by_username_tool)

    assert wrapped.__doc__ == server.fetch_posts_by_username_tool.__doc__
    assert wrapped.__wrapped__ is server.fetch_posts_by_username_tool

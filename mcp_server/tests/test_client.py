import httpx
import pytest

from rag_mcp.client import (
    RagApiError,
    fetch_channel_by_username,
    fetch_post_by_link,
    fetch_posts_by_username,
    fetch_posts_by_usernames,
    search_channels_by_keywords,
)

BASE_URL = 'http://localhost:8000'


async def test_fetch_posts_by_username_returns_parsed_json(httpx_mock):
    httpx_mock.add_response(
        url=f'{BASE_URL}/telegram/preview/posts/by-username?username=telegram&start_date=2024-01-01&end_date=2024-01-02',
        method='GET',
        json=[
            {
                'content': 'hello',
                'posted_at': '2024-01-01T12:00:00',
                'channel_username': 'telegram',
                'url': 'https://t.me/telegram/1',
                'media': [],
            }
        ],
    )

    result = await fetch_posts_by_username('telegram', '2024-01-01', '2024-01-02', BASE_URL)

    assert result == [
        {
            'content': 'hello',
            'posted_at': '2024-01-01T12:00:00',
            'channel_username': 'telegram',
            'url': 'https://t.me/telegram/1',
            'media': [],
        }
    ]


async def test_fetch_posts_by_username_raises_on_connection_error(httpx_mock):
    httpx_mock.add_exception(httpx.ConnectError('connection refused'))

    with pytest.raises(RagApiError, match='Could not reach RAG API'):
        await fetch_posts_by_username('telegram', '2024-01-01', '2024-01-02', BASE_URL)


async def test_fetch_posts_by_username_raises_on_http_error(httpx_mock):
    httpx_mock.add_response(
        url=f'{BASE_URL}/telegram/preview/posts/by-username?username=telegram&start_date=2024-01-01&end_date=2024-01-02',
        method='GET',
        status_code=404,
        text='not found',
    )

    with pytest.raises(RagApiError, match='RAG API returned error 404'):
        await fetch_posts_by_username('telegram', '2024-01-01', '2024-01-02', BASE_URL)


async def test_fetch_post_by_link_returns_parsed_json(httpx_mock):
    httpx_mock.add_response(
        url=f'{BASE_URL}/telegram/preview/posts/by-link?url=https%3A%2F%2Ft.me%2Ftelegram%2F1',
        method='GET',
        json={
            'content': 'hello',
            'posted_at': '2024-01-01T12:00:00',
            'channel_username': 'telegram',
            'url': 'https://t.me/telegram/1',
            'media': [],
        },
    )

    result = await fetch_post_by_link('https://t.me/telegram/1', BASE_URL)

    assert result == {
        'content': 'hello',
        'posted_at': '2024-01-01T12:00:00',
        'channel_username': 'telegram',
        'url': 'https://t.me/telegram/1',
        'media': [],
    }


async def test_fetch_post_by_link_raises_on_connection_error(httpx_mock):
    httpx_mock.add_exception(httpx.ConnectError('connection refused'))

    with pytest.raises(RagApiError, match='Could not reach RAG API'):
        await fetch_post_by_link('https://t.me/telegram/1', BASE_URL)


async def test_fetch_post_by_link_raises_on_http_error(httpx_mock):
    httpx_mock.add_response(
        url=f'{BASE_URL}/telegram/preview/posts/by-link?url=https%3A%2F%2Ft.me%2Ftelegram%2F1',
        method='GET',
        status_code=404,
        text='not found',
    )

    with pytest.raises(RagApiError, match='RAG API returned error 404'):
        await fetch_post_by_link('https://t.me/telegram/1', BASE_URL)


async def test_search_channels_by_keywords_returns_parsed_json(httpx_mock):
    httpx_mock.add_response(
        url=f'{BASE_URL}/telegram/preview/channels/search-by-keywords?keywords=news',
        method='GET',
        json=[{'name': 'News Channel', 'username': 'newschannel', 'subscribers_count': 1000}],
    )

    result = await search_channels_by_keywords('news', BASE_URL)

    assert result == [{'name': 'News Channel', 'username': 'newschannel', 'subscribers_count': 1000}]


async def test_search_channels_by_keywords_raises_on_connection_error(httpx_mock):
    httpx_mock.add_exception(httpx.ConnectError('connection refused'))

    with pytest.raises(RagApiError, match='Could not reach RAG API'):
        await search_channels_by_keywords('news', BASE_URL)


async def test_search_channels_by_keywords_raises_on_http_error(httpx_mock):
    httpx_mock.add_response(
        url=f'{BASE_URL}/telegram/preview/channels/search-by-keywords?keywords=news',
        method='GET',
        status_code=500,
        text='internal error',
    )

    with pytest.raises(RagApiError, match='RAG API returned error 500'):
        await search_channels_by_keywords('news', BASE_URL)


async def test_fetch_channel_by_username_returns_parsed_json(httpx_mock):
    httpx_mock.add_response(
        url=f'{BASE_URL}/telegram/preview/channels/by-username?username=telegram',
        method='GET',
        json={'name': 'Telegram', 'username': 'telegram', 'subscribers_count': 1000},
    )

    result = await fetch_channel_by_username('telegram', BASE_URL)

    assert result == {'name': 'Telegram', 'username': 'telegram', 'subscribers_count': 1000}


async def test_fetch_channel_by_username_raises_on_connection_error(httpx_mock):
    httpx_mock.add_exception(httpx.ConnectError('connection refused'))

    with pytest.raises(RagApiError, match='Could not reach RAG API'):
        await fetch_channel_by_username('telegram', BASE_URL)


async def test_fetch_channel_by_username_raises_on_http_error(httpx_mock):
    httpx_mock.add_response(
        url=f'{BASE_URL}/telegram/preview/channels/by-username?username=telegram',
        method='GET',
        status_code=404,
        text='not found',
    )

    with pytest.raises(RagApiError, match='RAG API returned error 404'):
        await fetch_channel_by_username('telegram', BASE_URL)


async def test_fetch_posts_by_usernames_returns_parsed_json(httpx_mock):
    httpx_mock.add_response(
        url=f'{BASE_URL}/telegram/preview/posts/by-usernames',
        method='POST',
        json=[
            {
                'content': 'hello',
                'posted_at': '2024-01-01T12:00:00',
                'channel_username': 'telegram',
                'url': 'https://t.me/telegram/1',
                'media': [],
            }
        ],
    )

    result = await fetch_posts_by_usernames(['telegram', 'durov'], '2024-01-01', '2024-01-02', BASE_URL)

    assert result == [
        {
            'content': 'hello',
            'posted_at': '2024-01-01T12:00:00',
            'channel_username': 'telegram',
            'url': 'https://t.me/telegram/1',
            'media': [],
        }
    ]


async def test_fetch_posts_by_usernames_raises_on_connection_error(httpx_mock):
    httpx_mock.add_exception(httpx.ConnectError('connection refused'))

    with pytest.raises(RagApiError, match='Could not reach RAG API'):
        await fetch_posts_by_usernames(['telegram'], '2024-01-01', '2024-01-02', BASE_URL)


async def test_fetch_posts_by_usernames_raises_on_http_error(httpx_mock):
    httpx_mock.add_response(
        url=f'{BASE_URL}/telegram/preview/posts/by-usernames',
        method='POST',
        status_code=404,
        text='not found',
    )

    with pytest.raises(RagApiError, match='RAG API returned error 404'):
        await fetch_posts_by_usernames(['telegram'], '2024-01-01', '2024-01-02', BASE_URL)

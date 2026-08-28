import httpx
import pytest

from rag_mcp.client import RagApiError, retrieve_posts

BASE_URL = "http://localhost:8000"


async def test_retrieve_posts_returns_parsed_json(httpx_mock):
    httpx_mock.add_response(
        url=f"{BASE_URL}/rag/retrieve",
        method="POST",
        json=[
            {
                "id": "8f14e45f-ceea-467e-bd25-7b90b1c3f9f0",
                "content": "hello world",
                "posted_at": "2026-08-01T12:00:00Z",
                "channel_url": "https://t.me/somechannel",
                "url": "https://t.me/somechannel/1",
            }
        ],
    )

    result = await retrieve_posts("hello", BASE_URL)

    assert result == [
        {
            "id": "8f14e45f-ceea-467e-bd25-7b90b1c3f9f0",
            "content": "hello world",
            "posted_at": "2026-08-01T12:00:00Z",
            "channel_url": "https://t.me/somechannel",
            "url": "https://t.me/somechannel/1",
        }
    ]


async def test_retrieve_posts_sends_query_as_form_field(httpx_mock):
    httpx_mock.add_response(url=f"{BASE_URL}/rag/retrieve", method="POST", json=[])

    await retrieve_posts("my query", BASE_URL)

    request = httpx_mock.get_requests()[0]
    assert request.read() == b"query=my+query"


async def test_retrieve_posts_raises_on_connection_error(httpx_mock):
    httpx_mock.add_exception(httpx.ConnectError("connection refused"))

    with pytest.raises(RagApiError, match="Could not reach RAG API"):
        await retrieve_posts("hello", BASE_URL)


async def test_retrieve_posts_raises_on_http_error(httpx_mock):
    httpx_mock.add_response(
        url=f"{BASE_URL}/rag/retrieve",
        method="POST",
        status_code=500,
        text="internal error",
    )

    with pytest.raises(RagApiError, match="RAG API returned error 500"):
        await retrieve_posts("hello", BASE_URL)

import httpx


class RagApiError(RuntimeError):
    """Raised when the telegramrag RAG API cannot be reached or returns an error."""


async def retrieve_posts(query: str, base_url: str) -> list[dict]:
    """Call POST {base_url}/rag/retrieve and return the parsed JSON list of posts."""
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        try:
            response = await client.post('/rag/retrieve', data={'query': query})
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RagApiError(f'RAG API returned error {exc.response.status_code}: {exc.response.text}') from exc
        except httpx.RequestError as exc:
            raise RagApiError(
                f'Could not reach RAG API at {base_url}. Is it running? '
                'Start it with `uv run uvicorn app.main:app` or `docker compose up`.'
            ) from exc

    return response.json()


async def fetch_posts_by_username(username: str, start_date: str, end_date: str, base_url: str) -> list[dict]:
    """Call GET {base_url}/telegram/posts/by-username and return the parsed JSON list of posts."""
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        try:
            response = await client.get(
                '/telegram/posts/by-username',
                params={'username': username, 'start_date': start_date, 'end_date': end_date},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RagApiError(f'RAG API returned error {exc.response.status_code}: {exc.response.text}') from exc
        except httpx.RequestError as exc:
            raise RagApiError(
                f'Could not reach RAG API at {base_url}. Is it running? '
                'Start it with `uv run uvicorn app.main:app` or `docker compose up`.'
            ) from exc

    return response.json()


async def search_channels_by_keywords(keywords: str, base_url: str) -> list[dict]:
    """Call GET {base_url}/telegram/channels/search-by-keywords and return the parsed JSON list of channels."""
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        try:
            response = await client.get('/telegram/channels/search-by-keywords', params={'keywords': keywords})
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RagApiError(f'RAG API returned error {exc.response.status_code}: {exc.response.text}') from exc
        except httpx.RequestError as exc:
            raise RagApiError(
                f'Could not reach RAG API at {base_url}. Is it running? '
                'Start it with `uv run uvicorn app.main:app` or `docker compose up`.'
            ) from exc

    return response.json()

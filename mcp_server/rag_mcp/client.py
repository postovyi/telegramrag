import httpx


class RagApiError(RuntimeError):
    """Raised when the telegramrag RAG API cannot be reached or returns an error."""


async def fetch_posts_by_username(username: str, start_date: str, end_date: str, base_url: str) -> list[dict]:
    """Call GET {base_url}/telegram/preview/posts/by-username and return the parsed JSON list of posts."""
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        try:
            response = await client.get(
                '/telegram/preview/posts/by-username',
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


async def fetch_posts_by_usernames(usernames: list[str], start_date: str, end_date: str, base_url: str) -> list[dict]:
    """Call POST {base_url}/telegram/preview/posts/by-usernames and return the parsed JSON list of posts."""
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        try:
            response = await client.post(
                '/telegram/preview/posts/by-usernames',
                json={'usernames': usernames, 'start_date': start_date, 'end_date': end_date},
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


async def fetch_post_by_link(url: str, base_url: str) -> dict:
    """Call GET {base_url}/telegram/preview/posts/by-link and return the parsed JSON post."""
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        try:
            response = await client.get('/telegram/preview/posts/by-link', params={'url': url})
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
    """Call GET {base_url}/telegram/preview/channels/search-by-keywords and return the parsed JSON list."""
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        try:
            response = await client.get('/telegram/preview/channels/search-by-keywords', params={'keywords': keywords})
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RagApiError(f'RAG API returned error {exc.response.status_code}: {exc.response.text}') from exc
        except httpx.RequestError as exc:
            raise RagApiError(
                f'Could not reach RAG API at {base_url}. Is it running? '
                'Start it with `uv run uvicorn app.main:app` or `docker compose up`.'
            ) from exc

    return response.json()


async def fetch_channel_by_username(username: str, base_url: str) -> dict:
    """Call GET {base_url}/telegram/preview/channels/by-username and return the parsed JSON channel."""
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        try:
            response = await client.get('/telegram/preview/channels/by-username', params={'username': username})
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RagApiError(f'RAG API returned error {exc.response.status_code}: {exc.response.text}') from exc
        except httpx.RequestError as exc:
            raise RagApiError(
                f'Could not reach RAG API at {base_url}. Is it running? '
                'Start it with `uv run uvicorn app.main:app` or `docker compose up`.'
            ) from exc

    return response.json()

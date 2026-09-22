import os

from mcp.server.fastmcp import FastMCP

from rag_mcp.client import RagApiError, fetch_posts_by_username, retrieve_posts, search_channels_by_keywords

DEFAULT_BASE_URL = 'http://localhost:8000'

mcp = FastMCP('telegramrag')


def _base_url() -> str:
    return os.environ.get('RAG_API_BASE_URL', DEFAULT_BASE_URL)


async def retrieve_posts_tool(query: str) -> str:
    """Retrieve Telegram posts relevant to `query` from the telegramrag RAG API."""
    try:
        posts = await retrieve_posts(query, _base_url())
    except RagApiError as exc:
        return f'Error: {exc}'

    if not posts:
        return 'No relevant posts found.'

    return '\n'.join(f'- [{post["posted_at"]}] {post["url"]}\n  {post["content"] or "(no text)"}' for post in posts)


async def fetch_posts_by_username_tool(username: str, start_date: str, end_date: str) -> str:
    """Fetch a Telegram channel's posts within a date range, scraped live by username.

    This scrapes the channel directly via Telegram at call time — it does NOT read from or
    write to the telegramrag database. No post or channel row is created as a side effect.
    Use this to preview a channel's post history; it is unrelated to the RAG-indexed
    `retrieve_posts` tool, which only searches posts already imported into the database.

    Args:
        username: The channel's Telegram username, without the leading `@` (e.g. `telegram`,
            not `@telegram` or a `t.me/...` URL).
        start_date: Start of the date range (inclusive), ISO 8601 (e.g. `2024-01-01T00:00:00`).
        end_date: End of the date range (inclusive), ISO 8601 (e.g. `2024-12-31T23:59:59`).

    Returns only text content — media is never downloaded. Posts with no text (media-only,
    no caption) are still included, shown as "(no text)".
    """
    try:
        posts = await fetch_posts_by_username(username, start_date, end_date, _base_url())
    except RagApiError as exc:
        return f'Error: {exc}'

    if not posts:
        return 'No posts found in that range.'

    return '\n'.join(f'- [{post["posted_at"]}] {post["url"]}\n  {post["content"] or "(no text)"}' for post in posts)


async def search_channels_by_keywords_tool(keywords: str) -> list[dict]:
    """Search public Telegram channels by keyword and return candidates ranked by subscriber count.

    This searches Telegram directly at call time — it does NOT read from or write to the
    telegramrag database, and it does NOT make the results available to `retrieve_posts` or
    any other RAG tool. Use it to discover or compare channels by size before deciding what
    (if anything) to import elsewhere; it does not import or persist anything itself.

    Args:
        keywords: Free-text search terms matched against channel titles/usernames.

    Returns a list of `{"name": str, "username": str, "subscribers_count": int}`, sorted by
    `subscribers_count` descending. The number of results is fixed by server-side
    configuration (`TELEGRAM_CHANNEL_SEARCH_LIMIT` on the telegramrag API) — it is not a
    parameter of this tool and cannot be overridden per call.
    """
    return await search_channels_by_keywords(keywords, _base_url())


mcp.tool(name='retrieve_posts')(retrieve_posts_tool)
mcp.tool(name='fetch_posts_by_username')(fetch_posts_by_username_tool)
mcp.tool(name='search_channels_by_keywords')(search_channels_by_keywords_tool)


def main() -> None:
    mcp.run()


if __name__ == '__main__':
    main()

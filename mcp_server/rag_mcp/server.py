import functools
import os
from collections.abc import Awaitable, Callable
from typing import ParamSpec

from mcp.server.fastmcp import FastMCP

from rag_mcp.client import (
    RagApiError,
    fetch_channel_by_username,
    fetch_post_by_link,
    fetch_posts_by_username,
    fetch_posts_by_usernames,
    search_channels_by_keywords,
)

DEFAULT_BASE_URL = 'http://localhost:8000'
DEFAULT_MAX_OUTPUT_CHARS = 80000
ENTRY_SEPARATOR = '\n- ['

P = ParamSpec('P')

mcp = FastMCP('telegramrag')


def _base_url() -> str:
    return os.environ.get('RAG_API_BASE_URL', DEFAULT_BASE_URL)


def _max_output_chars() -> int:
    raw = os.environ.get('MCP_MAX_OUTPUT_CHARS', '').strip()
    if not raw:
        return DEFAULT_MAX_OUTPUT_CHARS
    try:
        return max(int(raw), 0)
    except ValueError:
        return DEFAULT_MAX_OUTPUT_CHARS


def _truncate(text: str, cap: int) -> str:
    if len(text) <= cap:
        return text
    boundary = text.rfind(ENTRY_SEPARATOR, 0, cap + len(ENTRY_SEPARATOR))
    return text[:boundary] if boundary > 0 else text[:cap]


def limit_output(fn: Callable[P, Awaitable]) -> Callable[P, Awaitable]:
    """Cap the length of a tool's ``str`` result to ``MCP_MAX_OUTPUT_CHARS`` (``0`` = unlimited).

    Cuts on a post-entry boundary when possible, otherwise by characters. Non-``str`` results pass through.
    """

    @functools.wraps(fn)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> object:
        result = await fn(*args, **kwargs)
        cap = _max_output_chars()
        if isinstance(result, str) and cap:
            return _truncate(result, cap)
        return result

    return wrapper


async def fetch_posts_by_username_tool(username: str, start_date: str, end_date: str) -> str:
    """Fetch a Telegram channel's posts within a date range, scraped live by username.

    This scrapes the channel directly via Telegram at call time — it does NOT read from or
    write to the telegramrag database. No post or channel row is created as a side effect.
    Use this to preview a channel's post history.

    Args:
        username: The channel's Telegram username, without the leading `@` (e.g. `telegram`,
            not `@telegram` or a `t.me/...` URL).
        start_date: Start of the date range (inclusive), ISO 8601 (e.g. `2024-01-01T00:00:00`).
        end_date: End of the date range (inclusive), ISO 8601 (e.g. `2024-12-31T23:59:59`).

    Returns only text content — media is never downloaded. Posts with no text (media-only,
    no caption) are still included, shown as "(no text)".

    Output length is capped by server-side configuration (`MCP_MAX_OUTPUT_CHARS`); it is not a
    per-call parameter. For long ranges the listing may be cut off at the end — narrow the
    date range if posts seem to be missing.
    """
    try:
        posts = await fetch_posts_by_username(username, start_date, end_date, _base_url())
    except RagApiError as exc:
        return f'Error: {exc}'

    if not posts:
        return 'No posts found in that range.'

    return '\n'.join(f'- [{post["posted_at"]}] {post["url"]}\n  {post["content"] or "(no text)"}' for post in posts)


async def fetch_posts_by_usernames_tool(usernames: list[str], start_date: str, end_date: str) -> str:
    """Fetch posts within a date range across multiple Telegram channels, scraped live by username.

    This scrapes the channels directly via Telegram at call time — it does NOT read from or
    write to the telegramrag database. No post or channel row is created as a side effect.
    A username that fails to resolve (not found, private, scrape error) is silently skipped
    rather than failing the whole call. Use this to compare content across several channels
    before deciding what (if anything) to import.

    Args:
        usernames: The channels' Telegram usernames, without the leading `@`.
        start_date: Start of the date range (inclusive), ISO 8601 (e.g. `2024-01-01T00:00:00`).
        end_date: End of the date range (inclusive), ISO 8601 (e.g. `2024-12-31T23:59:59`).

    Returns only text content — media is never downloaded. Posts with no text (media-only,
    no caption) are still included, shown as "(no text)".

    Output length is capped by server-side configuration (`MCP_MAX_OUTPUT_CHARS`); it is not a
    per-call parameter. For long ranges the listing may be cut off at the end — narrow the
    date range if posts seem to be missing.
    """
    try:
        posts = await fetch_posts_by_usernames(usernames, start_date, end_date, _base_url())
    except RagApiError as exc:
        return f'Error: {exc}'

    if not posts:
        return 'No posts found in that range.'

    return '\n'.join(
        f'- [{post["posted_at"]}] {post["channel_username"]} — {post["url"]}\n  {post["content"] or "(no text)"}'
        for post in posts
    )


async def fetch_post_by_link_tool(url: str) -> str:
    """Fetch a single Telegram post by its public post link, scraped live.

    This fetches the post directly via Telegram at call time — it does NOT read from or
    write to the telegramrag database. No post or channel row is created as a side effect.

    Args:
        url: A public post link in the form `https://t.me/<username>/<message_id>`. Private/
            internal channel links (`t.me/c/...`) and invite links are not supported.

    Returns only text content — media is never downloaded. A post with no text (media-only,
    no caption) is still returned, shown as "(no text)". The result includes the channel's
    display name (falling back to its username if the name can't be resolved).

    Output length is capped by server-side configuration (`MCP_MAX_OUTPUT_CHARS`); it is not a
    per-call parameter.
    """
    try:
        post = await fetch_post_by_link(url, _base_url())
    except RagApiError as exc:
        return f'Error: {exc}'

    channel_name = post.get('channel_name') or post['channel_username']
    return f'- [{post["posted_at"]}] {channel_name} — {post["url"]}\n  {post["content"] or "(no text)"}'


async def search_channels_by_keywords_tool(keywords: str) -> list[dict]:
    """Search public Telegram channels by keyword and return candidates ranked by subscriber count.

    This searches Telegram directly at call time — it does NOT read from or write to the
    telegramrag database. Use it to discover or compare channels by size before deciding what
    (if anything) to import elsewhere; it does not import or persist anything itself.

    Args:
        keywords: Free-text search terms matched against channel titles/usernames.

    Returns a list of `{"name": str, "username": str, "subscribers_count": int}`, sorted by
    `subscribers_count` descending. The number of results is fixed by server-side
    configuration (`TELEGRAM_CHANNEL_SEARCH_LIMIT` on the telegramrag API) — it is not a
    parameter of this tool and cannot be overridden per call.
    """
    return await search_channels_by_keywords(keywords, _base_url())


async def fetch_channel_by_username_tool(username: str) -> str:
    """Fetch a single Telegram channel's info and subscriber count, live, by username.

    This fetches the channel directly via Telegram at call time — it does NOT read from or
    write to the telegramrag database. No channel row is created as a side effect. Use this
    to preview a channel before deciding whether to import it.

    Args:
        username: The channel's Telegram username, without the leading `@` (e.g. `telegram`,
            not `@telegram` or a `t.me/...` URL).

    Returns the channel's name, username, and subscriber count.
    """
    try:
        channel = await fetch_channel_by_username(username, _base_url())
    except RagApiError as exc:
        return f'Error: {exc}'

    return f'{channel["name"]} (@{channel["username"]}) — {channel["subscribers_count"]} subscribers'


mcp.tool(name='fetch_posts_by_username')(limit_output(fetch_posts_by_username_tool))
mcp.tool(name='fetch_posts_by_usernames')(limit_output(fetch_posts_by_usernames_tool))
mcp.tool(name='fetch_post_by_link')(limit_output(fetch_post_by_link_tool))
mcp.tool(name='search_channels_by_keywords')(search_channels_by_keywords_tool)
mcp.tool(name='fetch_channel_by_username')(limit_output(fetch_channel_by_username_tool))


def main() -> None:
    transport = os.environ.get('MCP_TRANSPORT', 'stdio')
    if transport == 'streamable-http':
        mcp.settings.host = os.environ.get('MCP_HOST', '127.0.0.1')
        mcp.settings.port = int(os.environ.get('MCP_PORT', '8002'))
    mcp.run(transport=transport)


if __name__ == '__main__':
    main()

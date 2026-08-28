import os

from mcp.server.fastmcp import FastMCP

from rag_mcp.client import RagApiError, retrieve_posts

DEFAULT_BASE_URL = "http://localhost:8000"

mcp = FastMCP("telegramrag")


def _base_url() -> str:
    return os.environ.get("RAG_API_BASE_URL", DEFAULT_BASE_URL)


async def retrieve_posts_tool(query: str) -> str:
    """Retrieve Telegram posts relevant to `query` from the telegramrag RAG API."""
    try:
        posts = await retrieve_posts(query, _base_url())
    except RagApiError as exc:
        return f"Error: {exc}"

    if not posts:
        return "No relevant posts found."

    return "\n".join(
        f"- [{post['posted_at']}] {post['url']}\n  {post['content']}" for post in posts
    )


mcp.tool(name="retrieve_posts")(retrieve_posts_tool)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

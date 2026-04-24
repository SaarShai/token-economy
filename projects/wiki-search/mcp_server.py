#!/usr/bin/env python3
"""MCP server for Token Economy wiki-search.

Requires `mcp` package. The core retrieval API has no external dependencies.
"""
from __future__ import annotations

from wiki_search import wiki_fetch, wiki_search, wiki_timeline

try:
    from mcp.server.fastmcp import FastMCP
except Exception as exc:  # pragma: no cover - optional runtime dependency
    raise SystemExit(f"mcp package unavailable: {exc}")


mcp = FastMCP("token-economy-wiki-search")


@mcp.tool()
def wiki_search_tool(query: str, k: int = 10) -> list[dict]:
    """Tier 1: compact search hits."""
    return wiki_search(query, k)


@mcp.tool()
def wiki_timeline_tool(item_id: str, window: int = 3) -> dict:
    """Tier 2: backlinks, neighbors, and log context."""
    return wiki_timeline(item_id, window)


@mcp.tool()
def wiki_fetch_tool(item_id: str) -> dict:
    """Tier 3: fetch one full page after relevance is established."""
    return wiki_fetch(item_id)


if __name__ == "__main__":
    mcp.run()


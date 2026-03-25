"""MCP tool for Brazilian legislation search."""

from typing import Any, Optional

from ..client import get_client


async def search_legislation(
    q: str,
    area: Optional[str] = None,
    tipo: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
) -> dict:
    """
    Search Brazilian legislation loaded from LexML.

    Args:
        q: Search query (full-text search over title and content).
        area: Legal area filter (e.g. "trabalhista", "previdenciario", "civel").
        tipo: Document type filter (e.g. "lei", "decreto", "constituicao").
        skip: Pagination offset.
        limit: Maximum results (max 50).
    """
    params: dict[str, Any] = {"q": q, "skip": skip, "limit": min(limit, 50)}
    if area:
        params["area"] = area
    if tipo:
        params["tipo"] = tipo

    client = get_client()
    return await client.get("/api/legislacao", params=params)

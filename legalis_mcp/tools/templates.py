"""MCP tools for legal document templates."""

from typing import Any, Optional

from ..client import get_client


async def list_templates(
    skip: int = 0,
    limit: int = 20,
) -> dict:
    """
    List available legal document templates.

    Args:
        skip: Pagination offset.
        limit: Maximum number of templates to return (max 100).
    """
    params: dict[str, Any] = {"skip": skip, "limit": min(limit, 100)}
    client = get_client()
    return await client.get("/api/templates", params=params)


async def get_template(template_id: str) -> dict:
    """
    Get details of a specific legal document template, including its sections.

    Args:
        template_id: UUID of the template.
    """
    client = get_client()
    return await client.get(f"/api/templates/{template_id}")

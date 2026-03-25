"""MCP tool for quota and usage reporting."""

from ..client import get_client


async def get_my_usage() -> dict:
    """
    Get the current user's AI usage, quota, and billing period information.

    Returns current period usage, remaining quota, plan details, and cost breakdown.
    """
    client = get_client()
    return await client.get("/api/plans/my-usage")

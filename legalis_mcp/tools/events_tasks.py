"""MCP tools for case events and tasks."""

from typing import Any, Optional

from ..client import get_client


async def create_case_event(
    case_id: str,
    title: str,
    visibility: str,
    description: Optional[str] = None,
    event_type: str = "manual",
) -> dict:
    """
    Create a new event on a case.

    Args:
        case_id: UUID of the case.
        title: Event title.
        visibility: Visibility scope — "internal" (visible only to the team)
            or "external" (visible to the client).
        description: Optional event description.
        event_type: Event type (default "manual").
    """
    payload: dict[str, Any] = {
        "title": title,
        "visibility": visibility,
        "event_type": event_type,
    }
    if description:
        payload["description"] = description

    client = get_client()
    return await client.post(f"/api/cases/{case_id}/events", json=payload)


async def create_case_task(
    case_id: str,
    title: str,
    due_date: str,
    priority: str = "medium",
    description: Optional[str] = None,
    recurrence: str = "none",
    create_external_event: bool = False,
) -> dict:
    """
    Create a new task on a case.

    Args:
        case_id: UUID of the case.
        title: Task title.
        due_date: Due date/time in ISO 8601 format (e.g. "2026-04-01T10:00:00").
        priority: Task priority — "low", "medium", "high", or "urgent" (default "medium").
        description: Optional task description.
        recurrence: Recurrence rule — "none", "daily", "weekly", "monthly", or "yearly"
            (default "none").
        create_external_event: Whether to create a corresponding external event
            (default False).
    """
    payload: dict[str, Any] = {
        "title": title,
        "due_date": due_date,
        "priority": priority,
        "recurrence": recurrence,
        "create_external_event": create_external_event,
    }
    if description:
        payload["description"] = description

    client = get_client()
    return await client.post(f"/api/cases/{case_id}/tasks", json=payload)


async def list_case_events(
    case_id: str,
    visibility: Optional[str] = None,
) -> dict:
    """
    List events for a case.

    Args:
        case_id: UUID of the case.
        visibility: Optional filter — "internal" or "external". If omitted, all events
            are returned.
    """
    params: dict[str, Any] = {}
    if visibility:
        params["visibility"] = visibility

    client = get_client()
    return await client.get(f"/api/cases/{case_id}/events", params=params or None)


async def list_upcoming_tasks(days: int = 7) -> dict:
    """
    List upcoming tasks across all of the user's cases.

    Args:
        days: Number of days ahead to look for tasks (default 7).
    """
    params: dict[str, Any] = {"days": days}
    client = get_client()
    return await client.get("/api/tasks/upcoming", params=params)


async def list_overdue_tasks() -> dict:
    """List all overdue tasks across the user's cases."""
    client = get_client()
    return await client.get("/api/tasks/overdue")


async def list_case_tasks(case_id: str) -> dict:
    """
    List tasks for a specific case.

    Args:
        case_id: UUID of the case.
    """
    client = get_client()
    return await client.get(f"/api/cases/{case_id}/tasks")


async def update_case_task(
    case_id: str,
    task_id: str,
    title: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[str] = None,
    description: Optional[str] = None,
    recurrence: Optional[str] = None,
) -> dict:
    """
    Update an existing task on a case.

    Args:
        case_id: UUID of the case.
        task_id: UUID of the task.
        title: New task title (optional).
        due_date: New due date in ISO 8601 format (optional).
        priority: New priority — "low", "medium", "high", or "urgent" (optional).
        description: New description (optional).
        recurrence: New recurrence rule — "none", "daily", "weekly", "monthly", or "yearly"
            (optional).
    """
    payload: dict[str, Any] = {}
    for field, value in [
        ("title", title),
        ("due_date", due_date),
        ("priority", priority),
        ("description", description),
        ("recurrence", recurrence),
    ]:
        if value is not None:
            payload[field] = value

    client = get_client()
    return await client.put(f"/api/cases/{case_id}/tasks/{task_id}", json=payload)


async def complete_case_task(case_id: str, task_id: str) -> dict:
    """
    Mark a task as complete.

    Args:
        case_id: UUID of the case.
        task_id: UUID of the task to complete.
    """
    client = get_client()
    return await client.post(f"/api/cases/{case_id}/tasks/{task_id}/complete", json={})


async def delete_case_task(case_id: str, task_id: str) -> dict:
    """
    Delete a task from a case.

    Args:
        case_id: UUID of the case.
        task_id: UUID of the task to delete.
    """
    client = get_client()
    return await client.delete(f"/api/cases/{case_id}/tasks/{task_id}")


async def delete_case_event(case_id: str, event_id: str) -> dict:
    """
    Delete an event from a case.

    Args:
        case_id: UUID of the case.
        event_id: UUID of the event to delete.
    """
    client = get_client()
    return await client.delete(f"/api/cases/{case_id}/events/{event_id}")

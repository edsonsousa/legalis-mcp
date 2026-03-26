"""Unit tests for case events and tasks tools."""

import json
import pytest
import respx
import httpx

from legalis_mcp.auth import Credentials
from legalis_mcp.client import LegalisClient

BASE = "https://hai-production-612f.up.railway.app"
CASE_ID = "case-abc-123"


def _mock_client():
    return LegalisClient(credentials=Credentials("tok", "ref"))


@pytest.fixture(autouse=True)
def patch_get_client(monkeypatch):
    """Patch get_client in tools so tests control the HTTP client."""
    client = _mock_client()
    monkeypatch.setattr(
        "legalis_mcp.tools.events_tasks.get_client", lambda: client
    )
    return client


# ---------------------------------------------------------------------------
# create_case_event
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_create_case_event_sends_required_fields():
    route = respx.post(f"{BASE}/api/cases/{CASE_ID}/events").mock(
        return_value=httpx.Response(201, json={"id": "evt-1", "title": "Audiência"})
    )
    from legalis_mcp.tools.events_tasks import create_case_event

    result = await create_case_event(
        case_id=CASE_ID, title="Audiência", visibility="internal"
    )
    assert result["id"] == "evt-1"
    payload = json.loads(route.calls[0].request.read())
    assert payload["title"] == "Audiência"
    assert payload["visibility"] == "internal"
    assert payload["event_type"] == "manual"


@pytest.mark.asyncio
@respx.mock
async def test_create_case_event_with_description():
    route = respx.post(f"{BASE}/api/cases/{CASE_ID}/events").mock(
        return_value=httpx.Response(201, json={"id": "evt-2"})
    )
    from legalis_mcp.tools.events_tasks import create_case_event

    await create_case_event(
        case_id=CASE_ID,
        title="Despacho",
        visibility="external",
        description="Despacho recebido pelo juízo.",
        event_type="system",
    )
    payload = json.loads(route.calls[0].request.read())
    assert payload["description"] == "Despacho recebido pelo juízo."
    assert payload["visibility"] == "external"
    assert payload["event_type"] == "system"


@pytest.mark.asyncio
@respx.mock
async def test_create_case_event_omits_description_when_none():
    route = respx.post(f"{BASE}/api/cases/{CASE_ID}/events").mock(
        return_value=httpx.Response(201, json={"id": "evt-3"})
    )
    from legalis_mcp.tools.events_tasks import create_case_event

    await create_case_event(case_id=CASE_ID, title="T", visibility="internal")
    payload = json.loads(route.calls[0].request.read())
    assert "description" not in payload


@pytest.mark.asyncio
@respx.mock
async def test_create_case_event_api_error():
    respx.post(f"{BASE}/api/cases/{CASE_ID}/events").mock(
        return_value=httpx.Response(404, json={"detail": "Case not found"})
    )
    from legalis_mcp.tools.events_tasks import create_case_event

    with pytest.raises(RuntimeError, match="404"):
        await create_case_event(case_id=CASE_ID, title="T", visibility="internal")


# ---------------------------------------------------------------------------
# create_case_task
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_create_case_task_sends_required_fields():
    route = respx.post(f"{BASE}/api/cases/{CASE_ID}/tasks").mock(
        return_value=httpx.Response(
            201, json={"id": "task-1", "title": "Protocolar recurso"}
        )
    )
    from legalis_mcp.tools.events_tasks import create_case_task

    result = await create_case_task(
        case_id=CASE_ID,
        title="Protocolar recurso",
        due_date="2026-04-01T10:00:00",
    )
    assert result["id"] == "task-1"
    payload = json.loads(route.calls[0].request.read())
    assert payload["title"] == "Protocolar recurso"
    assert payload["due_date"] == "2026-04-01T10:00:00"
    assert payload["priority"] == "medium"
    assert payload["recurrence"] == "none"
    assert payload["create_external_event"] is False


@pytest.mark.asyncio
@respx.mock
async def test_create_case_task_custom_priority_and_recurrence():
    route = respx.post(f"{BASE}/api/cases/{CASE_ID}/tasks").mock(
        return_value=httpx.Response(201, json={"id": "task-2"})
    )
    from legalis_mcp.tools.events_tasks import create_case_task

    await create_case_task(
        case_id=CASE_ID,
        title="Prazo mensal",
        due_date="2026-04-01T09:00:00",
        priority="high",
        recurrence="monthly",
        create_external_event=True,
    )
    payload = json.loads(route.calls[0].request.read())
    assert payload["priority"] == "high"
    assert payload["recurrence"] == "monthly"
    assert payload["create_external_event"] is True


@pytest.mark.asyncio
@respx.mock
async def test_create_case_task_with_description():
    route = respx.post(f"{BASE}/api/cases/{CASE_ID}/tasks").mock(
        return_value=httpx.Response(201, json={"id": "task-3"})
    )
    from legalis_mcp.tools.events_tasks import create_case_task

    await create_case_task(
        case_id=CASE_ID,
        title="Tarefa",
        due_date="2026-04-10T00:00:00",
        description="Verificar prazo recursal.",
    )
    payload = json.loads(route.calls[0].request.read())
    assert payload["description"] == "Verificar prazo recursal."


@pytest.mark.asyncio
@respx.mock
async def test_create_case_task_omits_description_when_none():
    route = respx.post(f"{BASE}/api/cases/{CASE_ID}/tasks").mock(
        return_value=httpx.Response(201, json={"id": "task-4"})
    )
    from legalis_mcp.tools.events_tasks import create_case_task

    await create_case_task(
        case_id=CASE_ID, title="T", due_date="2026-04-01T00:00:00"
    )
    payload = json.loads(route.calls[0].request.read())
    assert "description" not in payload


@pytest.mark.asyncio
@respx.mock
async def test_create_case_task_api_error():
    respx.post(f"{BASE}/api/cases/{CASE_ID}/tasks").mock(
        return_value=httpx.Response(422, json={"detail": "Validation error"})
    )
    from legalis_mcp.tools.events_tasks import create_case_task

    with pytest.raises(RuntimeError, match="422"):
        await create_case_task(
            case_id=CASE_ID, title="T", due_date="2026-04-01T00:00:00"
        )


# ---------------------------------------------------------------------------
# list_case_events
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_list_case_events_returns_all_when_no_filter():
    respx.get(f"{BASE}/api/cases/{CASE_ID}/events").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {"id": "e1", "title": "Audiência", "visibility": "internal"},
                    {"id": "e2", "title": "Notificação", "visibility": "external"},
                ],
                "total": 2,
            },
        )
    )
    from legalis_mcp.tools.events_tasks import list_case_events

    result = await list_case_events(case_id=CASE_ID)
    assert result["total"] == 2


@pytest.mark.asyncio
@respx.mock
async def test_list_case_events_filters_by_visibility():
    route = respx.get(f"{BASE}/api/cases/{CASE_ID}/events").mock(
        return_value=httpx.Response(
            200,
            json={"items": [{"id": "e1", "visibility": "internal"}], "total": 1},
        )
    )
    from legalis_mcp.tools.events_tasks import list_case_events

    result = await list_case_events(case_id=CASE_ID, visibility="internal")
    assert result["total"] == 1
    assert "visibility=internal" in str(route.calls[0].request.url)


@pytest.mark.asyncio
@respx.mock
async def test_list_case_events_no_visibility_param_in_url():
    route = respx.get(f"{BASE}/api/cases/{CASE_ID}/events").mock(
        return_value=httpx.Response(200, json={"items": [], "total": 0})
    )
    from legalis_mcp.tools.events_tasks import list_case_events

    await list_case_events(case_id=CASE_ID)
    assert "visibility" not in str(route.calls[0].request.url)


@pytest.mark.asyncio
@respx.mock
async def test_list_case_events_api_error():
    respx.get(f"{BASE}/api/cases/{CASE_ID}/events").mock(
        return_value=httpx.Response(403, json={"detail": "Forbidden"})
    )
    from legalis_mcp.tools.events_tasks import list_case_events

    with pytest.raises(RuntimeError, match="403"):
        await list_case_events(case_id=CASE_ID)


# ---------------------------------------------------------------------------
# list_upcoming_tasks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_list_upcoming_tasks_default_days():
    route = respx.get(f"{BASE}/api/tasks/upcoming").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": "t1",
                        "title": "Protocolar recurso",
                        "due_date": "2026-03-30T10:00:00",
                        "priority": "high",
                        "case_id": CASE_ID,
                    }
                ],
                "total": 1,
            },
        )
    )
    from legalis_mcp.tools.events_tasks import list_upcoming_tasks

    result = await list_upcoming_tasks()
    assert result["total"] == 1
    assert result["items"][0]["id"] == "t1"
    assert "days=7" in str(route.calls[0].request.url)


@pytest.mark.asyncio
@respx.mock
async def test_list_upcoming_tasks_custom_days():
    route = respx.get(f"{BASE}/api/tasks/upcoming").mock(
        return_value=httpx.Response(200, json={"items": [], "total": 0})
    )
    from legalis_mcp.tools.events_tasks import list_upcoming_tasks

    await list_upcoming_tasks(days=30)
    assert "days=30" in str(route.calls[0].request.url)


@pytest.mark.asyncio
@respx.mock
async def test_list_upcoming_tasks_api_error():
    respx.get(f"{BASE}/api/tasks/upcoming").mock(
        return_value=httpx.Response(500, json={"detail": "Internal server error"})
    )
    from legalis_mcp.tools.events_tasks import list_upcoming_tasks

    with pytest.raises(RuntimeError, match="500"):
        await list_upcoming_tasks()

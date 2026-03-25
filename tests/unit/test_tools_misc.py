"""Unit tests for legislation, interview, and usage tools."""

import json
import pytest
import respx
import httpx

from legalis_mcp.auth import Credentials
from legalis_mcp.client import LegalisClient

BASE = "https://hai-production-612f.up.railway.app"
CASE_ID = "case-123"


def _mock_client():
    return LegalisClient(credentials=Credentials("tok", "ref"))


@pytest.fixture(autouse=True)
def patch_get_client(monkeypatch):
    client = _mock_client()
    monkeypatch.setattr("legalis_mcp.tools.legislation.get_client", lambda: client)
    monkeypatch.setattr("legalis_mcp.tools.interview.get_client", lambda: client)
    monkeypatch.setattr("legalis_mcp.tools.usage.get_client", lambda: client)
    return client


# ---------------------------------------------------------------------------
# legislation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_search_legislation_passes_query():
    route = respx.get(f"{BASE}/api/legislacao").mock(
        return_value=httpx.Response(200, json={"items": [], "total": 0})
    )
    from legalis_mcp.tools.legislation import search_legislation

    await search_legislation(q="CLT art 482")
    assert "q=" in str(route.calls[0].request.url)


@pytest.mark.asyncio
@respx.mock
async def test_search_legislation_clamps_limit():
    route = respx.get(f"{BASE}/api/legislacao").mock(
        return_value=httpx.Response(200, json={"items": [], "total": 0})
    )
    from legalis_mcp.tools.legislation import search_legislation

    await search_legislation(q="lei", limit=200)
    assert "limit=50" in str(route.calls[0].request.url)


@pytest.mark.asyncio
@respx.mock
async def test_search_legislation_passes_area_filter():
    route = respx.get(f"{BASE}/api/legislacao").mock(
        return_value=httpx.Response(200, json={"items": []})
    )
    from legalis_mcp.tools.legislation import search_legislation

    await search_legislation(q="demissão", area="trabalhista")
    assert "area=trabalhista" in str(route.calls[0].request.url)


# ---------------------------------------------------------------------------
# interview
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_run_interview_start():
    route = respx.post(f"{BASE}/api/interview/start").mock(
        return_value=httpx.Response(
            200, json={"session_id": "sess-1", "questions": []}
        )
    )
    from legalis_mcp.tools.interview import run_interview

    result = await run_interview(CASE_ID, action="start")
    assert result["session_id"] == "sess-1"
    payload = json.loads(route.calls[0].request.read())
    assert payload["case_id"] == CASE_ID


@pytest.mark.asyncio
@respx.mock
async def test_run_interview_answer():
    route = respx.post(f"{BASE}/api/interview/answers").mock(
        return_value=httpx.Response(200, json={"next_questions": []})
    )
    from legalis_mcp.tools.interview import run_interview

    await run_interview(
        CASE_ID,
        action="answer",
        answers={"q1": "Sim"},
        session_id="sess-1",
    )
    assert route.called


@pytest.mark.asyncio
async def test_run_interview_answer_requires_session_id():
    from legalis_mcp.tools.interview import run_interview

    with pytest.raises(ValueError, match="session_id"):
        await run_interview(CASE_ID, action="answer", answers={"q1": "x"})


@pytest.mark.asyncio
@respx.mock
async def test_run_interview_complete():
    route = respx.post(f"{BASE}/api/interview/complete").mock(
        return_value=httpx.Response(200, json={"status": "completed"})
    )
    from legalis_mcp.tools.interview import run_interview

    await run_interview(CASE_ID, action="complete", session_id="sess-1")
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_run_interview_status():
    route = respx.get(f"{BASE}/api/interview").mock(
        return_value=httpx.Response(200, json={"status": "in_progress"})
    )
    from legalis_mcp.tools.interview import run_interview

    result = await run_interview(CASE_ID, action="status")
    assert result["status"] == "in_progress"


@pytest.mark.asyncio
async def test_run_interview_unknown_action():
    from legalis_mcp.tools.interview import run_interview

    with pytest.raises(ValueError, match="Unknown action"):
        await run_interview(CASE_ID, action="fly")


# ---------------------------------------------------------------------------
# usage
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_get_my_usage():
    respx.get(f"{BASE}/api/plans/my-usage").mock(
        return_value=httpx.Response(
            200,
            json={
                "used": 5,
                "limit": 50,
                "remaining": 45,
                "period_end": "2026-04-01",
            },
        )
    )
    from legalis_mcp.tools.usage import get_my_usage

    result = await get_my_usage()
    assert result["remaining"] == 45

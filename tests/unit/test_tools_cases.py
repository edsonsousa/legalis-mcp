"""Unit tests for case management tools."""

import json
import pytest
import respx
import httpx

from legalis_mcp.auth import Credentials
from legalis_mcp.client import LegalisClient

BASE = "https://hai-production-612f.up.railway.app"


def _mock_client():
    return LegalisClient(credentials=Credentials("tok", "ref"))


@pytest.fixture(autouse=True)
def patch_get_client(monkeypatch):
    """Patch get_client in tools so tests control the HTTP client."""
    client = _mock_client()
    monkeypatch.setattr("legalis_mcp.tools.cases.get_client", lambda: client)
    return client


# ---------------------------------------------------------------------------
# list_cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_list_cases_returns_items():
    respx.get(f"{BASE}/api/cases").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [{"id": "c1", "titulo": "Caso 1"}],
                "total": 1,
            },
        )
    )
    from legalis_mcp.tools.cases import list_cases

    result = await list_cases(limit=10)
    assert result["total"] == 1
    assert result["items"][0]["id"] == "c1"


@pytest.mark.asyncio
@respx.mock
async def test_list_cases_clamps_limit():
    route = respx.get(f"{BASE}/api/cases").mock(
        return_value=httpx.Response(200, json={"items": [], "total": 0})
    )
    from legalis_mcp.tools.cases import list_cases

    await list_cases(limit=999)
    assert "limit=100" in str(route.calls[0].request.url)


# ---------------------------------------------------------------------------
# get_case
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_get_case_returns_case():
    respx.get(f"{BASE}/api/cases/case-uuid").mock(
        return_value=httpx.Response(200, json={"id": "case-uuid", "titulo": "Rescisão"})
    )
    from legalis_mcp.tools.cases import get_case

    result = await get_case("case-uuid")
    assert result["id"] == "case-uuid"


# ---------------------------------------------------------------------------
# create_case
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_create_case_sends_required_fields():
    route = respx.post(f"{BASE}/api/cases").mock(
        return_value=httpx.Response(201, json={"id": "new-id"})
    )
    from legalis_mcp.tools.cases import create_case

    result = await create_case(titulo="Rescisão Indireta", area_direito="trabalhista")
    assert result["id"] == "new-id"
    payload = json.loads(route.calls[0].request.read())
    assert payload["titulo"] == "Rescisão Indireta"
    assert payload["area_direito"] == "trabalhista"


@pytest.mark.asyncio
@respx.mock
async def test_create_case_omits_none_fields():
    route = respx.post(f"{BASE}/api/cases").mock(
        return_value=httpx.Response(201, json={"id": "new-id"})
    )
    from legalis_mcp.tools.cases import create_case

    await create_case(titulo="T", area_direito="cível")
    payload = json.loads(route.calls[0].request.read())
    assert "cliente_nome" not in payload
    assert "comarca" not in payload


# ---------------------------------------------------------------------------
# search_cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_search_cases_passes_query():
    route = respx.get(f"{BASE}/api/cases/search").mock(
        return_value=httpx.Response(200, json={"items": [], "total": 0})
    )
    from legalis_mcp.tools.cases import search_cases

    await search_cases(q="João Silva")
    url = str(route.calls[0].request.url)
    assert "q=" in url


# ---------------------------------------------------------------------------
# update_case
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_update_case_sends_only_provided_fields():
    route = respx.put(f"{BASE}/api/cases/c1").mock(
        return_value=httpx.Response(200, json={"id": "c1"})
    )
    from legalis_mcp.tools.cases import update_case

    await update_case("c1", status="arquivado")
    payload = json.loads(route.calls[0].request.read())
    assert payload == {"status": "arquivado"}


# ---------------------------------------------------------------------------
# delete_case
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_delete_case_calls_delete():
    route = respx.delete(f"{BASE}/api/cases/c1").mock(
        return_value=httpx.Response(204)
    )
    from legalis_mcp.tools.cases import delete_case

    result = await delete_case("c1")
    assert result is None
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_delete_case_api_error():
    respx.delete(f"{BASE}/api/cases/c1").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"})
    )
    from legalis_mcp.tools.cases import delete_case

    with pytest.raises(RuntimeError, match="404"):
        await delete_case("c1")

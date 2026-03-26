"""Unit tests for legal document template tools."""

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
    client = _mock_client()
    monkeypatch.setattr("legalis_mcp.tools.templates.get_client", lambda: client)
    return client


# ---------------------------------------------------------------------------
# list_templates
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_list_templates_returns_items():
    respx.get(f"{BASE}/api/templates").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {"id": "tpl-1", "nome": "Reclamação Trabalhista"},
                    {"id": "tpl-2", "nome": "Contestação"},
                ],
                "total": 2,
            },
        )
    )
    from legalis_mcp.tools.templates import list_templates

    result = await list_templates()
    assert result["total"] == 2
    assert result["items"][0]["id"] == "tpl-1"


@pytest.mark.asyncio
@respx.mock
async def test_list_templates_clamps_limit():
    route = respx.get(f"{BASE}/api/templates").mock(
        return_value=httpx.Response(200, json={"items": [], "total": 0})
    )
    from legalis_mcp.tools.templates import list_templates

    await list_templates(limit=500)
    assert "limit=100" in str(route.calls[0].request.url)


# ---------------------------------------------------------------------------
# get_template
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_get_template_returns_details():
    respx.get(f"{BASE}/api/templates/tpl-1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "tpl-1",
                "nome": "Reclamação Trabalhista",
                "sections": ["fatos", "fundamentos_juridicos", "pedidos"],
            },
        )
    )
    from legalis_mcp.tools.templates import get_template

    result = await get_template("tpl-1")
    assert result["id"] == "tpl-1"
    assert "sections" in result


@pytest.mark.asyncio
@respx.mock
async def test_get_template_api_error():
    respx.get(f"{BASE}/api/templates/invalid").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"})
    )
    from legalis_mcp.tools.templates import get_template

    with pytest.raises(RuntimeError, match="404"):
        await get_template("invalid")

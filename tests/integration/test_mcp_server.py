"""
Integration tests for the Legalis MCP server.

These tests run against a real backend (via Docker Compose in /integration/).
They call the REST API directly through LegalisClient to validate the full
request/response cycle end-to-end.

Prerequisites:
    cd integration && docker-compose up -d
    LEGALIS_API_URL=http://localhost:8000
    LEGALIS_ACCESS_TOKEN=<token from test user>
    LEGALIS_REFRESH_TOKEN=<refresh token>

Run:
    cd mcp && pytest tests/integration/ -v
"""

import os
import pytest
import httpx

# Skip all integration tests unless a real token is available
pytestmark = pytest.mark.skipif(
    not os.environ.get("LEGALIS_ACCESS_TOKEN"),
    reason="LEGALIS_ACCESS_TOKEN not set — skipping integration tests (requires Docker)",
)

API_URL = os.environ.get("LEGALIS_API_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def http():
    token = os.environ["LEGALIS_ACCESS_TOKEN"]
    with httpx.Client(
        base_url=API_URL,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
    ) as client:
        yield client


@pytest.fixture(scope="session")
def mcp_client():
    """Return a LegalisClient backed by the local test backend."""
    import legalis_mcp.client as client_module
    from legalis_mcp.auth import Credentials
    from legalis_mcp.client import LegalisClient

    creds = Credentials(
        access_token=os.environ["LEGALIS_ACCESS_TOKEN"],
        refresh_token=os.environ.get("LEGALIS_REFRESH_TOKEN", ""),
    )

    original_url = client_module.API_BASE_URL
    client_module.API_BASE_URL = API_URL

    client = LegalisClient(credentials=creds)
    client._http = httpx.AsyncClient(
        base_url=API_URL,
        timeout=httpx.Timeout(30.0),
        headers={"Content-Type": "application/json"},
    )

    yield client

    import asyncio

    asyncio.get_event_loop().run_until_complete(client.close())
    client_module.API_BASE_URL = original_url


# ---------------------------------------------------------------------------
# Smoke test — can we reach the backend?
# ---------------------------------------------------------------------------


def test_backend_is_reachable(http):
    response = http.get("/api/auth/health")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_cases_returns_structure(mcp_client):
    result = await mcp_client.get("/api/cases")
    assert "items" in result or isinstance(result, list)


@pytest.mark.asyncio
async def test_create_and_get_case(mcp_client):
    new_case = await mcp_client.post(
        "/api/cases",
        json={
            "titulo": "MCP Integration Test Case",
            "area_direito": "trabalhista",
            "descricao": "Caso criado pelo teste de integração MCP",
        },
    )
    case_id = new_case["id"]
    assert case_id

    fetched = await mcp_client.get(f"/api/cases/{case_id}")
    assert fetched["id"] == case_id
    assert fetched["titulo"] == "MCP Integration Test Case"


# ---------------------------------------------------------------------------
# Legal documents
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_legal_document(mcp_client):
    case = await mcp_client.post(
        "/api/cases",
        json={"titulo": "Test Legal Doc Case", "area_direito": "trabalhista"},
    )
    case_id = case["id"]

    doc = await mcp_client.post(
        f"/api/cases/{case_id}/legal-documents",
        json={"tipo_peca": "reclamacao_trabalhista"},
    )
    doc_id = doc["id"]
    assert doc_id

    docs_resp = await mcp_client.get(f"/api/cases/{case_id}/legal-documents")
    items = docs_resp.get("documents") or docs_resp.get("items") or docs_resp
    assert any(d["id"] == doc_id for d in items)


# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_my_usage_returns_quota(mcp_client):
    result = await mcp_client.get("/api/plans/my-usage")
    assert any(
        k in result for k in ["used", "limit", "remaining", "quota", "generations_used"]
    )


# ---------------------------------------------------------------------------
# Legislation search
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_legislation(mcp_client):
    result = await mcp_client.get("/api/legislacao", params={"q": "CLT"})
    assert "items" in result or isinstance(result, list)

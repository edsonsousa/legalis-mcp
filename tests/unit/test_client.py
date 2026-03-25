"""Unit tests for LegalisClient — auth, refresh, retry, error handling."""

import pytest
import respx
import httpx
from unittest.mock import patch

from legalis_mcp.client import LegalisClient, AuthError
from legalis_mcp.auth import Credentials


def make_creds(access="tok-access", refresh="tok-refresh"):
    return Credentials(access_token=access, refresh_token=refresh)


# ---------------------------------------------------------------------------
# Successful requests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_get_returns_json():
    respx.get("https://hai-production-612f.up.railway.app/api/cases").mock(
        return_value=httpx.Response(200, json={"items": [], "total": 0})
    )
    client = LegalisClient(credentials=make_creds())
    result = await client.get("/api/cases")
    assert result == {"items": [], "total": 0}
    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_post_sends_json_body():
    route = respx.post("https://hai-production-612f.up.railway.app/api/cases").mock(
        return_value=httpx.Response(201, json={"id": "case-1"})
    )
    client = LegalisClient(credentials=make_creds())
    result = await client.post("/api/cases", json={"titulo": "Teste"})
    assert result == {"id": "case-1"}
    assert route.called
    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_delete_204_returns_none():
    respx.delete("https://hai-production-612f.up.railway.app/api/cases/x").mock(
        return_value=httpx.Response(204)
    )
    client = LegalisClient(credentials=make_creds())
    result = await client.delete("/api/cases/x")
    assert result is None
    await client.close()


# ---------------------------------------------------------------------------
# Token refresh on 401
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_refreshes_token_on_401_then_retries():
    call_count = 0

    def cases_side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(401, json={"detail": "Unauthorized"})
        return httpx.Response(200, json={"items": []})

    respx.get("https://hai-production-612f.up.railway.app/api/cases").mock(
        side_effect=cases_side_effect
    )
    respx.post("https://hai-production-612f.up.railway.app/api/auth/refresh").mock(
        return_value=httpx.Response(
            200, json={"access_token": "new-tok", "refresh_token": "new-ref"}
        )
    )

    with patch("legalis_mcp.client.save_credentials"):
        client = LegalisClient(credentials=make_creds())
        result = await client.get("/api/cases")

    assert result == {"items": []}
    assert call_count == 2
    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_raises_auth_error_when_refresh_fails():
    respx.get("https://hai-production-612f.up.railway.app/api/cases").mock(
        return_value=httpx.Response(401)
    )
    respx.post("https://hai-production-612f.up.railway.app/api/auth/refresh").mock(
        return_value=httpx.Response(401)
    )
    client = LegalisClient(credentials=make_creds())
    with pytest.raises(AuthError):
        await client.get("/api/cases")
    await client.close()


# ---------------------------------------------------------------------------
# HTTP error propagation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_raises_runtime_error_on_400():
    respx.post("https://hai-production-612f.up.railway.app/api/cases").mock(
        return_value=httpx.Response(422, json={"detail": "campo obrigatório"})
    )
    client = LegalisClient(credentials=make_creds())
    with pytest.raises(RuntimeError, match="422"):
        await client.post("/api/cases", json={})
    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_raises_runtime_error_on_503():
    respx.get("https://hai-production-612f.up.railway.app/api/cases").mock(
        return_value=httpx.Response(503)
    )
    client = LegalisClient(credentials=make_creds())
    with pytest.raises(RuntimeError, match="503"):
        await client.get("/api/cases")
    await client.close()


# ---------------------------------------------------------------------------
# No credentials
# ---------------------------------------------------------------------------


def test_raises_auth_error_when_no_credentials():
    with patch("legalis_mcp.client.load_credentials", return_value=None):
        with pytest.raises(AuthError):
            LegalisClient()

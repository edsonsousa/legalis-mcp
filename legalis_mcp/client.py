"""
Authenticated HTTP client for the Legalis REST API.

Handles:
- Bearer token injection
- Automatic JWT refresh on 401
- Timeout and basic retry
- Friendly error messages
"""

import os
from typing import Any, Optional

import httpx

from .auth import Credentials, load_credentials, save_credentials

API_BASE_URL = os.environ.get(
    "LEGALIS_API_URL", "https://hai-production-612f.up.railway.app"
)

_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
_RETRYABLE_STATUSES = {502, 503, 504}


class AuthError(Exception):
    """Raised when authentication fails and cannot be recovered."""


class LegalisClient:
    """Thin async HTTP client wrapping the Legalis REST API."""

    def __init__(self, credentials: Optional[Credentials] = None):
        self._creds = credentials or load_credentials()
        if self._creds is None:
            raise AuthError(
                "Credenciais não encontradas. Execute `legalis-mcp auth` primeiro."
            )
        self._http = httpx.AsyncClient(
            base_url=API_BASE_URL,
            timeout=_TIMEOUT,
            headers={"Content-Type": "application/json"},
        )

    async def close(self):
        await self._http.aclose()

    # ------------------------------------------------------------------
    # Core request helper
    # ------------------------------------------------------------------

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict] = None,
        json: Optional[Any] = None,
        retry_on_401: bool = True,
    ) -> Any:
        headers = {"Authorization": f"Bearer {self._creds.access_token}"}
        response = await self._http.request(
            method, path, params=params, json=json, headers=headers
        )

        if response.status_code == 401 and retry_on_401:
            # Try to refresh the token once
            refreshed = await self._refresh_token()
            if refreshed:
                return await self.request(
                    method, path, params=params, json=json, retry_on_401=False
                )
            raise AuthError(
                "Sessão expirada. Execute `legalis-mcp auth` para re-autenticar."
            )

        if response.status_code in _RETRYABLE_STATUSES:
            raise RuntimeError(
                f"Servidor temporariamente indisponível ({response.status_code}). "
                "Tente novamente em alguns instantes."
            )

        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise RuntimeError(f"Erro {response.status_code}: {detail}")

        if response.status_code == 204:
            return None

        return response.json()

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    async def get(self, path: str, *, params: Optional[dict] = None) -> Any:
        return await self.request("GET", path, params=params)

    async def post(self, path: str, *, json: Optional[Any] = None) -> Any:
        return await self.request("POST", path, json=json)

    async def put(self, path: str, *, json: Optional[Any] = None) -> Any:
        return await self.request("PUT", path, json=json)

    async def delete(self, path: str) -> Any:
        return await self.request("DELETE", path)

    # ------------------------------------------------------------------
    # Token refresh
    # ------------------------------------------------------------------

    async def _refresh_token(self) -> bool:
        """Attempt to refresh the access token using the refresh token."""
        try:
            response = await self._http.post(
                "/api/auth/refresh",
                json={"refresh_token": self._creds.refresh_token},
                timeout=10.0,
            )
            if response.status_code != 200:
                return False
            data = response.json()
            self._creds.access_token = data["access_token"]
            if data.get("refresh_token"):
                self._creds.refresh_token = data["refresh_token"]
            save_credentials(self._creds)
            return True
        except Exception:
            return False


# Singleton-like factory — one client per server process
_client: Optional[LegalisClient] = None


def get_client() -> LegalisClient:
    global _client
    if _client is None:
        _client = LegalisClient()
    return _client

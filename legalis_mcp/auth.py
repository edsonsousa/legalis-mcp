"""
OAuth 2.0 Authorization Code + PKCE flow for Legalis MCP.

Flow:
  1. legalis-mcp auth → starts local HTTP server on localhost:{port}
  2. Opens browser at {FRONTEND_URL}/auth/authorize?client_id=local-mcp&...
  3. User logs in (if needed) and clicks "Autorizar"
  4. Frontend POSTs to backend → gets redirect_url with ?code=xxx
  5. Frontend redirects browser to localhost:{port}/callback?code=xxx&state=yyy
  6. MCP exchanges code for tokens via POST /api/auth/token
  7. Saves tokens to ~/.legalis/credentials.json

Usage:
    from legalis_mcp.auth import load_credentials, save_credentials, run_auth_flow
"""

import base64
import hashlib
import json
import os
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

CREDENTIALS_FILE = Path(
    os.environ.get("LEGALIS_CREDENTIALS_FILE", "~/.legalis/credentials.json")
).expanduser()

DEFAULT_OAUTH_PORT = int(os.environ.get("LEGALIS_OAUTH_PORT", "3742"))
API_BASE_URL = os.environ.get(
    "LEGALIS_API_URL", "https://hai-production-612f.up.railway.app"
)
FRONTEND_URL = os.environ.get("LEGALIS_FRONTEND_URL", "https://legalis-ia.com")
CLIENT_ID = "local-mcp"


class Credentials:
    def __init__(self, access_token: str, refresh_token: str):
        self.access_token = access_token
        self.refresh_token = refresh_token

    def to_dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Credentials":
        return cls(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
        )


def load_credentials() -> Optional[Credentials]:
    """Load credentials from disk. Returns None if not found or invalid."""
    env_access = os.environ.get("LEGALIS_ACCESS_TOKEN")
    env_refresh = os.environ.get("LEGALIS_REFRESH_TOKEN")
    if env_access and env_refresh:
        return Credentials(access_token=env_access, refresh_token=env_refresh)

    if not CREDENTIALS_FILE.exists():
        return None

    try:
        data = json.loads(CREDENTIALS_FILE.read_text())
        return Credentials.from_dict(data)
    except (json.JSONDecodeError, KeyError):
        return None


def save_credentials(creds: Credentials) -> None:
    """Persist credentials to disk with restricted permissions."""
    CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_FILE.write_text(json.dumps(creds.to_dict(), indent=2))
    CREDENTIALS_FILE.chmod(0o600)


def clear_credentials() -> None:
    """Remove stored credentials."""
    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()


def _generate_pkce() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge (S256)."""
    code_verifier = (
        base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    )
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


def run_auth_flow(port: int = DEFAULT_OAUTH_PORT) -> Credentials:
    """
    OAuth 2.0 Authorization Code + PKCE flow.

    1. Starts a local HTTP server on localhost:{port}.
    2. Opens the browser at the Legalis frontend consent page.
    3. User logs in (if needed) and authorizes.
    4. Frontend redirects to localhost:{port}/callback?code=xxx&state=yyy.
    5. MCP exchanges the code for tokens via POST /api/auth/token.
    6. Saves and returns credentials.
    """
    callback_url = f"http://localhost:{port}/callback"
    code_verifier, code_challenge = _generate_pkce()
    state = secrets.token_urlsafe(16)

    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": callback_url,
        "response_type": "code",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    auth_url = f"{API_BASE_URL}/api/auth/authorize?{urlencode(params)}"

    result: dict = {}
    server_ready = threading.Event()
    auth_done = threading.Event()

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path != "/callback":
                self._respond(404, "Not found")
                return

            query = parse_qs(parsed.query)
            code = query.get("code", [None])[0]
            returned_state = query.get("state", [None])[0]
            error = query.get("error", [None])[0]

            if error:
                result["error"] = error
                self._respond(
                    400,
                    "<html><body><h2>Autorização negada.</h2>"
                    "<p>Pode fechar esta aba.</p></body></html>",
                    content_type="text/html",
                )
                auth_done.set()
                return

            if returned_state != state:
                result["error"] = "state_mismatch"
                self._respond(400, "State mismatch — possível ataque CSRF.")
                auth_done.set()
                return

            if code:
                result["code"] = code
                self._respond(
                    200,
                    "<html><body><h2>Autenticação concluída ✓</h2>"
                    "<p>Pode fechar esta aba e voltar ao Claude.</p></body></html>",
                    content_type="text/html",
                )
                auth_done.set()
            else:
                self._respond(400, "Código ausente. Tente novamente.")

        def _respond(self, code: int, body: str, content_type: str = "text/plain"):
            encoded = body.encode()
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format, *args):  # silence access logs
            pass

    server = HTTPServer(("localhost", port), CallbackHandler)

    def _serve():
        server_ready.set()
        server.timeout = 0.5
        while not auth_done.is_set():
            server.handle_request()
        server.server_close()

    thread = threading.Thread(target=_serve, daemon=True)
    thread.start()
    server_ready.wait(timeout=5)

    print("\nAbrindo o browser para autenticação...")
    print(f"Se o browser não abrir, acesse manualmente:\n  {auth_url}\n")
    webbrowser.open(auth_url)

    auth_done.wait(timeout=120)

    if result.get("error"):
        raise PermissionError(f"Autorização negada: {result['error']}")

    if not result.get("code"):
        raise TimeoutError(
            "Autenticação não concluída em 2 minutos. Execute `legalis-mcp auth` novamente."
        )

    creds = _exchange_code(result["code"], callback_url, code_verifier)
    save_credentials(creds)
    print("Credenciais salvas com sucesso.")
    return creds


def _exchange_code(code: str, redirect_uri: str, code_verifier: str) -> Credentials:
    """Exchange an authorization code for access + refresh tokens."""
    response = httpx.post(
        f"{API_BASE_URL}/api/auth/token",
        json={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": CLIENT_ID,
            "code_verifier": code_verifier,
        },
        timeout=15.0,
    )
    if response.status_code != 200:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise RuntimeError(f"Falha ao trocar código por tokens: {detail}")

    data = response.json()
    return Credentials(
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
    )

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


_LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="6" fill="#1a3a6b"/>
  <rect x="12" y="8" width="6" height="14" rx="1" fill="white"/>
  <rect x="8" y="6" width="14" height="3.5" rx="1.5" fill="white"/>
  <rect x="7" y="22" width="16" height="3.5" rx="1.5" fill="white"/>
  <circle cx="23" cy="7.5" r="3.5" fill="#d4a843"/>
  <line x1="23" y1="5.5" x2="23" y2="9.5" stroke="white" stroke-width="1.2" stroke-linecap="round"/>
  <line x1="21" y1="7.5" x2="25" y2="7.5" stroke="white" stroke-width="1.2" stroke-linecap="round"/>
</svg>"""

_HTML_BASE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Legalis — {title}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #f8fafc;
      color: #0f172a;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .card {{
      background: #ffffff;
      border-radius: 12px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.06);
      padding: 40px 48px;
      max-width: 440px;
      width: 100%;
      text-align: center;
      border-top: 4px solid {accent};
    }}
    .logo {{ margin-bottom: 24px; }}
    .icon {{
      width: 52px; height: 52px; border-radius: 50%;
      background: {icon_bg};
      display: flex; align-items: center; justify-content: center;
      margin: 0 auto 20px;
      font-size: 24px;
    }}
    h1 {{ font-size: 1.25rem; font-weight: 600; color: #0f172a; margin-bottom: 8px; }}
    p {{ font-size: 0.9rem; color: #64748b; line-height: 1.5; }}
    .detail {{
      margin-top: 12px;
      font-size: 0.8rem;
      color: #94a3b8;
      font-family: monospace;
    }}
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">{logo}</div>
    <div class="icon">{icon}</div>
    <h1>{heading}</h1>
    <p>{body}</p>
    {detail_block}
  </div>
</body>
</html>"""


def _html_success() -> str:
    """Return styled HTML for the OAuth success page."""
    return _HTML_BASE.format(
        title="Autenticação concluída",
        accent="#1a3a6b",
        icon_bg="#dcfce7",
        logo=_LOGO_SVG,
        icon="✓",
        heading="Autenticação concluída",
        body="Pode fechar esta aba e voltar ao Claude.",
        detail_block="",
    )


def _html_error(message: str) -> str:
    """Return styled HTML for OAuth error pages."""
    return _HTML_BASE.format(
        title="Erro de autenticação",
        accent="#dc2626",
        icon_bg="#fee2e2",
        logo=_LOGO_SVG,
        icon="✕",
        heading="Erro de autenticação",
        body="Pode fechar esta aba e tentar novamente.",
        detail_block=f'<p class="detail">{message}</p>',
    )


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
                self._respond(400, _html_error("Autorização negada."), content_type="text/html")
                auth_done.set()
                return

            if returned_state != state:
                result["error"] = "state_mismatch"
                self._respond(400, _html_error("Erro de segurança: state mismatch."), content_type="text/html")
                auth_done.set()
                return

            if code:
                result["code"] = code
                self._respond(200, _html_success(), content_type="text/html")
                auth_done.set()
            else:
                self._respond(400, _html_error("Código ausente. Tente novamente."), content_type="text/html")

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

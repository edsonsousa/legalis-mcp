"""
OAuth browser flow + credentials persistence for Legalis MCP.

Usage:
    from legalis_mcp.auth import load_credentials, save_credentials, run_auth_flow
"""

import json
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlparse

CREDENTIALS_FILE = Path(
    os.environ.get("LEGALIS_CREDENTIALS_FILE", "~/.legalis/credentials.json")
).expanduser()

DEFAULT_OAUTH_PORT = int(os.environ.get("LEGALIS_OAUTH_PORT", "3742"))
API_BASE_URL = os.environ.get(
    "LEGALIS_API_URL", "https://hai-production-612f.up.railway.app"
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
    # Environment variables take precedence (for CI/tests)
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
    # Restrict to owner read/write only
    CREDENTIALS_FILE.chmod(0o600)


def clear_credentials() -> None:
    """Remove stored credentials."""
    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()


def run_auth_flow(port: int = DEFAULT_OAUTH_PORT) -> Credentials:
    """
    Start OAuth browser flow.

    1. Starts a local HTTP server on `localhost:{port}`.
    2. Opens the browser at the backend /auth/mcp endpoint.
    3. Waits for the backend to redirect back with tokens.
    4. Saves and returns credentials.
    """
    callback_url = f"http://localhost:{port}/callback"
    auth_url = f"{API_BASE_URL}/api/auth/mcp?redirect={callback_url}"

    result: dict = {}
    server_ready = threading.Event()
    auth_done = threading.Event()

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path != "/callback":
                self._respond(404, "Not found")
                return

            params = parse_qs(parsed.query)
            access_token = params.get("token", [None])[0]
            refresh_token = params.get("refresh", [None])[0]

            if access_token and refresh_token:
                result["access_token"] = access_token
                result["refresh_token"] = refresh_token
                self._respond(
                    200,
                    "<html><body><h2>Autenticação concluída ✓</h2>"
                    "<p>Pode fechar esta aba e voltar ao Claude.</p></body></html>",
                    content_type="text/html",
                )
                auth_done.set()
            else:
                self._respond(400, "Token ausente na resposta. Tente novamente.")

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
        # Serve until auth completes or timeout
        server.timeout = 0.5
        while not auth_done.is_set():
            server.handle_request()
        server.server_close()

    thread = threading.Thread(target=_serve, daemon=True)
    thread.start()
    server_ready.wait(timeout=5)

    print(f"\nAbrindo o browser para autenticação...")
    print(f"Se o browser não abrir, acesse manualmente:\n  {auth_url}\n")
    webbrowser.open(auth_url)

    auth_done.wait(timeout=120)

    if not result.get("access_token"):
        raise TimeoutError(
            "Autenticação não concluída em 2 minutos. Execute `legalis-mcp auth` novamente."
        )

    creds = Credentials(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
    )
    save_credentials(creds)
    print("Credenciais salvas com sucesso.")
    return creds

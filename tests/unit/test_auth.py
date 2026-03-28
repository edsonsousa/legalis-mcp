"""Unit tests for auth module — URL construction, credentials loading."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import legalis_mcp.auth as auth_module
from legalis_mcp.auth import (
    API_BASE_URL,
    CLIENT_ID,
    FRONTEND_URL,
    Credentials,
    _html_error,
    _html_success,
    load_credentials,
    save_credentials,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


def test_frontend_url_default():
    """FRONTEND_URL padrão deve ser legalis-ia.com."""
    assert FRONTEND_URL == "https://legalis-ia.com"


def test_client_id_is_local_mcp():
    assert CLIENT_ID == "local-mcp"


# ---------------------------------------------------------------------------
# auth_url construction — captured by intercepting webbrowser.open
# ---------------------------------------------------------------------------


def _capture_auth_url(port: int = 3742) -> str:
    """
    Run the auth flow just far enough to capture the URL passed to
    webbrowser.open, then abort without actually starting a browser or server.
    """
    captured: dict = {}

    def fake_open(url):
        captured["url"] = url

    # Prevent the real HTTP server thread from starting
    fake_event = MagicMock()
    fake_event.wait.return_value = True
    fake_event.is_set.return_value = True

    fake_done = MagicMock()
    fake_done.wait.return_value = True
    fake_done.is_set.return_value = True

    # We need result to have a "code" so _exchange_code is called — but we
    # don't want the actual token exchange. Raise after URL capture.
    with (
        patch("legalis_mcp.auth.threading.Event", side_effect=[fake_event, fake_done]),
        patch("legalis_mcp.auth.threading.Thread"),
        patch("legalis_mcp.auth.webbrowser.open", side_effect=fake_open),
        patch("legalis_mcp.auth._exchange_code", side_effect=RuntimeError("stop")),
        patch("legalis_mcp.auth.HTTPServer"),
    ):
        try:
            auth_module.run_auth_flow(port=port)
        except (RuntimeError, Exception):
            pass

    return captured.get("url", "")


def test_auth_url_points_to_backend():
    """auth_url deve apontar para o backend /api/auth/authorize, não o frontend."""
    url = _capture_auth_url()
    assert url.startswith(f"{API_BASE_URL}/api/auth/authorize"), (
        f"Expected URL starting with {API_BASE_URL}/api/auth/authorize, got: {url}"
    )


def test_auth_url_not_direct_frontend():
    """auth_url não deve apontar diretamente para o frontend."""
    url = _capture_auth_url()
    assert "legalis-ia.com" not in url
    assert "legalis-ia.com" not in url


def test_auth_url_contains_client_id():
    url = _capture_auth_url()
    assert "client_id=local-mcp" in url


def test_auth_url_contains_pkce_params():
    url = _capture_auth_url()
    assert "code_challenge=" in url
    assert "code_challenge_method=S256" in url
    assert "state=" in url
    assert "response_type=code" in url


def test_auth_url_contains_redirect_uri():
    url = _capture_auth_url(port=3742)
    assert "redirect_uri=" in url
    assert "localhost" in url
    assert "3742" in url


# ---------------------------------------------------------------------------
# load_credentials
# ---------------------------------------------------------------------------


def test_load_credentials_from_env(monkeypatch):
    monkeypatch.setenv("LEGALIS_ACCESS_TOKEN", "env-access")
    monkeypatch.setenv("LEGALIS_REFRESH_TOKEN", "env-refresh")
    creds = load_credentials()
    assert creds is not None
    assert creds.access_token == "env-access"
    assert creds.refresh_token == "env-refresh"


def test_load_credentials_from_file(tmp_path, monkeypatch):
    monkeypatch.delenv("LEGALIS_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("LEGALIS_REFRESH_TOKEN", raising=False)

    creds_file = tmp_path / "credentials.json"
    creds_file.write_text(
        json.dumps({"access_token": "file-access", "refresh_token": "file-refresh"})
    )
    monkeypatch.setattr(auth_module, "CREDENTIALS_FILE", creds_file)

    creds = load_credentials()
    assert creds is not None
    assert creds.access_token == "file-access"
    assert creds.refresh_token == "file-refresh"


def test_load_credentials_returns_none_when_missing(tmp_path, monkeypatch):
    monkeypatch.delenv("LEGALIS_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("LEGALIS_REFRESH_TOKEN", raising=False)
    monkeypatch.setattr(auth_module, "CREDENTIALS_FILE", tmp_path / "nonexistent.json")

    assert load_credentials() is None


def test_load_credentials_env_takes_precedence_over_file(tmp_path, monkeypatch):
    monkeypatch.setenv("LEGALIS_ACCESS_TOKEN", "env-access")
    monkeypatch.setenv("LEGALIS_REFRESH_TOKEN", "env-refresh")

    creds_file = tmp_path / "credentials.json"
    creds_file.write_text(
        json.dumps({"access_token": "file-access", "refresh_token": "file-refresh"})
    )
    monkeypatch.setattr(auth_module, "CREDENTIALS_FILE", creds_file)

    creds = load_credentials()
    assert creds.access_token == "env-access"


# ---------------------------------------------------------------------------
# HTML pages — _html_success / _html_error
# ---------------------------------------------------------------------------


def test_html_success_contains_primary_color():
    assert "#1a3a6b" in _html_success()


def test_html_success_contains_accent_color():
    assert "#d4a843" in _html_success()


def test_html_success_contains_message():
    html = _html_success()
    assert "Autenticação concluída" in html
    assert "fechar" in html


def test_html_success_is_valid_html():
    html = _html_success()
    assert "<!DOCTYPE html>" in html
    assert "<head>" in html
    assert "<body>" in html


def test_html_error_contains_message():
    html = _html_error("Autorização negada.")
    assert "Autorização negada." in html


def test_html_error_contains_primary_color():
    assert "#1a3a6b" in _html_error("qualquer erro")


def test_html_error_differs_from_success():
    assert _html_error("x") != _html_success()

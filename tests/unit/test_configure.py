"""Unit tests for legalis-mcp configure command."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

import legalis_mcp.__main__ as main_module
from legalis_mcp.__main__ import cli


@pytest.fixture
def runner():
    return CliRunner()


# ---------------------------------------------------------------------------
# _find_executable
# ---------------------------------------------------------------------------


def test_find_executable_uses_shutil_which_when_found():
    with patch("shutil.which", return_value="/usr/local/bin/legalis-mcp"):
        result = main_module._find_executable()
    assert result == "/usr/local/bin/legalis-mcp"


def test_find_executable_fallback_to_sys_executable():
    with patch("shutil.which", return_value=None):
        result = main_module._find_executable()
    assert sys.executable in result
    assert "legalis_mcp" in result


# ---------------------------------------------------------------------------
# _get_client_config_path
# ---------------------------------------------------------------------------


def test_get_client_config_path_returns_none_when_parent_missing(tmp_path):
    nonexistent = str(tmp_path / "no_such_dir" / "config.json")
    paths = {"linux": nonexistent, "darwin": nonexistent, "win32": nonexistent}
    result = main_module._get_client_config_path(paths)
    assert result is None


def test_get_client_config_path_returns_path_when_parent_exists(tmp_path):
    config_dir = tmp_path / "some_client"
    config_dir.mkdir()
    config_file = str(config_dir / "config.json")
    paths = {"linux": config_file, "darwin": config_file, "win32": config_file}
    result = main_module._get_client_config_path(paths)
    assert result == config_dir / "config.json"


# ---------------------------------------------------------------------------
# _merge_mcp_config
# ---------------------------------------------------------------------------


def test_merge_mcp_config_creates_new_file(tmp_path):
    config_path = tmp_path / "config.json"
    main_module._merge_mcp_config(config_path, "/usr/bin/legalis-mcp")
    data = json.loads(config_path.read_text())
    assert data["mcpServers"]["legalis"]["command"] == "/usr/bin/legalis-mcp"
    assert data["mcpServers"]["legalis"]["args"] == ["serve"]


def test_merge_mcp_config_preserves_existing_servers(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"mcpServers": {"other-server": {"command": "other", "args": []}}})
    )
    main_module._merge_mcp_config(config_path, "/usr/bin/legalis-mcp")
    data = json.loads(config_path.read_text())
    assert "other-server" in data["mcpServers"]
    assert "legalis" in data["mcpServers"]


def test_merge_mcp_config_overwrites_existing_legalis_entry(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"mcpServers": {"legalis": {"command": "old-path", "args": ["serve"]}}})
    )
    main_module._merge_mcp_config(config_path, "/new/legalis-mcp")
    data = json.loads(config_path.read_text())
    assert data["mcpServers"]["legalis"]["command"] == "/new/legalis-mcp"


def test_merge_mcp_config_handles_empty_json(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text("{}")
    main_module._merge_mcp_config(config_path, "legalis-mcp")
    data = json.loads(config_path.read_text())
    assert "mcpServers" in data
    assert "legalis" in data["mcpServers"]


# ---------------------------------------------------------------------------
# configure command — end-to-end via CliRunner
# ---------------------------------------------------------------------------


def _single_client(config_path: Path) -> dict:
    p = str(config_path)
    return {"Test Client": {"linux": p, "darwin": p, "win32": p}}


def test_configure_detects_and_writes_client(tmp_path, monkeypatch, runner):
    config_dir = tmp_path / "client"
    config_dir.mkdir()
    config_path = config_dir / "config.json"

    monkeypatch.setattr(main_module, "_MCP_CLIENTS", _single_client(config_path))
    with patch("shutil.which", return_value="/usr/bin/legalis-mcp"):
        result = runner.invoke(cli, ["configure"])

    assert result.exit_code == 0
    assert "Test Client" in result.output
    assert "\u2713" in result.output
    data = json.loads(config_path.read_text())
    assert "legalis" in data["mcpServers"]
    assert data["mcpServers"]["legalis"]["command"] == "/usr/bin/legalis-mcp"


def test_configure_shows_not_found_for_absent_clients(tmp_path, monkeypatch, runner):
    absent = str(tmp_path / "nonexistent" / "config.json")
    monkeypatch.setattr(
        main_module,
        "_MCP_CLIENTS",
        {"Absent Client": {"linux": absent, "darwin": absent, "win32": absent}},
    )
    result = runner.invoke(cli, ["configure"])
    assert result.exit_code == 0
    assert "Absent Client" in result.output
    assert "nao encontrados" in result.output


def test_configure_fallback_output_when_no_clients(monkeypatch, runner):
    monkeypatch.setattr(main_module, "_MCP_CLIENTS", {})
    with patch("shutil.which", return_value="/usr/bin/legalis-mcp"):
        result = runner.invoke(cli, ["configure"])
    assert result.exit_code == 0
    assert "mcpServers" in result.output
    assert "legalis" in result.output


def test_configure_merge_safe_preserves_other_servers(tmp_path, monkeypatch, runner):
    config_dir = tmp_path / "client"
    config_dir.mkdir()
    config_path = config_dir / "config.json"
    config_path.write_text(
        json.dumps({"mcpServers": {"another-mcp": {"command": "another", "args": []}}})
    )

    monkeypatch.setattr(main_module, "_MCP_CLIENTS", _single_client(config_path))
    with patch("shutil.which", return_value="/usr/bin/legalis-mcp"):
        runner.invoke(cli, ["configure"])

    data = json.loads(config_path.read_text())
    assert "another-mcp" in data["mcpServers"]
    assert "legalis" in data["mcpServers"]

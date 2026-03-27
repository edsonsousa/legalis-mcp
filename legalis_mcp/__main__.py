"""
Entry point for the Legalis MCP server.

Usage:
    legalis-mcp auth        # Authenticate via browser (OAuth flow)
    legalis-mcp configure   # Configure Legalis MCP in detected MCP clients
    legalis-mcp serve       # Start MCP server (stdio transport, for Claude config)
    legalis-mcp logout      # Remove stored credentials
    legalis-mcp status      # Check authentication status
"""

import json
import shutil
import sys
from pathlib import Path
from typing import Optional

import click

_MCP_CLIENTS: dict[str, dict[str, str]] = {
    "Claude Desktop": {
        "linux": "~/.config/claude/claude_desktop_config.json",
        "darwin": "~/Library/Application Support/Claude/claude_desktop_config.json",
        "win32": "~/AppData/Roaming/Claude/claude_desktop_config.json",
    },
    "Cursor": {
        "linux": "~/.cursor/mcp.json",
        "darwin": "~/.cursor/mcp.json",
        "win32": "~/AppData/Roaming/Cursor/mcp.json",
    },
    "Windsurf": {
        "linux": "~/.codeium/windsurf/mcp_config.json",
        "darwin": "~/.codeium/windsurf/mcp_config.json",
        "win32": "~/.codeium/windsurf/mcp_config.json",
    },
    "Claude Code": {
        "linux": "~/.claude/claude_code_config.json",
        "darwin": "~/.claude/claude_code_config.json",
        "win32": "~/.claude/claude_code_config.json",
    },
}


def _find_executable() -> str:
    found = shutil.which("legalis-mcp")
    if found:
        return found
    return f"{sys.executable} -m legalis_mcp"


def _get_client_config_path(paths_by_platform: dict[str, str]) -> Optional[Path]:
    platform = sys.platform
    raw = paths_by_platform.get(platform) or paths_by_platform.get("linux")
    if not raw:
        return None
    path = Path(raw).expanduser()
    if path.parent.exists():
        return path
    return None


def _merge_mcp_config(config_path: Path, executable: str) -> None:
    existing: dict = {}
    if config_path.exists():
        try:
            existing = json.loads(config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = {}
    existing.setdefault("mcpServers", {})["legalis"] = {
        "command": executable,
        "args": ["serve"],
    }
    config_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")


@click.group()
def cli():
    """Legalis MCP — AI assistant for Brazilian legal practitioners."""
    pass


@cli.command()
def configure():
    """Configure Legalis MCP in detected MCP clients automatically."""
    executable = _find_executable()
    configured = []
    not_found = []

    for client_name, paths_by_platform in _MCP_CLIENTS.items():
        config_path = _get_client_config_path(paths_by_platform)
        if config_path is None:
            not_found.append(client_name)
            continue
        _merge_mcp_config(config_path, executable)
        configured.append((client_name, config_path))

    if configured:
        click.echo("\nClientes configurados:")
        for name, path in configured:
            click.echo(f"  \u2713 {name}  \u2192  {path}")
        click.echo("\nReinicie o cliente para ativar o Legalis.")

    if not_found:
        click.echo("\nClientes nao encontrados:")
        for name in not_found:
            click.echo(f"  - {name}")

    if not configured:
        click.echo("\nNenhum cliente MCP detectado.")
        click.echo("Adicione manualmente ao arquivo de configuracao do seu cliente:\n")
        fallback = {
            "mcpServers": {
                "legalis": {"command": executable, "args": ["serve"]}
            }
        }
        click.echo(json.dumps(fallback, indent=2))


@cli.command()
@click.option("--port", default=3742, show_default=True, help="Local OAuth callback port.")
def auth(port: int):
    """Authenticate with Legalis via browser (OAuth flow)."""
    from .auth import run_auth_flow

    try:
        run_auth_flow(port=port)
        click.echo("Autenticado com sucesso. Token salvo em ~/.legalis/credentials.json")
    except TimeoutError as e:
        click.echo(f"Erro: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Erro inesperado: {e}", err=True)
        sys.exit(1)


@cli.command()
def serve():
    """Start the Legalis MCP server (stdio transport)."""
    from .auth import load_credentials

    creds = load_credentials()
    if creds is None:
        click.echo(
            "Credenciais não encontradas. Execute `legalis-mcp auth` primeiro.",
            err=True,
        )
        sys.exit(1)

    from .server import mcp

    mcp.run(transport="stdio")


@cli.command()
def logout():
    """Remove stored Legalis credentials."""
    from .auth import clear_credentials

    clear_credentials()
    click.echo("Credenciais removidas.")


@cli.command()
def status():
    """Check if credentials are stored and valid."""
    from .auth import load_credentials

    creds = load_credentials()
    if creds is None:
        click.echo("Não autenticado. Execute `legalis-mcp auth` para autenticar.")
        sys.exit(1)

    import asyncio

    async def _check():
        from .client import LegalisClient

        client = LegalisClient(credentials=creds)
        try:
            data = await client.get("/api/auth/me")
            click.echo(f"Autenticado como: {data.get('email', data.get('name', 'usuário'))}")
        except Exception as e:
            click.echo(f"Token presente mas inválido: {e}", err=True)
            sys.exit(1)
        finally:
            await client.close()

    asyncio.run(_check())


if __name__ == "__main__":
    cli()

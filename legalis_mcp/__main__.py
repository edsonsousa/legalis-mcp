"""
Entry point for the Legalis MCP server.

Usage:
    legalis-mcp auth        # Authenticate via browser (OAuth flow)
    legalis-mcp serve       # Start MCP server (stdio transport, for Claude config)
    legalis-mcp logout      # Remove stored credentials
    legalis-mcp status      # Check authentication status
"""

import sys

import click


@click.group()
def cli():
    """Legalis MCP — AI assistant for Brazilian legal practitioners."""
    pass


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

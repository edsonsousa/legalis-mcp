# Legalis MCP Server
### Assistente jurídico com IA para advogados brasileiros

> [Leia em Português](README.pt-BR.md)

MCP (Model Context Protocol) server for [Legalis](https://hai-ten.vercel.app) — Brazilian legal document AI for attorneys.

Connect Claude (or any MCP-compatible client) to your Legalis account and interact with cases, generate legal documents, search legislation, and more using natural language.

---

## Quick start

### 1. Install

```bash
pip install legalis-mcp
# or with uv:
uv tool install legalis-mcp
```

### 2. Authenticate

```bash
legalis-mcp auth
```

This opens your browser. Log in to Legalis normally — tokens are saved to `~/.legalis/credentials.json` (owner-readable only).

### 3. Configure Claude

Add to your Claude configuration (`~/.claude/claude_desktop_config.json` for Claude Desktop, or `claude_code_config.json` for Claude Code):

```json
{
  "mcpServers": {
    "legalis": {
      "command": "legalis-mcp",
      "args": ["serve"]
    }
  }
}
```

### 4. Use

In Claude, try:

- *"Liste meus casos no Legalis"*
- *"Crie um caso de rescisão indireta para João Silva"*
- *"Gere a seção de fundamentos jurídicos da peça X do caso Y"*
- *"Pesquise legislação trabalhista sobre justa causa"*
- *"Quantas gerações ainda tenho disponíveis este mês?"*

---

## Available tools

| Tool | Description |
|------|-------------|
| `list_cases` | List cases (paginated, filterable by status) |
| `get_case` | Get case details by ID |
| `create_case` | Create a new case |
| `update_case` | Update case fields |
| `search_cases` | Full-text search across cases |
| `list_legal_documents` | List peças processuais for a case |
| `get_legal_document` | Get a document with all sections |
| `create_legal_document` | Create a new legal document |
| `generate_section` | AI-generate a document section (fatos, fundamentos, pedidos…) |
| `get_case_context` | Get case context (facts, parties, evidence) |
| `run_interview` | AI-guided case intake interview |
| `search_legislation` | Search Brazilian legislation (LexML) |
| `get_my_usage` | Check AI quota and billing period usage |

---

## CLI commands

```bash
legalis-mcp auth      # Authenticate via browser
legalis-mcp serve     # Start MCP server (stdio)
legalis-mcp status    # Verify authentication
legalis-mcp logout    # Remove stored credentials
```

---

## Development

```bash
git clone <repo>
cd mcp
pip install -e ".[test]"

# Run unit tests (no external services needed)
pytest tests/unit/ -v

# Run integration tests (requires Docker)
cd ../integration && docker-compose up -d
cd ../mcp
LEGALIS_API_URL=http://localhost:8000 \
LEGALIS_ACCESS_TOKEN=<token> \
LEGALIS_REFRESH_TOKEN=<refresh> \
pytest tests/integration/ -v
```

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LEGALIS_API_URL` | `https://hai-production-612f.up.railway.app` | Backend URL |
| `LEGALIS_ACCESS_TOKEN` | — | Pre-issued token (CI/test only) |
| `LEGALIS_REFRESH_TOKEN` | — | Refresh token (CI/test only) |
| `LEGALIS_CREDENTIALS_FILE` | `~/.legalis/credentials.json` | Credentials file path |
| `LEGALIS_OAUTH_PORT` | `3742` | Local OAuth callback port |

---

## Security

- Credentials are stored in `~/.legalis/credentials.json` with `600` permissions (owner read/write only).
- The OAuth redirect is restricted to `http://localhost` — open-redirect attacks are blocked at the backend.
- Tokens are never stored in the MCP configuration file.
- All API calls go through the existing Legalis backend — RBAC, rate limiting, and quotas apply normally.

---

## Publishing

```bash
# PyPI
pip install build twine
python -m build
twine upload dist/*

# Then register at:
# - smithery.ai (MCP marketplace)
# - mcp.so (community directory)
# - github.com/modelcontextprotocol/servers (official list)
```

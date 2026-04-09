# Legalis MCP Server
### Assistente jurídico com IA para advogados brasileiros

> [Leia em Português](README.pt-BR.md)

MCP (Model Context Protocol) server for [Legalis](https://legalis-ia.com) — Brazilian legal document AI for attorneys.

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

### Cases
| Tool | Description |
|------|-------------|
| `list_cases` | List cases (paginated, filterable by status) |
| `get_case` | Get case details by ID |
| `create_case` | Create a new case |
| `update_case` | Update case fields |
| `search_cases` | Full-text search across cases |
| `delete_case` | Delete a case permanently |

### Legal documents
| Tool | Description |
|------|-------------|
| `list_legal_documents` | List peças processuais for a case |
| `get_legal_document` | Get a document with all sections |
| `create_legal_document` | Create a new legal document |
| `generate_section` | AI-generate a document section (fatos, fundamentos, pedidos…) |
| `update_section_text` | Manually edit a document section |
| `get_case_context` | Get case context (facts, parties, evidence) |
| `update_case_context` | Update case context |
| `delete_legal_document` | Delete a legal document |
| `export_legal_document_docx` | Export a document as DOCX |

### Events & Tasks
| Tool | Description |
|------|-------------|
| `create_case_event` | Create an event on a case (internal or client-visible) |
| `list_case_events` | List events for a case |
| `delete_case_event` | Delete a case event |
| `create_case_task` | Create a task with due date and priority |
| `list_case_tasks` | List tasks for a case |
| `update_case_task` | Update a task's fields |
| `complete_case_task` | Mark a task as complete |
| `delete_case_task` | Delete a task |
| `list_upcoming_tasks` | List upcoming tasks across all cases |
| `list_overdue_tasks` | List all overdue tasks |

### Other
| Tool | Description |
|------|-------------|
| `run_interview` | AI-guided case intake interview |
| `list_templates` | List available document templates |
| `get_template` | Get template details and sections |
| `search_legislation` | Search Brazilian legislation (LexML) |
| `get_my_usage` | Check AI quota and billing period usage |

---

## API coverage

The table below maps every Legalis backend endpoint to its MCP tool (when available).

### Cases
| Endpoint | Method | MCP Tool |
|----------|--------|----------|
| `/api/cases` | GET | `list_cases` ✅ |
| `/api/cases` | POST | `create_case` ✅ |
| `/api/cases/{id}` | GET | `get_case` ✅ |
| `/api/cases/{id}` | PUT | `update_case` ✅ |
| `/api/cases/{id}` | DELETE | `delete_case` ✅ |
| `/api/cases/search` | GET | `search_cases` ✅ |
| `/api/cases/{id}/overview` | GET | — |
| `/api/cases/{id}/portal-token` | POST / DELETE | — |

### Legal documents
| Endpoint | Method | MCP Tool |
|----------|--------|----------|
| `/api/cases/{id}/legal-documents` | GET | `list_legal_documents` ✅ |
| `/api/cases/{id}/legal-documents` | POST | `create_legal_document` ✅ |
| `/api/cases/{id}/legal-documents/{doc}` | GET | `get_legal_document` ✅ |
| `/api/cases/{id}/legal-documents/{doc}` | DELETE | `delete_legal_document` ✅ |
| `/api/cases/{id}/legal-documents/{doc}/sections/{key}/generate` | POST | `generate_section` ✅ |
| `/api/cases/{id}/legal-documents/{doc}/sections/{key}/text` | PUT | `update_section_text` ✅ |
| `/api/cases/{id}/legal-documents/{doc}/export/docx` | GET | `export_legal_document_docx` ✅ |

### Case context
| Endpoint | Method | MCP Tool |
|----------|--------|----------|
| `/api/cases/{id}/context` | GET | `get_case_context` ✅ |
| `/api/cases/{id}/context` | PUT | `update_case_context` ✅ |
| `/api/cases/{id}/context/history` | GET | — |

### Tasks
| Endpoint | Method | MCP Tool |
|----------|--------|----------|
| `/api/cases/{id}/tasks` | GET | `list_case_tasks` ✅ |
| `/api/cases/{id}/tasks` | POST | `create_case_task` ✅ |
| `/api/cases/{id}/tasks/{task}` | PUT | `update_case_task` ✅ |
| `/api/cases/{id}/tasks/{task}` | DELETE | `delete_case_task` ✅ |
| `/api/cases/{id}/tasks/{task}/complete` | POST | `complete_case_task` ✅ |
| `/api/tasks/upcoming` | GET | `list_upcoming_tasks` ✅ |
| `/api/tasks/overdue` | GET | `list_overdue_tasks` ✅ |

### Events
| Endpoint | Method | MCP Tool |
|----------|--------|----------|
| `/api/cases/{id}/events` | GET | `list_case_events` ✅ |
| `/api/cases/{id}/events` | POST | `create_case_event` ✅ |
| `/api/cases/{id}/events/{event}` | DELETE | `delete_case_event` ✅ |

### Templates & Legislation
| Endpoint | Method | MCP Tool |
|----------|--------|----------|
| `/api/templates` | GET | `list_templates` ✅ |
| `/api/templates/{id}` | GET | `get_template` ✅ |
| `/api/legislacao` | GET | `search_legislation` ✅ |

### Usage
| Endpoint | Method | MCP Tool |
|----------|--------|----------|
| `/api/plans/my-usage` | GET | `get_my_usage` ✅ |

### Not yet covered
| Endpoint | Notes |
|----------|-------|
| `/api/cases/{id}/overview` | BFF endpoint — case + tasks + events in one call |
| `/api/cases/{id}/portal-token` | Share case status with clients via public link |
| `/api/cases/{id}/context/history` | Context version history |
| `/api/users/me` | User profile read/update |
| `/api/users/settings` | Notification and UI preferences |
| `/api/users/documents` | Uploaded documents (non-generated) |
| `/api/voice-agent/*` | Voice assistant (plan-gated feature) |
| `/api/corporates/{id}/users` | Team member management |
| `/api/subordinates/invite` | Invite team members |

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

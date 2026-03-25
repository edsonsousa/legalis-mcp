# Legalis MCP Server
### Assistente jurídico com IA para advogados brasileiros

Servidor MCP (Model Context Protocol) para o [Legalis](https://hai-ten.vercel.app) — IA para documentos jurídicos voltada a advogados brasileiros.

Conecte o Claude (ou qualquer cliente compatível com MCP) à sua conta Legalis e interaja com casos, gere peças processuais, pesquise legislação e muito mais usando linguagem natural.

---

## Início rápido

### 1. Instalar

```bash
pip install legalis-mcp
# ou com uv:
uv tool install legalis-mcp
```

### 2. Autenticar

```bash
legalis-mcp auth
```

Abre o navegador. Faça login normalmente no Legalis — os tokens são salvos em `~/.legalis/credentials.json` (leitura restrita ao dono).

### 3. Configurar o Claude

Adicione à configuração do Claude (`~/.claude/claude_desktop_config.json` para o Claude Desktop, ou `claude_code_config.json` para o Claude Code):

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

### 4. Usar

No Claude, experimente:

- *"Liste meus casos no Legalis"*
- *"Crie um caso de rescisão indireta para João Silva"*
- *"Gere a seção de fundamentos jurídicos da peça X do caso Y"*
- *"Pesquise legislação trabalhista sobre justa causa"*
- *"Quantas gerações ainda tenho disponíveis este mês?"*

---

## Ferramentas disponíveis

| Ferramenta | Descrição |
|------------|-----------|
| `list_cases` | Lista casos (paginado, filtrável por status) |
| `get_case` | Obtém detalhes de um caso pelo ID |
| `create_case` | Cria um novo caso |
| `update_case` | Atualiza campos de um caso |
| `search_cases` | Busca textual em todos os casos |
| `list_legal_documents` | Lista peças processuais de um caso |
| `get_legal_document` | Obtém uma peça com todas as seções |
| `create_legal_document` | Cria uma nova peça processual |
| `generate_section` | Gera com IA uma seção da peça (fatos, fundamentos, pedidos…) |
| `get_case_context` | Obtém contexto do caso (fatos, partes, provas) |
| `run_interview` | Entrevista guiada por IA para captação do caso |
| `search_legislation` | Pesquisa legislação brasileira (LexML) |
| `get_my_usage` | Consulta cota de IA e uso no período de cobrança |

---

## Comandos CLI

```bash
legalis-mcp auth      # Autenticar via navegador
legalis-mcp serve     # Iniciar servidor MCP (stdio)
legalis-mcp status    # Verificar autenticação
legalis-mcp logout    # Remover credenciais salvas
```

---

## Desenvolvimento

```bash
git clone <repo>
cd mcp
pip install -e ".[test]"

# Testes unitários (sem serviços externos)
pytest tests/unit/ -v

# Testes de integração (requer Docker)
cd ../integration && docker-compose up -d
cd ../mcp
LEGALIS_API_URL=http://localhost:8000 \
LEGALIS_ACCESS_TOKEN=<token> \
LEGALIS_REFRESH_TOKEN=<refresh> \
pytest tests/integration/ -v
```

### Variáveis de ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `LEGALIS_API_URL` | `https://hai-production-612f.up.railway.app` | URL do backend |
| `LEGALIS_ACCESS_TOKEN` | — | Token pré-emitido (apenas CI/testes) |
| `LEGALIS_REFRESH_TOKEN` | — | Refresh token (apenas CI/testes) |
| `LEGALIS_CREDENTIALS_FILE` | `~/.legalis/credentials.json` | Caminho do arquivo de credenciais |
| `LEGALIS_OAUTH_PORT` | `3742` | Porta local para callback OAuth |

---

## Segurança

- Credenciais salvas em `~/.legalis/credentials.json` com permissão `600` (leitura/escrita somente pelo dono).
- O redirect OAuth é restrito a `http://localhost` — ataques de open-redirect são bloqueados no backend.
- Tokens nunca são armazenados no arquivo de configuração do MCP.
- Todas as chamadas de API passam pelo backend existente do Legalis — RBAC, rate limiting e cotas aplicam-se normalmente.

---

## Publicação

```bash
# PyPI
pip install build twine
python -m build
twine upload dist/*

# Registrar também em:
# - smithery.ai (marketplace de MCPs)
# - mcp.so (diretório da comunidade)
# - github.com/modelcontextprotocol/servers (lista oficial)
```

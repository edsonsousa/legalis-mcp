# Legalis MCP Server
### Assistente jurídico com IA para advogados brasileiros

Servidor MCP (Model Context Protocol) para o [Legalis](https://legalis-ia.com) — IA para documentos jurídicos voltada a advogados brasileiros.

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

### Casos
| Ferramenta | Descrição |
|------------|-----------|
| `list_cases` | Lista casos (paginado, filtrável por status) |
| `get_case` | Obtém detalhes de um caso pelo ID |
| `create_case` | Cria um novo caso |
| `update_case` | Atualiza campos de um caso |
| `search_cases` | Busca textual em todos os casos |
| `delete_case` | Exclui um caso permanentemente |

### Peças processuais
| Ferramenta | Descrição |
|------------|-----------|
| `list_legal_documents` | Lista peças processuais de um caso |
| `get_legal_document` | Obtém uma peça com todas as seções |
| `create_legal_document` | Cria uma nova peça processual |
| `generate_section` | Gera com IA uma seção da peça (fatos, fundamentos, pedidos…) |
| `update_section_text` | Edita manualmente o texto de uma seção |
| `get_case_context` | Obtém contexto do caso (fatos, partes, provas) |
| `update_case_context` | Atualiza o contexto do caso |
| `delete_legal_document` | Exclui uma peça processual |
| `export_legal_document_docx` | Exporta uma peça no formato DOCX |

### Eventos e Tarefas
| Ferramenta | Descrição |
|------------|-----------|
| `create_case_event` | Cria um evento no caso (interno ou visível ao cliente) |
| `list_case_events` | Lista eventos de um caso |
| `delete_case_event` | Exclui um evento do caso |
| `create_case_task` | Cria uma tarefa com prazo e prioridade |
| `list_case_tasks` | Lista tarefas de um caso |
| `update_case_task` | Atualiza campos de uma tarefa |
| `complete_case_task` | Marca uma tarefa como concluída |
| `delete_case_task` | Exclui uma tarefa |
| `list_upcoming_tasks` | Lista tarefas próximas em todos os casos |
| `list_overdue_tasks` | Lista todas as tarefas em atraso |

### Outros
| Ferramenta | Descrição |
|------------|-----------|
| `run_interview` | Entrevista guiada por IA para captação do caso |
| `list_templates` | Lista modelos de peças disponíveis |
| `get_template` | Obtém detalhes e seções de um modelo |
| `search_legislation` | Pesquisa legislação brasileira (LexML) |
| `get_my_usage` | Consulta cota de IA e uso no período de cobrança |

---

## Cobertura da API

A tabela abaixo mapeia todos os endpoints do backend Legalis para a ferramenta MCP correspondente (quando disponível).

### Casos
| Endpoint | Método | Ferramenta MCP |
|----------|--------|----------------|
| `/api/cases` | GET | `list_cases` ✅ |
| `/api/cases` | POST | `create_case` ✅ |
| `/api/cases/{id}` | GET | `get_case` ✅ |
| `/api/cases/{id}` | PUT | `update_case` ✅ |
| `/api/cases/{id}` | DELETE | `delete_case` ✅ |
| `/api/cases/search` | GET | `search_cases` ✅ |
| `/api/cases/{id}/overview` | GET | — |
| `/api/cases/{id}/portal-token` | POST / DELETE | — |

### Peças processuais
| Endpoint | Método | Ferramenta MCP |
|----------|--------|----------------|
| `/api/cases/{id}/legal-documents` | GET | `list_legal_documents` ✅ |
| `/api/cases/{id}/legal-documents` | POST | `create_legal_document` ✅ |
| `/api/cases/{id}/legal-documents/{doc}` | GET | `get_legal_document` ✅ |
| `/api/cases/{id}/legal-documents/{doc}` | DELETE | `delete_legal_document` ✅ |
| `/api/cases/{id}/legal-documents/{doc}/sections/{key}/generate` | POST | `generate_section` ✅ |
| `/api/cases/{id}/legal-documents/{doc}/sections/{key}/text` | PUT | `update_section_text` ✅ |
| `/api/cases/{id}/legal-documents/{doc}/export/docx` | GET | `export_legal_document_docx` ✅ |

### Contexto do caso
| Endpoint | Método | Ferramenta MCP |
|----------|--------|----------------|
| `/api/cases/{id}/context` | GET | `get_case_context` ✅ |
| `/api/cases/{id}/context` | PUT | `update_case_context` ✅ |
| `/api/cases/{id}/context/history` | GET | — |

### Tarefas
| Endpoint | Método | Ferramenta MCP |
|----------|--------|----------------|
| `/api/cases/{id}/tasks` | GET | `list_case_tasks` ✅ |
| `/api/cases/{id}/tasks` | POST | `create_case_task` ✅ |
| `/api/cases/{id}/tasks/{task}` | PUT | `update_case_task` ✅ |
| `/api/cases/{id}/tasks/{task}` | DELETE | `delete_case_task` ✅ |
| `/api/cases/{id}/tasks/{task}/complete` | POST | `complete_case_task` ✅ |
| `/api/tasks/upcoming` | GET | `list_upcoming_tasks` ✅ |
| `/api/tasks/overdue` | GET | `list_overdue_tasks` ✅ |

### Eventos
| Endpoint | Método | Ferramenta MCP |
|----------|--------|----------------|
| `/api/cases/{id}/events` | GET | `list_case_events` ✅ |
| `/api/cases/{id}/events` | POST | `create_case_event` ✅ |
| `/api/cases/{id}/events/{event}` | DELETE | `delete_case_event` ✅ |

### Modelos e Legislação
| Endpoint | Método | Ferramenta MCP |
|----------|--------|----------------|
| `/api/templates` | GET | `list_templates` ✅ |
| `/api/templates/{id}` | GET | `get_template` ✅ |
| `/api/legislacao` | GET | `search_legislation` ✅ |

### Uso
| Endpoint | Método | Ferramenta MCP |
|----------|--------|----------------|
| `/api/plans/my-usage` | GET | `get_my_usage` ✅ |

### Ainda não cobertos
| Endpoint | Observação |
|----------|------------|
| `/api/cases/{id}/overview` | Endpoint BFF — caso + tarefas + eventos em uma chamada |
| `/api/cases/{id}/portal-token` | Compartilhar o caso com clientes via link público |
| `/api/cases/{id}/context/history` | Histórico de versões do contexto |
| `/api/users/me` | Leitura e atualização do perfil do usuário |
| `/api/users/settings` | Preferências de notificação e interface |
| `/api/users/documents` | Documentos enviados (não gerados por IA) |
| `/api/voice-agent/*` | Assistente de voz (feature limitada por plano) |
| `/api/corporates/{id}/users` | Gerenciamento de membros da equipe |
| `/api/subordinates/invite` | Convidar membros para a equipe |

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

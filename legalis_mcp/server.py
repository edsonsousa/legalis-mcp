"""
Legalis MCP Server — FastMCP app registering all tools.

This module is the core of the MCP server. It instantiates the FastMCP app
and registers every tool from the tools/ package.
"""

from mcp.server.fastmcp import FastMCP

from .tools.cases import (
    create_case,
    get_case,
    list_cases,
    search_cases,
    update_case,
)
from .tools.interview import run_interview
from .tools.legal_docs import (
    create_legal_document,
    generate_section,
    get_case_context,
    get_legal_document,
    list_legal_documents,
)
from .tools.legislation import search_legislation
from .tools.usage import get_my_usage

mcp = FastMCP(
    "Legalis Legal Assistant",
    instructions=(
        "You are connected to Legalis, a Brazilian legal document AI platform for attorneys. "
        "You can manage cases, generate legal documents (peças processuais), search legislation, "
        "run AI-guided case intake interviews, and check quota usage. "
        "All operations are scoped to the authenticated attorney's account. "
        "Legal documents follow Brazilian procedural law. "
        "When generating document sections, always confirm the case_id and doc_id before proceeding."
    ),
)

# ── Cases ──────────────────────────────────────────────────────────────────────
mcp.tool()(list_cases)
mcp.tool()(get_case)
mcp.tool()(create_case)
mcp.tool()(update_case)
mcp.tool()(search_cases)

# ── Legal documents ────────────────────────────────────────────────────────────
mcp.tool()(list_legal_documents)
mcp.tool()(get_legal_document)
mcp.tool()(create_legal_document)
mcp.tool()(generate_section)
mcp.tool()(get_case_context)

# ── Interview ──────────────────────────────────────────────────────────────────
mcp.tool()(run_interview)

# ── Legislation ────────────────────────────────────────────────────────────────
mcp.tool()(search_legislation)

# ── Usage / quota ──────────────────────────────────────────────────────────────
mcp.tool()(get_my_usage)

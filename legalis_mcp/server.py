"""
Legalis MCP Server — FastMCP app registering all tools.

This module is the core of the MCP server. It instantiates the FastMCP app
and registers every tool from the tools/ package.
"""

from mcp.server.fastmcp import FastMCP

from .tools.cases import (
    create_case,
    delete_case,
    get_case,
    list_cases,
    search_cases,
    update_case,
)
from .tools.events_tasks import (
    complete_case_task,
    create_case_event,
    create_case_task,
    delete_case_event,
    delete_case_task,
    list_case_events,
    list_case_tasks,
    list_overdue_tasks,
    list_upcoming_tasks,
    update_case_task,
)
from .tools.interview import run_interview
from .tools.legal_docs import (
    create_legal_document,
    delete_legal_document,
    export_legal_document_docx,
    generate_section,
    get_case_context,
    get_legal_document,
    list_legal_documents,
    update_case_context,
    update_section_text,
)
from .tools.legislation import search_legislation
from .tools.templates import get_template, list_templates
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
mcp.tool()(delete_case)

# ── Legal documents ────────────────────────────────────────────────────────────
mcp.tool()(list_legal_documents)
mcp.tool()(get_legal_document)
mcp.tool()(create_legal_document)
mcp.tool()(generate_section)
mcp.tool()(update_section_text)
mcp.tool()(get_case_context)
mcp.tool()(update_case_context)
mcp.tool()(delete_legal_document)
mcp.tool()(export_legal_document_docx)

# ── Events & Tasks ─────────────────────────────────────────────────────────────
mcp.tool()(create_case_event)
mcp.tool()(list_case_events)
mcp.tool()(delete_case_event)
mcp.tool()(create_case_task)
mcp.tool()(list_case_tasks)
mcp.tool()(update_case_task)
mcp.tool()(complete_case_task)
mcp.tool()(delete_case_task)
mcp.tool()(list_upcoming_tasks)
mcp.tool()(list_overdue_tasks)

# ── Interview ──────────────────────────────────────────────────────────────────
mcp.tool()(run_interview)

# ── Templates ──────────────────────────────────────────────────────────────────
mcp.tool()(list_templates)
mcp.tool()(get_template)

# ── Legislation ────────────────────────────────────────────────────────────────
mcp.tool()(search_legislation)

# ── Usage / quota ──────────────────────────────────────────────────────────────
mcp.tool()(get_my_usage)

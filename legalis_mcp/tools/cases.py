"""MCP tools for case management."""

from typing import Any, Optional

from ..client import get_client


async def list_cases(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
) -> dict:
    """
    List cases for the authenticated user.

    Args:
        skip: Number of cases to skip (pagination offset).
        limit: Maximum number of cases to return (max 100).
        status: Filter by status (e.g. "ativo", "arquivado").
    """
    params: dict[str, Any] = {"skip": skip, "limit": min(limit, 100)}
    if status:
        params["status"] = status
    client = get_client()
    return await client.get("/api/cases", params=params)


async def get_case(case_id: str) -> dict:
    """
    Get details of a specific case.

    Args:
        case_id: UUID of the case.
    """
    client = get_client()
    return await client.get(f"/api/cases/{case_id}")


async def create_case(
    titulo: str,
    area_direito: str,
    descricao: Optional[str] = None,
    numero_processo: Optional[str] = None,
    cliente_nome: Optional[str] = None,
    cliente_cpf: Optional[str] = None,
    parte_contraria: Optional[str] = None,
    comarca: Optional[str] = None,
    vara: Optional[str] = None,
) -> dict:
    """
    Create a new case.

    Args:
        titulo: Case title.
        area_direito: Legal area (e.g. "trabalhista", "cível", "previdenciário").
        descricao: Optional case description / summary of facts.
        numero_processo: Court process number (optional).
        cliente_nome: Client full name.
        cliente_cpf: Client CPF (Brazilian tax ID).
        parte_contraria: Opposing party name.
        comarca: Court jurisdiction city.
        vara: Court division/chamber.
    """
    payload: dict[str, Any] = {
        "titulo": titulo,
        "area_direito": area_direito,
    }
    if descricao:
        payload["descricao"] = descricao
    if numero_processo:
        payload["numero_processo"] = numero_processo
    if cliente_nome:
        payload["cliente_nome"] = cliente_nome
    if cliente_cpf:
        payload["cliente_cpf"] = cliente_cpf
    if parte_contraria:
        payload["parte_contraria"] = parte_contraria
    if comarca:
        payload["comarca"] = comarca
    if vara:
        payload["vara"] = vara

    client = get_client()
    return await client.post("/api/cases", json=payload)


async def update_case(
    case_id: str,
    titulo: Optional[str] = None,
    area_direito: Optional[str] = None,
    descricao: Optional[str] = None,
    status: Optional[str] = None,
    numero_processo: Optional[str] = None,
    cliente_nome: Optional[str] = None,
    parte_contraria: Optional[str] = None,
    comarca: Optional[str] = None,
    vara: Optional[str] = None,
) -> dict:
    """
    Update an existing case.

    Args:
        case_id: UUID of the case to update.
        titulo: New title (optional).
        area_direito: New legal area (optional).
        descricao: New description (optional).
        status: New status (optional).
        numero_processo: Process number (optional).
        cliente_nome: Client name (optional).
        parte_contraria: Opposing party (optional).
        comarca: Court city (optional).
        vara: Court division (optional).
    """
    payload: dict[str, Any] = {}
    for field, value in [
        ("titulo", titulo),
        ("area_direito", area_direito),
        ("descricao", descricao),
        ("status", status),
        ("numero_processo", numero_processo),
        ("cliente_nome", cliente_nome),
        ("parte_contraria", parte_contraria),
        ("comarca", comarca),
        ("vara", vara),
    ]:
        if value is not None:
            payload[field] = value

    client = get_client()
    return await client.put(f"/api/cases/{case_id}", json=payload)


async def search_cases(
    q: str,
    skip: int = 0,
    limit: int = 20,
) -> dict:
    """
    Search cases by keyword.

    Args:
        q: Search query (searches title, description, client name, etc.).
        skip: Pagination offset.
        limit: Maximum results (max 100).
    """
    params: dict[str, Any] = {"q": q, "skip": skip, "limit": min(limit, 100)}
    client = get_client()
    return await client.get("/api/cases/search", params=params)


async def delete_case(case_id: str) -> dict:
    """
    Delete a case permanently.

    Args:
        case_id: UUID of the case to delete.
    """
    client = get_client()
    return await client.delete(f"/api/cases/{case_id}")

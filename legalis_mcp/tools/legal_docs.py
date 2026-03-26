"""MCP tools for legal documents (peças processuais)."""

from typing import Any, Optional

from ..client import get_client


async def list_legal_documents(case_id: str) -> dict:
    """
    List all legal documents for a case.

    Args:
        case_id: UUID of the case.
    """
    client = get_client()
    return await client.get(f"/api/cases/{case_id}/legal-documents")


async def get_legal_document(case_id: str, doc_id: str) -> dict:
    """
    Get a legal document with all its sections.

    Args:
        case_id: UUID of the case.
        doc_id: UUID of the legal document.
    """
    client = get_client()
    return await client.get(f"/api/cases/{case_id}/legal-documents/{doc_id}")


async def create_legal_document(
    case_id: str,
    tipo_peca: str,
    template_id: Optional[str] = None,
    titulo: Optional[str] = None,
) -> dict:
    """
    Create a new legal document for a case.

    Args:
        case_id: UUID of the case.
        tipo_peca: Document type (e.g. "reclamacao_trabalhista", "contestacao", "recurso_ordinario").
        template_id: Optional UUID of a template to use as base.
        titulo: Optional document title override.
    """
    payload: dict[str, Any] = {"tipo_peca": tipo_peca}
    if template_id:
        payload["template_id"] = template_id
    if titulo:
        payload["titulo"] = titulo

    client = get_client()
    return await client.post(f"/api/cases/{case_id}/legal-documents", json=payload)


async def generate_section(
    case_id: str,
    doc_id: str,
    section_key: str,
    instructions: Optional[str] = None,
) -> dict:
    """
    Generate or regenerate a section of a legal document using AI.

    Args:
        case_id: UUID of the case.
        doc_id: UUID of the legal document.
        section_key: Section identifier (e.g. "fatos", "fundamentos_juridicos", "pedidos").
        instructions: Optional custom instructions for the AI generation.
    """
    payload: dict[str, Any] = {"section_key": section_key}
    if instructions:
        payload["instructions"] = instructions

    client = get_client()
    return await client.post(
        f"/api/cases/{case_id}/legal-documents/{doc_id}/sections",
        json=payload,
    )


async def get_case_context(case_id: str) -> dict:
    """
    Get the current context for a case (facts, parties, evidence summary).

    Args:
        case_id: UUID of the case.
    """
    client = get_client()
    return await client.get(f"/api/cases/{case_id}/context")


async def update_case_context(
    case_id: str,
    fatos: Optional[str] = None,
    partes: Optional[dict] = None,
    provas: Optional[str] = None,
    observacoes: Optional[str] = None,
) -> dict:
    """
    Update the context for a case (facts, parties, evidence summary).

    Args:
        case_id: UUID of the case.
        fatos: Summary of the case facts.
        partes: Parties involved (dict with keys like "reclamante", "reclamada", etc.).
        provas: Summary of available evidence.
        observacoes: Additional notes or observations.
    """
    payload: dict[str, Any] = {}
    for field, value in [
        ("fatos", fatos),
        ("partes", partes),
        ("provas", provas),
        ("observacoes", observacoes),
    ]:
        if value is not None:
            payload[field] = value

    client = get_client()
    return await client.put(f"/api/cases/{case_id}/context", json=payload)


async def delete_legal_document(case_id: str, doc_id: str) -> dict:
    """
    Delete a legal document from a case.

    Args:
        case_id: UUID of the case.
        doc_id: UUID of the legal document to delete.
    """
    client = get_client()
    return await client.delete(f"/api/cases/{case_id}/legal-documents/{doc_id}")


async def update_section_text(
    case_id: str,
    doc_id: str,
    section_key: str,
    text: str,
) -> dict:
    """
    Manually update the text of a section in a legal document.

    Use this to edit AI-generated content or write a section from scratch.

    Args:
        case_id: UUID of the case.
        doc_id: UUID of the legal document.
        section_key: Section identifier (e.g. "fatos", "fundamentos_juridicos", "pedidos").
        text: New text content for the section.
    """
    payload: dict[str, Any] = {"text": text}
    client = get_client()
    return await client.put(
        f"/api/cases/{case_id}/legal-documents/{doc_id}/sections/{section_key}/text",
        json=payload,
    )


async def export_legal_document_docx(case_id: str, doc_id: str) -> dict:
    """
    Export a legal document as a DOCX file.

    Returns a download URL or base64-encoded file content.

    Args:
        case_id: UUID of the case.
        doc_id: UUID of the legal document to export.
    """
    client = get_client()
    return await client.post(
        f"/api/cases/{case_id}/legal-documents/{doc_id}/export/docx",
        json={},
    )

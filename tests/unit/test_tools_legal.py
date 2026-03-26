"""Unit tests for legal document tools."""

import json
import pytest
import respx
import httpx

from legalis_mcp.auth import Credentials
from legalis_mcp.client import LegalisClient

BASE = "https://hai-production-612f.up.railway.app"
CASE_ID = "case-abc"
DOC_ID = "doc-xyz"


def _mock_client():
    return LegalisClient(credentials=Credentials("tok", "ref"))


@pytest.fixture(autouse=True)
def patch_get_client(monkeypatch):
    client = _mock_client()
    monkeypatch.setattr("legalis_mcp.tools.legal_docs.get_client", lambda: client)
    return client


# ---------------------------------------------------------------------------
# list_legal_documents
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_list_legal_documents():
    respx.get(f"{BASE}/api/cases/{CASE_ID}/legal-documents").mock(
        return_value=httpx.Response(200, json={"documents": []})
    )
    from legalis_mcp.tools.legal_docs import list_legal_documents

    result = await list_legal_documents(CASE_ID)
    assert "documents" in result


# ---------------------------------------------------------------------------
# get_legal_document
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_get_legal_document():
    respx.get(f"{BASE}/api/cases/{CASE_ID}/legal-documents/{DOC_ID}").mock(
        return_value=httpx.Response(
            200, json={"id": DOC_ID, "tipo_peca": "contestacao", "sections": []}
        )
    )
    from legalis_mcp.tools.legal_docs import get_legal_document

    result = await get_legal_document(CASE_ID, DOC_ID)
    assert result["id"] == DOC_ID


# ---------------------------------------------------------------------------
# create_legal_document
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_create_legal_document_sends_tipo():
    route = respx.post(f"{BASE}/api/cases/{CASE_ID}/legal-documents").mock(
        return_value=httpx.Response(201, json={"id": "new-doc"})
    )
    from legalis_mcp.tools.legal_docs import create_legal_document

    result = await create_legal_document(CASE_ID, tipo_peca="reclamacao_trabalhista")
    assert result["id"] == "new-doc"
    payload = json.loads(route.calls[0].request.read())
    assert payload["tipo_peca"] == "reclamacao_trabalhista"


# ---------------------------------------------------------------------------
# generate_section
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_generate_section_calls_sections_endpoint():
    route = respx.post(
        f"{BASE}/api/cases/{CASE_ID}/legal-documents/{DOC_ID}/sections"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "section_key": "fatos",
                "texto_gerado": "Os fatos são...",
                "teve_alteracao": True,
            },
        )
    )
    from legalis_mcp.tools.legal_docs import generate_section

    result = await generate_section(CASE_ID, DOC_ID, "fatos")
    assert result["section_key"] == "fatos"
    assert result["texto_gerado"] != ""
    payload = json.loads(route.calls[0].request.read())
    assert payload["section_key"] == "fatos"


@pytest.mark.asyncio
@respx.mock
async def test_generate_section_passes_instructions():
    route = respx.post(
        f"{BASE}/api/cases/{CASE_ID}/legal-documents/{DOC_ID}/sections"
    ).mock(return_value=httpx.Response(200, json={"section_key": "pedidos"}))
    from legalis_mcp.tools.legal_docs import generate_section

    await generate_section(CASE_ID, DOC_ID, "pedidos", instructions="Foque nos danos morais")
    payload = json.loads(route.calls[0].request.read())
    assert payload.get("instructions") == "Foque nos danos morais"


# ---------------------------------------------------------------------------
# get_case_context
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_get_case_context():
    respx.get(f"{BASE}/api/cases/{CASE_ID}/context").mock(
        return_value=httpx.Response(200, json={"fatos": "...", "version": 3})
    )
    from legalis_mcp.tools.legal_docs import get_case_context

    result = await get_case_context(CASE_ID)
    assert result["version"] == 3


# ---------------------------------------------------------------------------
# update_case_context
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_update_case_context_sends_provided_fields():
    route = respx.put(f"{BASE}/api/cases/{CASE_ID}/context").mock(
        return_value=httpx.Response(200, json={"fatos": "Novo fato", "version": 4})
    )
    from legalis_mcp.tools.legal_docs import update_case_context

    result = await update_case_context(CASE_ID, fatos="Novo fato")
    assert result["version"] == 4
    payload = json.loads(route.calls[0].request.read())
    assert payload == {"fatos": "Novo fato"}


@pytest.mark.asyncio
@respx.mock
async def test_update_case_context_omits_none_fields():
    route = respx.put(f"{BASE}/api/cases/{CASE_ID}/context").mock(
        return_value=httpx.Response(200, json={})
    )
    from legalis_mcp.tools.legal_docs import update_case_context

    await update_case_context(CASE_ID, observacoes="obs")
    payload = json.loads(route.calls[0].request.read())
    assert "fatos" not in payload
    assert payload["observacoes"] == "obs"


# ---------------------------------------------------------------------------
# delete_legal_document
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_delete_legal_document_calls_delete():
    route = respx.delete(f"{BASE}/api/cases/{CASE_ID}/legal-documents/{DOC_ID}").mock(
        return_value=httpx.Response(204)
    )
    from legalis_mcp.tools.legal_docs import delete_legal_document

    result = await delete_legal_document(CASE_ID, DOC_ID)
    assert result is None
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_delete_legal_document_api_error():
    respx.delete(f"{BASE}/api/cases/{CASE_ID}/legal-documents/{DOC_ID}").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"})
    )
    from legalis_mcp.tools.legal_docs import delete_legal_document

    with pytest.raises(RuntimeError, match="404"):
        await delete_legal_document(CASE_ID, DOC_ID)


# ---------------------------------------------------------------------------
# update_section_text
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_update_section_text_sends_text():
    route = respx.put(
        f"{BASE}/api/cases/{CASE_ID}/legal-documents/{DOC_ID}/sections/fatos/text"
    ).mock(return_value=httpx.Response(200, json={"section_key": "fatos", "text": "novo"}))
    from legalis_mcp.tools.legal_docs import update_section_text

    result = await update_section_text(CASE_ID, DOC_ID, "fatos", "novo")
    assert result["section_key"] == "fatos"
    payload = json.loads(route.calls[0].request.read())
    assert payload["text"] == "novo"


# ---------------------------------------------------------------------------
# export_legal_document_docx
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_export_legal_document_docx_calls_endpoint():
    route = respx.post(
        f"{BASE}/api/cases/{CASE_ID}/legal-documents/{DOC_ID}/export/docx"
    ).mock(return_value=httpx.Response(200, json={"download_url": "https://example.com/doc.docx"}))
    from legalis_mcp.tools.legal_docs import export_legal_document_docx

    result = await export_legal_document_docx(CASE_ID, DOC_ID)
    assert "download_url" in result
    assert route.called

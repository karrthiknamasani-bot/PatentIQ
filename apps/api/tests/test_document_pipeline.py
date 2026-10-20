import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.services.document_processing.pipeline import document_pipeline
from tests.fixtures import (
    generate_test_txt_bytes,
    generate_test_docx_bytes,
    generate_test_pdf_bytes,
    generate_scanned_empty_pdf_bytes,
)


def test_pipeline_txt_direct():
    """Verify direct pipeline processing of TXT document."""
    txt_bytes = generate_test_txt_bytes()
    result = document_pipeline.process("patent_spec.txt", txt_bytes, content_type="text/plain")

    assert result.success is True
    assert result.metadata.filename == "patent_spec.txt"
    assert result.metadata.source_type == "txt"
    assert len(result.chunks) > 0

    # Ensure claims were recognized
    claim_chunks = [c for c in result.chunks if c.section == "claims"]
    assert len(claim_chunks) >= 1
    assert any(c.claim_number == 1 for c in claim_chunks)


def test_pipeline_docx_direct():
    """Verify direct pipeline processing of DOCX document."""
    docx_bytes = generate_test_docx_bytes()
    result = document_pipeline.process(
        "invention.docx",
        docx_bytes,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    assert result.success is True
    assert result.metadata.filename == "invention.docx"
    assert result.metadata.source_type == "docx"
    assert len(result.chunks) > 0

    # Claims and source reference check
    assert any("para:" in c.source_reference for c in result.chunks)


def test_pipeline_pdf_direct():
    """Verify direct pipeline processing of multi-page PDF document."""
    pdf_bytes = generate_test_pdf_bytes(num_pages=2)
    result = document_pipeline.process("disclosure.pdf", pdf_bytes, content_type="application/pdf")

    assert result.success is True
    assert result.metadata.filename == "disclosure.pdf"
    assert result.metadata.source_type == "pdf"
    assert result.metadata.page_count == 2
    assert len(result.chunks) > 0

    # Check page references
    assert any("page:1" in c.source_reference for c in result.chunks)
    assert any("page:2" in c.source_reference for c in result.chunks)


def test_pipeline_scanned_pdf_direct():
    """Verify direct pipeline handles scanned/empty PDF by failing with OCR warning."""
    scanned_bytes = generate_scanned_empty_pdf_bytes()
    result = document_pipeline.process("scanned.pdf", scanned_bytes, content_type="application/pdf")

    assert result.success is False
    assert "OCR" in (result.error or "")


@pytest.mark.asyncio
async def test_endpoint_process_txt_success():
    """Verify POST /api/documents/process returns 200 for a valid TXT file."""
    txt_bytes = generate_test_txt_bytes()
    files = {"file": ("patent.txt", txt_bytes, "text/plain")}

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post("/api/documents/process", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "patent.txt"
    assert data["file_type"] == "txt"
    assert data["chunk_count"] > 0
    assert len(data["sample_chunks"]) > 0
    assert "claims" in [s.lower() for s in data["detected_sections"]]


@pytest.mark.asyncio
async def test_endpoint_process_docx_success():
    """Verify POST /api/documents/process returns 200 for a valid DOCX file."""
    docx_bytes = generate_test_docx_bytes()
    files = {
        "file": (
            "invention.docx",
            docx_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post("/api/documents/process", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "invention.docx"
    assert data["file_type"] == "docx"
    assert data["chunk_count"] > 0
    assert len(data["sample_chunks"]) > 0


@pytest.mark.asyncio
async def test_endpoint_process_pdf_success():
    """Verify POST /api/documents/process returns 200 for a valid PDF file."""
    pdf_bytes = generate_test_pdf_bytes(num_pages=2)
    files = {"file": ("disclosure.pdf", pdf_bytes, "application/pdf")}

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post("/api/documents/process", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "disclosure.pdf"
    assert data["file_type"] == "pdf"
    assert data["page_count"] == 2
    assert data["chunk_count"] > 0
    assert len(data["sample_chunks"]) > 0


@pytest.mark.asyncio
async def test_endpoint_process_unsupported_file():
    """Verify POST /api/documents/process rejects unsupported file types with 400."""
    files = {"file": ("malicious.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/octet-stream")}

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post("/api/documents/process", files=files)

    assert response.status_code == 400
    data = response.json()
    assert "Unsupported file extension" in data["detail"]


@pytest.mark.asyncio
async def test_endpoint_process_empty_file():
    """Verify POST /api/documents/process rejects empty files with 400."""
    files = {"file": ("empty.txt", b"", "text/plain")}

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post("/api/documents/process", files=files)

    assert response.status_code == 400
    data = response.json()
    assert "empty" in data["detail"].lower()


@pytest.mark.asyncio
async def test_endpoint_process_scanned_pdf_error():
    """Verify POST /api/documents/process returns 422 for a PDF with no extractable text."""
    scanned_bytes = generate_scanned_empty_pdf_bytes()
    files = {"file": ("scanned_blank.pdf", scanned_bytes, "application/pdf")}

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post("/api/documents/process", files=files)

    assert response.status_code == 422
    data = response.json()
    assert "OCR" in data["detail"]

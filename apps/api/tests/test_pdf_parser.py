import pytest
from app.services.document_processing.pdf_parser import PDFParser, PDFExtractionError
from tests.fixtures import generate_test_pdf_bytes, generate_scanned_empty_pdf_bytes


def test_pdf_parser_extracts_text_and_page_numbers():
    """Verify PyMuPDF extracts text page by page with correct page numbers and references."""
    pdf_bytes = generate_test_pdf_bytes(num_pages=2)
    segments, metadata, warnings = PDFParser.parse(pdf_bytes)

    assert len(segments) == 2
    assert metadata["page_count"] == 2

    # Verify Page 1
    page1 = segments[0]
    assert page1.page_number == 1
    assert page1.source_reference == "page:1"
    assert "Hybrid Rotor Balancing System" in page1.text
    assert "Abstract" in page1.text

    # Verify Page 2
    page2 = segments[1]
    assert page2.page_number == 2
    assert page2.source_reference == "page:2"
    assert page2.section == "claims"
    assert "Claim 1" in page2.text


def test_pdf_parser_scanned_empty_pdf():
    """Verify that a PDF without extractable text raises PDFExtractionError indicating OCR requirement."""
    empty_pdf_bytes = generate_scanned_empty_pdf_bytes()
    with pytest.raises(PDFExtractionError) as exc_info:
        PDFParser.parse(empty_pdf_bytes)

    assert "no extractable text" in str(exc_info.value).lower()
    assert "ocr" in str(exc_info.value).lower()


def test_pdf_parser_corrupted_bytes():
    """Verify graceful failure on corrupted bytes."""
    corrupted_bytes = b"%PDF-1.4 corrupted garbage non-pdf stream"
    with pytest.raises(PDFExtractionError):
        PDFParser.parse(corrupted_bytes)

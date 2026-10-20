import pytest
from app.services.document_processing.docx_parser import DOCXParser, DOCXExtractionError
from tests.fixtures import generate_test_docx_bytes


def test_docx_parser_extracts_paragraphs_and_headings():
    """Verify python-docx extracts paragraphs, detects headings, and sets page_number to None."""
    docx_bytes = generate_test_docx_bytes()
    segments, metadata, warnings = DOCXParser.parse(docx_bytes)

    assert len(segments) > 0
    # DOCX does not store pages; page_number should be None
    assert all(seg.page_number is None for seg in segments)

    # Check paragraph references
    assert segments[0].source_reference.startswith("para:")

    # Verify sections detected from headings
    sections = [seg.section for seg in segments]
    assert "abstract" in sections
    assert "background" in sections
    assert "detailed_description" in sections
    assert "claims" in sections


def test_docx_parser_corrupted_file():
    """Verify controlled error on corrupted DOCX stream."""
    with pytest.raises(DOCXExtractionError):
        DOCXParser.parse(b"not a valid zip/docx archive")

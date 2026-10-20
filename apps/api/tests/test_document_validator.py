import pytest
from app.services.document_processing.validator import DocumentValidator
from tests.fixtures import generate_test_txt_bytes, generate_test_pdf_bytes, generate_test_docx_bytes


def test_validator_valid_files():
    """Verify that supported extensions (.pdf, .docx, .txt) pass validation."""
    pdf_bytes = generate_test_pdf_bytes()
    is_valid, err = DocumentValidator.validate("patent.pdf", pdf_bytes, "application/pdf")
    assert is_valid is True
    assert err is None

    docx_bytes = generate_test_docx_bytes()
    is_valid, err = DocumentValidator.validate(
        "patent.docx",
        docx_bytes,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    assert is_valid is True
    assert err is None

    txt_bytes = generate_test_txt_bytes()
    is_valid, err = DocumentValidator.validate("patent.txt", txt_bytes, "text/plain")
    assert is_valid is True
    assert err is None


def test_validator_unsupported_extension():
    """Verify rejection of disallowed file extensions."""
    is_valid, err = DocumentValidator.validate("data.csv", b"a,b,c", "text/csv")
    assert is_valid is False
    assert "Unsupported file extension '.csv'" in err

    is_valid, err = DocumentValidator.validate("photo.png", b"\x89PNG\r\n\x1a\n", "image/png")
    assert is_valid is False
    assert "Unsupported file extension '.png'" in err


def test_validator_empty_file():
    """Verify rejection of empty 0-byte uploads."""
    is_valid, err = DocumentValidator.validate("empty.pdf", b"", "application/pdf")
    assert is_valid is False
    assert "empty" in err.lower()


def test_validator_size_limit(monkeypatch):
    """Verify rejection when file size exceeds the configured maximum."""
    # Temporarily set max size to 1 MB for testing
    from app.core.config import settings
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 1)

    oversized_bytes = b"x" * (1024 * 1024 + 100)  # 1 MB + 100 bytes
    is_valid, err = DocumentValidator.validate("large.txt", oversized_bytes, "text/plain")
    assert is_valid is False
    assert "exceeds maximum allowed limit" in err


def test_validator_mimetype_mismatch():
    """Verify rejection when declared MIME type conflicts with extension."""
    is_valid, err = DocumentValidator.validate("document.pdf", b"fake content", "image/jpeg")
    assert is_valid is False
    assert "does not match .pdf extension" in err

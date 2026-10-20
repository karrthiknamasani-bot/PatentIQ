import io
from typing import List, Tuple, Dict, Any
try:
    import pymupdf as fitz
except ImportError:
    import fitz
from app.schemas.document import ExtractedSegment
from app.services.document_processing.cleaner import TextCleaner
from app.services.document_processing.section_detector import SectionDetector


class PDFExtractionError(Exception):
    """Raised when PDF extraction fails or document is non-textual."""
    pass


class PDFParser:
    """Extracts text page-by-page from PDF files using PyMuPDF."""

    @classmethod
    def parse(cls, file_bytes: bytes) -> Tuple[List[ExtractedSegment], Dict[str, Any], List[str]]:
        """Extracts text, metadata, and warnings from a PDF file buffer.

        Returns:
            (segments, metadata_dict, warnings)
        """
        segments: List[ExtractedSegment] = []
        warnings: List[str] = []
        total_extracted_chars = 0

        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as exc:
            raise PDFExtractionError(f"Malformed or corrupted PDF file: {type(exc).__name__}") from exc

        page_count = len(doc)
        metadata = {
            "title": doc.metadata.get("title") or None,
            "author": doc.metadata.get("author") or None,
            "page_count": page_count,
        }

        current_section = "unknown"

        for page_idx in range(page_count):
            page_num = page_idx + 1
            page = doc[page_idx]
            raw_text = page.get_text("text")
            cleaned_page = TextCleaner.clean(raw_text)

            if not cleaned_page:
                warnings.append(f"Page {page_num} contains no extractable text (possible image or blank page).")
                continue

            total_extracted_chars += len(cleaned_page)

            # Detect section changes within the page
            page_lines = cleaned_page.split("\n")
            detected = SectionDetector.detect_heading(page_lines[0]) if page_lines else None
            if detected:
                current_section = detected

            segments.append(
                ExtractedSegment(
                    text=cleaned_page,
                    section=current_section,
                    page_number=page_num,
                    source_reference=f"page:{page_num}",
                )
            )

        doc.close()

        if total_extracted_chars == 0:
            raise PDFExtractionError(
                "PDF contains no extractable text across all pages. The document appears to be scanned or image-based, which requires Optical Character Recognition (OCR)."
            )

        return segments, metadata, warnings

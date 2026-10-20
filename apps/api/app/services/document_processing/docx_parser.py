import io
from typing import List, Tuple, Dict, Any
import docx
from app.schemas.document import ExtractedSegment
from app.services.document_processing.cleaner import TextCleaner
from app.services.document_processing.section_detector import SectionDetector


class DOCXExtractionError(Exception):
    """Raised when DOCX extraction fails or file is corrupted."""
    pass


class DOCXParser:
    """Extracts paragraphs and headings from Word (.docx) documents using python-docx."""

    @classmethod
    def parse(cls, file_bytes: bytes) -> Tuple[List[ExtractedSegment], Dict[str, Any], List[str]]:
        """Parses DOCX bytes into structured segments with section identification.

        Page numbers are set to None as Word files do not store fixed pagination.
        """
        segments: List[ExtractedSegment] = []
        warnings: List[str] = []

        try:
            doc = docx.Document(io.BytesIO(file_bytes))
        except Exception as exc:
            raise DOCXExtractionError(f"Malformed or corrupted DOCX file: {type(exc).__name__}") from exc

        # Extract title from core properties if available
        title = None
        try:
            if doc.core_properties and doc.core_properties.title:
                title = doc.core_properties.title
        except Exception:
            pass

        metadata = {
            "title": title,
            "page_count": None,
        }

        current_section = "unknown"
        valid_para_count = 0

        for para_idx, para in enumerate(doc.paragraphs):
            raw_text = para.text
            cleaned = TextCleaner.clean(raw_text)
            if not cleaned:
                continue

            valid_para_count += 1
            # Check if this paragraph is a section heading
            is_heading_style = (para.style and para.style.name and "heading" in para.style.name.lower())
            detected = SectionDetector.detect_heading(cleaned)
            if detected:
                current_section = detected
            elif is_heading_style:
                # If styled as a heading but not recognized in patent lexicon, keep current or mark as section
                custom_sec = SectionDetector.detect_heading(cleaned)
                if custom_sec:
                    current_section = custom_sec

            segments.append(
                ExtractedSegment(
                    text=cleaned,
                    section=current_section,
                    page_number=None,  # Page numbers unavailable in DOCX
                    source_reference=f"para:{para_idx + 1}",
                )
            )

        if valid_para_count == 0:
            raise DOCXExtractionError("DOCX file contains no readable text content.")

        return segments, metadata, warnings

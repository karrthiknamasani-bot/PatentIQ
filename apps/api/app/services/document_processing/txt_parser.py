from typing import List, Tuple, Dict, Any
from app.schemas.document import ExtractedSegment
from app.services.document_processing.cleaner import TextCleaner
from app.services.document_processing.section_detector import SectionDetector


class TXTExtractionError(Exception):
    """Raised when text file decoding fails."""
    pass


class TXTParser:
    """Extracts text from plain text files with robust encoding fallback."""

    ENCODINGS_TO_TRY = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

    @classmethod
    def parse(cls, file_bytes: bytes) -> Tuple[List[ExtractedSegment], Dict[str, Any], List[str]]:
        """Parses plain text bytes into paragraph segments with section tagging."""
        decoded_text = None
        used_encoding = None

        for enc in cls.ENCODINGS_TO_TRY:
            try:
                decoded_text = file_bytes.decode(enc)
                used_encoding = enc
                break
            except UnicodeDecodeError:
                continue

        if decoded_text is None:
            raise TXTExtractionError("Unable to decode text file using supported encodings (UTF-8, Latin-1, CP1252).")

        cleaned = TextCleaner.clean(decoded_text)
        if not cleaned:
            raise TXTExtractionError("Plain text file is empty or contains only whitespace.")

        paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
        segments: List[ExtractedSegment] = []
        warnings: List[str] = []

        if used_encoding != "utf-8":
            warnings.append(f"File was decoded using fallback encoding '{used_encoding}' instead of UTF-8.")

        current_section = "unknown"
        for idx, para in enumerate(paragraphs):
            first_line = para.split("\n")[0]
            detected = SectionDetector.detect_heading(first_line)
            if detected:
                current_section = detected

            segments.append(
                ExtractedSegment(
                    text=para,
                    section=current_section,
                    page_number=None,
                    source_reference=f"block:{idx + 1}",
                )
            )

        metadata = {
            "title": None,
            "page_count": None,
            "encoding": used_encoding,
        }

        return segments, metadata, warnings

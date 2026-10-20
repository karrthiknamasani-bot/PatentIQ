import re
from typing import Optional


class SectionDetector:
    """Deterministic rule-based detector for identifying patent and technical document sections."""

    SECTION_PATTERNS = [
        ("claims", re.compile(r"^(?:patent\s+)?claims?(?:\s+of\s+the\s+invention)?(?:\s*:)?$|^what\s+is\s+claimed\s+(?:is|are)\s*:?$", re.IGNORECASE)),
        ("abstract", re.compile(r"^(?:executive\s+)?abstract(?:\s*:)?$", re.IGNORECASE)),
        ("technical_field", re.compile(r"^(?:technical\s+)?field(?:\s+of\s+(?:the\s+)?invention)?(?:\s*:)?$", re.IGNORECASE)),
        ("background", re.compile(r"^(?:background(?:\s+of\s+(?:the\s+)?invention)?|prior\s+art|related\s+art)(?:\s*:)?$", re.IGNORECASE)),
        ("problem", re.compile(r"^(?:technical\s+)?problems?(?:\s+to\s+be\s+solved)?(?:\s*:)?$", re.IGNORECASE)),
        ("summary", re.compile(r"^(?:brief\s+)?summary(?:\s+of\s+(?:the\s+)?invention)?(?:\s*:)?$", re.IGNORECASE)),
        ("detailed_description", re.compile(r"^(?:detailed\s+description(?:\s+of\s+(?:the\s+)?(?:invention|preferred\s+embodiments?))?|detailed\s+specification)(?:\s*:)?$", re.IGNORECASE)),
        ("embodiments", re.compile(r"^(?:preferred\s+|exemplary\s+)?embodiments?(?:\s+of\s+(?:the\s+)?invention)?(?:\s*:)?$", re.IGNORECASE)),
        ("implementation", re.compile(r"^(?:implementation(?:\s+details)?|system\s+architecture|methodology)(?:\s*:)?$", re.IGNORECASE)),
        ("advantages", re.compile(r"^(?:technical\s+)?advantages?(?:\s+of\s+(?:the\s+)?invention)?|effects\s+of\s+(?:the\s+)?invention(?:\s*:)?$", re.IGNORECASE)),
        ("applications", re.compile(r"^(?:commercial\s+)?applications?|industrial\s+applicability(?:\s*:)?$", re.IGNORECASE)),
        ("conclusion", re.compile(r"^conclusions?(?:\s+and\s+future\s+work)?(?:\s*:)?$", re.IGNORECASE)),
        ("references", re.compile(r"^(?:references|cited\s+documents|citations|bibliography)(?:\s*:)?$", re.IGNORECASE)),
        ("title", re.compile(r"^(?:invention\s+)?title(?:\s*:)?$", re.IGNORECASE)),
    ]

    @classmethod
    def detect_heading(cls, line: str) -> Optional[str]:
        """Checks if a single line matches a known section heading.

        Returns canonical section name or None if line is not a section heading.
        """
        clean_line = line.strip()
        if not clean_line or len(clean_line) > 100:
            return None

        # Strip common leading enumeration: "1.", "1.0", "I.", "Section 1:", "(1)"
        clean_line = re.sub(r"^(?:section\s+\d+|(?:\d+(?:\.\d+)*|[ivxlcdm]+)[\.:\)]|\d+(?:\.\d+)*\b)\s*[:-]?\s*", "", clean_line, flags=re.IGNORECASE).strip()

        for section_name, pattern in cls.SECTION_PATTERNS:
            if pattern.match(clean_line):
                return section_name

        return None

    @classmethod
    def classify_segment(cls, text: str, default_section: str = "unknown") -> str:
        """Examines the first line or first paragraph of text to classify the segment section."""
        if not text:
            return default_section

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if not lines:
            return default_section

        # Check first line
        first_line_section = cls.detect_heading(lines[0])
        if first_line_section:
            return first_line_section

        return default_section

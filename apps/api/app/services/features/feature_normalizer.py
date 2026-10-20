import re
import hashlib
from typing import Optional


class FeatureNormalizer:
    """Deterministic normalization and ID generation for technical features.

    Responsibilities:
    - Whitespace normalization and formatting noise cleanup.
    - Preservation of technical terms, numbers, units, and chemical/math symbols.
    - Deterministic, content-addressed feature ID generation.
    """

    # Regex for stripping leading bullet points, numbering, or decorative prefixes
    _PREFIX_RE = re.compile(r"^[\s\-\*\•\d+\.\)\(\]]+\s*")
    _WHITESPACE_RE = re.compile(r"\s+")
    _SURROUNDING_QUOTES_RE = re.compile(r"^[\"\'\`]+|[\"\'\`]+$")

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """Standardizes feature text while strictly preserving technical tokens.

        - Strips extraneous bounding quotes and bullet artifacts.
        - Collapses internal multi-spaces and linebreaks to a single space.
        - Preserves uppercase technical acronyms, chemical formulas, and units.
        """
        if not text:
            return ""

        # 1. Collapse all internal whitespaces/newlines to single space
        cleaned = cls._WHITESPACE_RE.sub(" ", text).strip()

        # 2. Strip leading bullet / numbering decorators if present at boundary
        cleaned = cls._PREFIX_RE.sub("", cleaned).strip()

        # 3. Strip surrounding quotation marks
        cleaned = cls._SURROUNDING_QUOTES_RE.sub("", cleaned).strip()

        # 4. Collapse any residual whitespace
        cleaned = cls._WHITESPACE_RE.sub(" ", cleaned).strip()

        return cleaned

    @classmethod
    def get_canonical_key(cls, feature_type: str, normalized_text: str) -> str:
        """Computes a normalized lowercase key for exact duplicate detection.

        Avoids aggressive stemming or token removal so technical specificity is maintained.
        """
        clean_text = cls.normalize_text(normalized_text).lower()
        clean_type = feature_type.lower().strip()
        return f"{clean_type}::{clean_text}"

    @classmethod
    def generate_feature_id(
        cls,
        project_id: str,
        feature_type: str,
        normalized_text: str,
    ) -> str:
        """Generates a stable, deterministic feature ID from project ID, feature type, and content.

        Format: feat_{type_prefix}_{sha256_hash[:12]}
        Guarantees: Same project + same type + same text -> exact same feature_id.
        """
        canonical = cls.get_canonical_key(feature_type, normalized_text)
        content_bytes = f"{project_id.strip()}::{canonical}".encode("utf-8")
        digest = hashlib.sha256(content_bytes).hexdigest()[:12]
        type_prefix = feature_type.lower()[:4]
        return f"feat_{type_prefix}_{digest}"

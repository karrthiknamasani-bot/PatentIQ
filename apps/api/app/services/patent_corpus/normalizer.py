import re
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from app.schemas.patent import PatentDocumentBase


class PatentNormalizer:
    """Deterministic text and metadata normalizer for patent prior-art records.

    Preserves exact technical vocabulary, chemical/mathematical notations, and claim structure.
    Does NOT use an LLM and does NOT perform semantic alterations.
    """

    # Non-printable control characters excluding \t and \n
    _CONTROL_CHARS_REGEX = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")

    # Consecutive blank lines (3 or more -> 2)
    _EXCESSIVE_BLANKS_REGEX = re.compile(r"\n{3,}")

    # Standard date formats encountered in patent datasets
    _DATE_FORMATS = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y%m%d",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%Y.%m.%d",
    ]

    @classmethod
    def clean_text(cls, text: Optional[str]) -> str:
        """Normalizes whitespace and line breaks while preserving technical terminology,

        chemical formulae, mathematical symbols, and claim numbering.
        """
        if not text:
            return ""

        # 1. Normalize line endings to \n
        cleaned = text.replace("\r\n", "\n").replace("\r", "\n")

        # 2. Normalize unicode whitespace variants to standard space
        cleaned = cleaned.replace("\u00a0", " ").replace("\u200b", "").replace("\u3000", " ")

        # 3. Strip non-printable control characters
        cleaned = cls._CONTROL_CHARS_REGEX.sub("", cleaned)

        # 4. Clean trailing whitespace per line while preserving technical indentations
        lines = [re.sub(r"[ \t]+$", "", line) for line in cleaned.split("\n")]
        cleaned = "\n".join(lines)

        # 5. Collapse excessive blank lines (more than 2 consecutive newlines)
        cleaned = cls._EXCESSIVE_BLANKS_REGEX.sub("\n\n", cleaned)

        return cleaned.strip()

    @classmethod
    def normalize_empty(cls, val: Any) -> Optional[Any]:
        """Converts empty strings, whitespace-only strings, or placeholder strings ('N/A', 'none', 'null')

        consistently to None.
        """
        if val is None:
            return None
        if isinstance(val, str):
            s = val.strip()
            if not s or s.lower() in {"n/a", "none", "null", "undefined", "unknown"}:
                return None
            return s
        return val

    @classmethod
    def normalize_date(cls, val: Any) -> Optional[str]:
        """Parses and converts date inputs to canonical ISO 'YYYY-MM-DD' format.

        Returns None if invalid or unparseable.
        """
        if not val:
            return None

        if isinstance(val, (date, datetime)):
            return val.strftime("%Y-%m-%d")

        raw_str = str(val).strip()
        if not raw_str:
            return None

        for fmt in cls._DATE_FORMATS:
            try:
                dt = datetime.strptime(raw_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # Handle ISO with timestamp (e.g., 2023-05-12T00:00:00Z)
        try:
            dt = datetime.fromisoformat(raw_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass

        return None

    @classmethod
    def normalize_string_list(cls, items: Any) -> List[str]:
        """Deduplicates, strips whitespace, and preserves insertion order for lists of strings."""
        if not items:
            return []

        if isinstance(items, str):
            # Split semicolon or comma separated strings if passed as flat text
            parts = re.split(r"[;,]\s*", items)
        elif isinstance(items, (list, tuple, set)):
            parts = [str(x) for x in items]
        else:
            parts = [str(items)]

        cleaned_list: List[str] = []
        seen = set()

        for item in parts:
            c = item.strip()
            if c and c not in seen:
                seen.add(c)
                cleaned_list.append(c)

        return cleaned_list

    @classmethod
    def normalize_claims(cls, claims: Any) -> Optional[Union[List[str], str]]:
        """Normalizes claims field whether provided as list of strings or single block."""
        if not claims:
            return None

        if isinstance(claims, list):
            cleaned = [cls.clean_text(c) for c in claims if c and cls.clean_text(c)]
            return cleaned if cleaned else None

        if isinstance(claims, str):
            cleaned_str = cls.clean_text(claims)
            return cleaned_str if cleaned_str else None

        return None

    @classmethod
    def normalize_document(cls, raw: Dict[str, Any]) -> PatentDocumentBase:
        """Normalizes all fields of a raw patent record dictionary into a canonical PatentDocumentBase."""
        # 1. Patent Number & Identifiers
        patent_number = str(raw.get("patent_number") or raw.get("patentNumber") or raw.get("doc_number") or "").strip()
        pub_number = cls.normalize_empty(raw.get("publication_number") or raw.get("publicationNumber"))
        app_number = cls.normalize_empty(raw.get("application_number") or raw.get("applicationNumber") or raw.get("app_number"))

        # 2. Jurisdiction
        raw_country = str(raw.get("country_code") or raw.get("country") or raw.get("jurisdiction") or "US").strip().upper()
        country_code = raw_country if raw_country else "US"

        # 3. Core Text
        title = cls.clean_text(str(raw.get("title") or ""))
        abstract = cls.clean_text(str(raw.get("abstract") or ""))
        description = cls.clean_text(str(raw.get("description") or raw.get("full_text") or "")) or None
        claims = cls.normalize_claims(raw.get("claims"))

        # 4. Entities
        inventors = cls.normalize_string_list(raw.get("inventors") or raw.get("inventor"))
        assignee = cls.normalize_empty(raw.get("assignee") or raw.get("applicant"))

        # 5. Dates
        pub_date = cls.normalize_date(raw.get("publication_date") or raw.get("publicationDate"))
        filing_date = cls.normalize_date(raw.get("filing_date") or raw.get("filingDate"))
        priority_date = cls.normalize_date(raw.get("priority_date") or raw.get("priorityDate"))

        # 6. Classifications
        ipc_classes = cls.normalize_string_list(raw.get("ipc_classes") or raw.get("ipcClasses") or raw.get("ipc"))
        cpc_classes = cls.normalize_string_list(raw.get("cpc_classes") or raw.get("cpcClasses") or raw.get("cpc"))

        # 7. Provenance & Metadata
        language = str(raw.get("language") or "en").strip().lower()
        source = str(raw.get("source") or "custom").strip()
        metadata = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}

        # Capture any source URLs or retrieval dates into metadata
        if "source_url" in raw and "source_url" not in metadata:
            metadata["source_url"] = raw["source_url"]
        if "source_dataset" in raw and "source_dataset" not in metadata:
            metadata["source_dataset"] = raw["source_dataset"]
        if "retrieved_at" in raw and "retrieved_at" not in metadata:
            metadata["retrieved_at"] = raw["retrieved_at"]

        return PatentDocumentBase(
            patent_number=patent_number,
            publication_number=pub_number,
            application_number=app_number,
            country_code=country_code,
            title=title,
            abstract=abstract,
            inventors=inventors,
            assignee=assignee,
            publication_date=pub_date,
            filing_date=filing_date,
            priority_date=priority_date,
            ipc_classes=ipc_classes,
            cpc_classes=cpc_classes,
            language=language,
            source=source,
            metadata=metadata,
            claims=claims,
            description=description,
        )

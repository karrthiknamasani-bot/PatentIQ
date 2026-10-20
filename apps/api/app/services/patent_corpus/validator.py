import re
import hashlib
from typing import List, Set, Optional, Dict, Any
from app.schemas.patent import (
    PatentDocumentBase,
    PatentChunkCreate,
    CorpusValidationReport,
    ValidationIssue,
)


class PatentCorpusValidator:
    """Strict validation engine for patent prior-art records and chunks.

    Detects malformed fields, duplicate identifiers, date errors, and malformed chunks.
    Does NOT silently discard records; all issues are recorded in the validation report.
    """

    # 2-letter ISO/WIPO country codes (e.g., US, EP, WO, JP, CN, KR, GB, DE, CA, IN, etc.)
    _COUNTRY_CODE_REGEX = re.compile(r"^[A-Z]{2}$")

    # Valid ISO date format YYYY-MM-DD
    _ISO_DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    def __init__(self) -> None:
        self.seen_patent_numbers: Set[str] = set()
        self.seen_chunk_keys: Set[str] = set()
        self.issues: List[ValidationIssue] = []
        self.total_records = 0
        self.valid_records = 0
        self.invalid_records = 0
        self.warning_count = 0
        self.duplicate_patent_count = 0
        self.duplicate_chunk_count = 0

    def reset(self) -> None:
        """Resets validator state for a new batch or corpus validation run."""
        self.seen_patent_numbers.clear()
        self.seen_chunk_keys.clear()
        self.issues.clear()
        self.total_records = 0
        self.valid_records = 0
        self.invalid_records = 0
        self.warning_count = 0
        self.duplicate_patent_count = 0
        self.duplicate_chunk_count = 0

    def validate_document(self, doc: PatentDocumentBase) -> bool:
        """Validates a single patent document record.

        Returns True if the document is strictly valid (no ERRORs), False otherwise.
        """
        self.total_records += 1
        record_errors = 0

        p_num = doc.patent_number.strip() if doc.patent_number else ""

        # 1. Patent Number Existence
        if not p_num:
            self._add_issue("ERROR", patent_number=None, field="patent_number", message="Missing required patent_number identifier.")
            record_errors += 1
        else:
            # Duplicate check
            norm_num = p_num.upper()
            if norm_num in self.seen_patent_numbers:
                self._add_issue("ERROR", patent_number=p_num, field="patent_number", message=f"Duplicate patent identifier detected: '{p_num}'")
                self.duplicate_patent_count += 1
                record_errors += 1
            else:
                self.seen_patent_numbers.add(norm_num)

        # 2. Title validation
        if not doc.title or not doc.title.strip():
            self._add_issue("ERROR", patent_number=p_num, field="title", message="Patent title cannot be empty.")
            record_errors += 1

        # 3. Abstract validation
        if not doc.abstract or not doc.abstract.strip():
            self._add_issue("ERROR", patent_number=p_num, field="abstract", message="Patent abstract cannot be empty.")
            record_errors += 1

        # 4. Country code validation
        if not self._COUNTRY_CODE_REGEX.match(doc.country_code):
            self._add_issue("ERROR", patent_number=p_num, field="country_code", message=f"Invalid country code '{doc.country_code}'. Must be 2 uppercase letters.")
            record_errors += 1

        # 5. Date validation
        for date_field, date_val in [
            ("publication_date", doc.publication_date),
            ("filing_date", doc.filing_date),
            ("priority_date", doc.priority_date),
        ]:
            if date_val:
                date_str = str(date_val).strip()
                if not self._ISO_DATE_REGEX.match(date_str):
                    self._add_issue("WARNING", patent_number=p_num, field=date_field, message=f"Date '{date_str}' does not conform to ISO YYYY-MM-DD format.")
                    self.warning_count += 1

        # 6. Provenance check
        if not doc.source or not doc.source.strip():
            self._add_issue("WARNING", patent_number=p_num, field="source", message="Missing source provenance.")
            self.warning_count += 1

        if record_errors == 0:
            self.valid_records += 1
            return True
        else:
            self.invalid_records += 1
            return False

    def validate_chunks(self, chunks: List[PatentChunkCreate], patent_number: str) -> bool:
        """Validates generated chunks for a patent document.

        Ensures non-empty text, sequential chunk indices, valid claim numbers, and no duplicate chunks.
        """
        all_valid = True
        expected_index = 0

        for chunk in chunks:
            # 1. Text existence
            if not chunk.text or not chunk.text.strip():
                self._add_issue("ERROR", patent_number=patent_number, field="chunk.text", message=f"Chunk {chunk.chunk_index} has empty text.")
                all_valid = False

            # 2. Sequential indexing check
            if chunk.chunk_index != expected_index:
                self._add_issue("WARNING", patent_number=patent_number, field="chunk.chunk_index", message=f"Non-sequential chunk index: expected {expected_index}, got {chunk.chunk_index}.")
                self.warning_count += 1
            expected_index = chunk.chunk_index + 1

            # 3. Claims section claim_number validation
            if chunk.section == "claims":
                if chunk.claim_number is None or chunk.claim_number < 1:
                    self._add_issue("ERROR", patent_number=patent_number, field="chunk.claim_number", message=f"Claims section chunk {chunk.chunk_index} must have a positive claim_number (got {chunk.claim_number}).")
                    all_valid = False

            # 4. Duplicate chunk detection
            text_hash = hashlib.sha256(chunk.text.encode("utf-8")).hexdigest()[:16]
            chunk_key = f"{patent_number}:{chunk.section}:{text_hash}"
            if chunk_key in self.seen_chunk_keys:
                self._add_issue("WARNING", patent_number=patent_number, field="chunk.duplicate", message=f"Duplicate chunk content detected in section '{chunk.section}' for patent '{patent_number}'.")
                self.duplicate_chunk_count += 1
                self.warning_count += 1
            else:
                self.seen_chunk_keys.add(chunk_key)

        return all_valid

    def get_report(self) -> CorpusValidationReport:
        """Returns the compiled validation report."""
        return CorpusValidationReport(
            total_records_inspected=self.total_records,
            valid_records_count=self.valid_records,
            invalid_records_count=self.invalid_records,
            warning_count=self.warning_count,
            duplicate_patent_count=self.duplicate_patent_count,
            duplicate_chunk_count=self.duplicate_chunk_count,
            issues=self.issues,
            is_valid=(self.invalid_records == 0),
        )

    def _add_issue(self, severity: str, patent_number: Optional[str], field: Optional[str], message: str) -> None:
        self.issues.append(
            ValidationIssue(
                severity=severity,
                patent_number=patent_number,
                field=field,
                message=message,
            )
        )

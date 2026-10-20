import os
import json
import hashlib
from typing import Iterator, List, Dict, Any, Union
from app.schemas.patent import PatentDocumentBase
from app.services.patent_corpus.normalizer import PatentNormalizer


class PatentCorpusLoader:
    """Loads and streams patent prior-art records from JSON and JSONL files

    with flexible field mappings and memory-efficient streaming.
    """

    @classmethod
    def stream_jsonl(cls, filepath: str) -> Iterator[PatentDocumentBase]:
        """Memory-efficient streaming generator yielding normalized PatentDocumentBase

        records line-by-line from a JSONL file without loading the full file into memory.
        """
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"Corpus file not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                clean_line = line.strip()
                if not clean_line:
                    continue
                try:
                    raw_record = json.loads(clean_line)
                    if isinstance(raw_record, dict):
                        yield PatentNormalizer.normalize_document(raw_record)
                except json.JSONDecodeError as err:
                    # Malformed JSON line is converted to minimal record with parse error note
                    yield PatentDocumentBase(
                        patent_number="",
                        title="",
                        abstract="",
                        metadata={"parse_error": f"Line {line_no}: {str(err)}", "raw_line": clean_line[:100]},
                    )

    @classmethod
    def load_json(cls, filepath: str) -> List[PatentDocumentBase]:
        """Loads and normalizes records from a standard JSON file (array or single object)."""
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"Corpus file not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        records: List[PatentDocumentBase] = []
        if isinstance(data, list):
            for raw in data:
                if isinstance(raw, dict):
                    records.append(PatentNormalizer.normalize_document(raw))
        elif isinstance(data, dict):
            records.append(PatentNormalizer.normalize_document(data))

        return records

    @classmethod
    def load_file(cls, filepath: str) -> List[PatentDocumentBase]:
        """Automatically detects file format (.json or .jsonl) and returns normalized patent list."""
        _, ext = os.path.splitext(filepath.lower())
        if ext == ".jsonl":
            return list(cls.stream_jsonl(filepath))
        elif ext == ".json":
            return cls.load_json(filepath)
        else:
            # Attempt JSON first, fallback to JSONL
            try:
                return cls.load_json(filepath)
            except Exception:
                return list(cls.stream_jsonl(filepath))

    @classmethod
    def write_jsonl(
        cls,
        filepath: str,
        items: Union[Iterator[Any], List[Any]],
    ) -> int:
        """Writes items (Pydantic models or dicts) to a JSONL file.

        Returns total count of records written.
        """
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        count = 0
        with open(filepath, "w", encoding="utf-8") as f:
            for item in items:
                if hasattr(item, "model_dump"):
                    line_data = item.model_dump(mode="json", exclude_none=False)
                elif isinstance(item, dict):
                    line_data = item
                else:
                    line_data = dict(item)
                f.write(json.dumps(line_data, ensure_ascii=False) + "\n")
                count += 1
        return count

    @staticmethod
    def compute_file_sha256(filepath: str) -> str:
        """Calculates SHA-256 hex digest of a file for manifest checksums."""
        if not os.path.isfile(filepath):
            return ""
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

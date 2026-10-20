"""Tests for real USPTO patent pilot dataset and XML parsing resilience.

Verifies:
1. Manifest structure and checksum integrity
2. Pilot JSONL dataset existence and parseability
3. Uniqueness of patent identifiers (zero duplicates)
4. Non-truncation and presence of mandatory fields (title, abstract, claims, description)
5. Pydantic schema compatibility with PatentDocumentBase
6. XML parser error handling for malformed input
"""

import os
import sys
import json
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.schemas.patent import PatentDocumentBase
from scripts.extract_uspto_pilot import parse_patent_record

PILOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "real_patents_pilot"))
RAW_FILE = os.path.join(PILOT_DIR, "real_patents_pilot_raw.jsonl")
INGEST_FILE = os.path.join(PILOT_DIR, "real_patents_pilot_ingest.jsonl")
MANIFEST_FILE = os.path.join(PILOT_DIR, "manifest.json")


def test_manifest_integrity():
    """Verify manifest exists and contains accurate metadata and checksums."""
    assert os.path.exists(MANIFEST_FILE), f"Manifest file missing: {MANIFEST_FILE}"
    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["manifest_version"] == "1.0.0"
    assert manifest["source"]["source_filename"] == "ipg161011.xml"
    assert manifest["statistics"]["records_extracted"] == 100
    assert manifest["statistics"]["duplicate_count"] == 0
    assert manifest["statistics"]["xml_parse_errors"] == 0
    assert len(manifest["outputs"]) == 2
    for out in manifest["outputs"]:
        assert os.path.exists(out["path"])
        assert out["record_count"] == 100
        assert len(out["sha256"]) == 64


def test_pilot_dataset_exists_and_count():
    """Verify pilot JSONL files exist and contain exactly 100 non-empty JSON lines."""
    for filepath in [RAW_FILE, INGEST_FILE]:
        assert os.path.exists(filepath), f"Pilot file missing: {filepath}"
        with open(filepath, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        assert len(lines) == 100, f"Expected 100 records in {filepath}, found {len(lines)}"


def test_no_duplicate_patent_identifiers():
    """Verify that all 100 extracted patent numbers and publication numbers are unique."""
    with open(INGEST_FILE, "r", encoding="utf-8") as f:
        records = [json.loads(l) for l in f if l.strip()]

    patent_numbers = [r["patent_number"] for r in records]
    assert len(patent_numbers) == len(set(patent_numbers)), "Duplicate patent_number detected!"

    pub_numbers = [r["publication_number"] for r in records]
    assert len(pub_numbers) == len(set(pub_numbers)), "Duplicate publication_number detected!"


def test_mandatory_fields_present_and_unfabricated():
    """Verify that every record contains genuine, non-empty text across all core patent fields."""
    with open(INGEST_FILE, "r", encoding="utf-8") as f:
        records = [json.loads(l) for l in f if l.strip()]

    for r in records:
        # Patent identifier
        assert r["patent_number"].startswith("US-")
        assert len(r["patent_number"]) >= 8

        # Title
        assert isinstance(r["title"], str)
        assert len(r["title"].strip()) >= 5

        # Abstract
        assert isinstance(r["abstract"], str)
        assert len(r["abstract"].strip()) >= 20

        # Claims
        assert isinstance(r["claims"], list)
        assert len(r["claims"]) >= 1
        for claim in r["claims"]:
            assert isinstance(claim, str)
            assert len(claim.strip()) >= 10

        # Description
        assert isinstance(r["description"], str)
        assert len(r["description"].strip()) >= 100

        # Dates
        assert r["publication_date"] is not None
        assert len(r["publication_date"]) == 10  # YYYY-MM-DD
        assert r["filing_date"] is not None
        assert len(r["filing_date"]) == 10  # YYYY-MM-DD

        # Inventors
        assert isinstance(r["inventors"], list)
        assert len(r["inventors"]) >= 1

        # Provenance
        assert r["source"] == "uspto"
        assert r["language"] == "en"


def test_schema_conformity_with_patent_document_base():
    """Validate that every pilot record parses cleanly into the canonical PatentDocumentBase Pydantic model."""
    with open(INGEST_FILE, "r", encoding="utf-8") as f:
        records = [json.loads(l) for l in f if l.strip()]

    for r in records:
        doc = PatentDocumentBase(**r)
        assert doc.country_code == "US"
        assert doc.patent_number == r["patent_number"]
        assert doc.title == r["title"]
        assert doc.abstract == r["abstract"]
        assert doc.claims == r["claims"]
        assert doc.description == r["description"]


def test_xml_parser_error_handling_and_resilience():
    """Verify parser robustness against malformed XML, empty strings, and design patents."""
    # 1. Invalid XML syntax
    assert parse_patent_record("<us-patent-grant>unclosed tag") is None

    # 2. Empty XML string
    assert parse_patent_record("") is None

    # 3. Design patent (non-utility)
    design_xml = """<us-patent-grant>
        <application-reference appl-type="design">
            <document-id><doc-number>29123456</doc-number></document-id>
        </application-reference>
        <publication-reference>
            <document-id><country>US</country><doc-number>D123456</doc-number><kind>S1</kind></document-id>
        </publication-reference>
    </us-patent-grant>"""
    assert parse_patent_record(design_xml) is None

    # 4. Incomplete utility patent missing doc-number
    incomplete_xml = """<us-patent-grant>
        <application-reference appl-type="utility">
            <document-id><doc-number>12345678</doc-number></document-id>
        </application-reference>
        <publication-reference>
            <document-id><country>US</country></document-id>
        </publication-reference>
    </us-patent-grant>"""
    assert parse_patent_record(incomplete_xml) is None

import os
import json
import tempfile
import pytest
from app.schemas.patent import (
    PatentDocumentBase,
    PatentChunkCreate,
    CorpusManifest,
)
from app.services.patent_corpus.normalizer import PatentNormalizer
from app.services.patent_corpus.chunker import PatentCorpusChunker
from app.services.patent_corpus.validator import PatentCorpusValidator
from app.services.patent_corpus.loader import PatentCorpusLoader
from app.services.patent_corpus.models import (
    to_supabase_patent_document_row,
    to_supabase_patent_chunk_row,
    SECTION_CLAIMS,
    SECTION_ABSTRACT,
    SECTION_TITLE,
)


@pytest.fixture
def sample_raw_patent_dict():
    return {
        "patent_number": "US-10492811-B2",
        "publication_number": "US10492811B2",
        "application_number": "15/099881",
        "country_code": "US",
        "title": "Smart surgical instruments and systems with integrated sensor telemetry",
        "abstract": "A surgical instrument system includes an end effector and an electronic control system.",
        "inventors": ["David N. Plescia", "Jeffrey D. Messerly"],
        "assignee": "Cilag GmbH International",
        "publication_date": "2019-12-03",
        "filing_date": "2016-04-15",
        "priority_date": "2015-06-30",
        "ipc_classes": ["A61B 17/00"],
        "cpc_classes": ["A61B 2017/00015"],
        "language": "en",
        "source": "uspto",
        "metadata": {
            "source_url": "https://patents.google.com/patent/US10492811B2/en",
            "source_dataset": "USPTO Public Bulk Data",
        },
        "claims": [
            "Claim 1: A surgical instrument comprising an end effector and a sensor array.",
            "Claim 2: The surgical instrument of claim 1, further comprising an articulation joint.",
        ],
        "description": "Background of the Invention\nSurgical stapling requires precise force management.\n\nSummary of the Invention\nThe present invention provides sensor telemetry.",
    }


def test_normalization_whitespace_and_controls():
    """Verify deterministic whitespace normalization, control char removal, and math/formula preservation."""
    raw_text = "Line 1\r\nLine 2\u00a0with non-breaking\x07 space.\n\n\n\nLine 3: Formula H2O at 25°C ± 0.5Ω and α-phase."
    cleaned = PatentNormalizer.clean_text(raw_text)

    # Line endings normalized
    assert "\r" not in cleaned
    # Non-breaking space converted
    assert "\u00a0" not in cleaned
    # Control character \x07 removed
    assert "\x07" not in cleaned
    # Excessive blank lines collapsed
    assert "\n\n\n" not in cleaned
    # Symbols preserved
    assert "H2O" in cleaned
    assert "25°C" in cleaned
    assert "±" in cleaned
    assert "0.5Ω" in cleaned
    assert "α-phase" in cleaned


def test_metadata_preservation_and_field_mapping(sample_raw_patent_dict):
    """Verify raw patent dictionary is faithfully mapped to canonical PatentDocumentBase."""
    doc = PatentNormalizer.normalize_document(sample_raw_patent_dict)

    assert doc.patent_number == "US-10492811-B2"
    assert doc.country_code == "US"
    assert doc.title == "Smart surgical instruments and systems with integrated sensor telemetry"
    assert len(doc.inventors) == 2
    assert doc.assignee == "Cilag GmbH International"
    assert str(doc.publication_date) == "2019-12-03"
    assert "A61B 17/00" in doc.ipc_classes
    assert doc.metadata["source_dataset"] == "USPTO Public Bulk Data"


def test_json_loading(sample_raw_patent_dict):
    """Verify loading from standard JSON file."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump([sample_raw_patent_dict], f)
        temp_path = f.name

    try:
        docs = PatentCorpusLoader.load_json(temp_path)
        assert len(docs) == 1
        assert docs[0].patent_number == "US-10492811-B2"
    finally:
        os.remove(temp_path)


def test_jsonl_streaming_loading(sample_raw_patent_dict):
    """Verify line-by-line streaming generator on JSONL file."""
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        f.write(json.dumps(sample_raw_patent_dict) + "\n")
        # Add another record
        rec2 = {**sample_raw_patent_dict, "patent_number": "US-9880993-B2"}
        f.write(json.dumps(rec2) + "\n")
        temp_path = f.name

    try:
        stream = PatentCorpusLoader.stream_jsonl(temp_path)
        docs = list(stream)
        assert len(docs) == 2
        assert docs[0].patent_number == "US-10492811-B2"
        assert docs[1].patent_number == "US-9880993-B2"
    finally:
        os.remove(temp_path)


def test_claim_parsing_and_traceability():
    """Verify claims parsing maintains exact claim_number indexing."""
    chunker = PatentCorpusChunker(max_chars=1000)
    claims_text = (
        "Claim 1: An apparatus comprising a sensor and processor.\n\n"
        "Claim 2: The apparatus of claim 1, further comprising a wireless transmitter.\n\n"
        "Claim 3: The apparatus of claim 2, wherein the sensor is an optical sensor."
    )
    doc = PatentDocumentBase(
        patent_number="US-TEST-001",
        title="Test Patent",
        abstract="Test Abstract",
        claims=claims_text,
    )
    chunks = chunker.chunk_document(doc)
    claim_chunks = [c for c in chunks if c.section == SECTION_CLAIMS]

    assert len(claim_chunks) == 3
    assert claim_chunks[0].claim_number == 1
    assert claim_chunks[0].paragraph_id == "claim:1"
    assert claim_chunks[1].claim_number == 2
    assert claim_chunks[1].paragraph_id == "claim:2"
    assert claim_chunks[2].claim_number == 3
    assert claim_chunks[2].paragraph_id == "claim:3"


def test_patent_chunker_section_boundaries():
    """Verify narrative sections are kept separate and never blended."""
    chunker = PatentCorpusChunker(max_chars=1000)
    doc = PatentDocumentBase(
        patent_number="US-TEST-002",
        title="Apparatus and Method",
        abstract="This is the isolated abstract.",
        claims=["Claim 1: A device."],
        description="Background of the Invention\nThis is the background.\n\nDetailed Description\nThis is the detailed specification.",
    )
    chunks = chunker.chunk_document(doc)
    sections = [c.section for c in chunks]

    assert SECTION_TITLE in sections
    assert SECTION_ABSTRACT in sections
    assert SECTION_CLAIMS in sections
    assert "background" in sections
    assert "detailed_description" in sections

    # Check that abstract chunk contains only abstract text
    abstract_chunk = next(c for c in chunks if c.section == SECTION_ABSTRACT)
    assert abstract_chunk.text == "This is the isolated abstract."


def test_chunker_sentence_snapping_and_overlap():
    """Verify long narrative sections split cleanly at sentence boundaries with overlap."""
    chunker = PatentCorpusChunker(max_chars=120, overlap_chars=30)
    text = "First long sentence explaining technical concept. Second sentence describing component interactions. Third sentence concluding the passage."
    slices = chunker._split_text_with_overlap(text)

    assert len(slices) >= 2
    # Ensure each slice respects max_chars (or is a single sentence)
    for s in slices:
        assert len(s) <= 150


def test_validator_detects_duplicate_patents():
    """Verify validator catches duplicate patent numbers and flags an ERROR."""
    validator = PatentCorpusValidator()
    doc1 = PatentDocumentBase(patent_number="US-DUPLICATE", title="Patent A", abstract="Abstract A")
    doc2 = PatentDocumentBase(patent_number="US-DUPLICATE", title="Patent B", abstract="Abstract B")

    assert validator.validate_document(doc1) is True
    assert validator.validate_document(doc2) is False

    report = validator.get_report()
    assert report.is_valid is False
    assert report.duplicate_patent_count == 1
    assert any("Duplicate patent identifier" in i.message for i in report.issues)


def test_validator_detects_duplicate_chunks():
    """Verify validator catches identical duplicate chunks within the same patent."""
    validator = PatentCorpusValidator()
    chunks = [
        PatentChunkCreate(patent_number="US-1", chunk_index=0, section="abstract", text="Identical text body."),
        PatentChunkCreate(patent_number="US-1", chunk_index=1, section="abstract", text="Identical text body."),
    ]
    validator.validate_chunks(chunks, patent_number="US-1")
    report = validator.get_report()

    assert report.duplicate_chunk_count == 1
    assert report.warning_count >= 1


def test_validator_detects_malformed_records():
    """Verify validator catches missing identifiers, empty text, and invalid country codes."""
    validator = PatentCorpusValidator()
    # Missing patent number & empty title
    doc_bad = PatentDocumentBase(
        patent_number="",
        title="",
        abstract="",
        country_code="XYZ",  # invalid
    )
    is_valid = validator.validate_document(doc_bad)
    assert is_valid is False

    report = validator.get_report()
    assert report.invalid_records_count == 1
    error_fields = [i.field for i in report.issues if i.severity == "ERROR"]
    assert "patent_number" in error_fields
    assert "title" in error_fields
    assert "abstract" in error_fields


def test_to_supabase_schema_mapping(sample_raw_patent_dict):
    """Verify serialization to dictionary strictly matches Supabase PostgreSQL schema."""
    doc = PatentNormalizer.normalize_document(sample_raw_patent_dict)
    doc_row = to_supabase_patent_document_row(doc, doc_uuid="11111111-2222-3333-4444-555555555555")

    assert doc_row["id"] == "11111111-2222-3333-4444-555555555555"
    assert doc_row["patent_number"] == "US-10492811-B2"
    assert doc_row["publication_date"] == "2019-12-03"
    assert isinstance(doc_row["inventors"], list)
    assert isinstance(doc_row["metadata"], dict)

    chunk = PatentChunkCreate(
        patent_number="US-10492811-B2",
        chunk_index=0,
        section="claims",
        claim_number=1,
        text="Claim 1: A surgical instrument.",
    )
    chunk_row = to_supabase_patent_chunk_row(
        chunk=chunk,
        patent_id=doc_row["id"],
        chunk_uuid="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    )

    assert chunk_row["id"] == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    assert chunk_row["patent_id"] == "11111111-2222-3333-4444-555555555555"
    assert chunk_row["chunk_index"] == 0
    assert chunk_row["section"] == "claims"
    assert chunk_row["claim_number"] == 1
    assert chunk_row["embedding_status"] == "pending"


def test_end_to_end_corpus_pipeline():
    """Verify the entire ingestion, chunking, and manifest generation pipeline end-to-end."""
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_path = os.path.join(tmpdir, "raw.jsonl")
        norm_path = os.path.join(tmpdir, "norm.jsonl")
        chunks_path = os.path.join(tmpdir, "chunks.jsonl")
        manifest_path = os.path.join(tmpdir, "manifest.json")

        records = [
            {
                "patent_number": f"US-TEST-{i}",
                "title": f"Patent Title {i}",
                "abstract": f"Abstract text for patent {i}.",
                "claims": [f"Claim 1: A method {i}."],
                "country_code": "US",
                "source": "uspto",
            }
            for i in range(1, 4)
        ]

        with open(raw_path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        # 1. Load and normalize
        docs = PatentCorpusLoader.load_file(raw_path)
        assert len(docs) == 3

        # 2. Validate
        validator = PatentCorpusValidator()
        for d in docs:
            assert validator.validate_document(d) is True
        PatentCorpusLoader.write_jsonl(norm_path, docs)

        # 3. Chunk
        chunker = PatentCorpusChunker(max_chars=1000)
        chunks = []
        for d in docs:
            c = chunker.chunk_document(d)
            validator.validate_chunks(c, d.patent_number)
            chunks.extend(c)
        PatentCorpusLoader.write_jsonl(chunks_path, chunks)

        assert len(chunks) > 0

        # 4. Manifest
        checksums = {
            "raw": PatentCorpusLoader.compute_file_sha256(raw_path),
            "norm": PatentCorpusLoader.compute_file_sha256(norm_path),
            "chunks": PatentCorpusLoader.compute_file_sha256(chunks_path),
        }
        manifest = CorpusManifest(
            acquisition_date="2026-09-15",
            num_patents=len(docs),
            num_chunks=len(chunks),
            checksums=checksums,
        )
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest.model_dump(mode="json"), f)

        # Verify manifest on disk
        with open(manifest_path, "r", encoding="utf-8") as f:
            loaded_manifest = json.load(f)
        assert loaded_manifest["num_patents"] == 3
        assert loaded_manifest["num_chunks"] == len(chunks)
        assert len(loaded_manifest["checksums"]["raw"]) == 64

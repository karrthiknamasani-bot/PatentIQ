import pytest
from app.services.document_processing.section_detector import SectionDetector
from app.services.document_processing.chunker import PatentAwareChunker
from app.schemas.document import ExtractedSegment


def test_section_detector_common_headings():
    """Verify detection of various technical and patent section headings."""
    assert SectionDetector.detect_heading("Abstract") == "abstract"
    assert SectionDetector.detect_heading("Executive Abstract:") == "abstract"
    assert SectionDetector.detect_heading("1. Background of the Invention") == "background"
    assert SectionDetector.detect_heading("Prior Art") == "background"
    assert SectionDetector.detect_heading("Summary of the Invention") == "summary"
    assert SectionDetector.detect_heading("Detailed Description of Preferred Embodiments") == "detailed_description"
    assert SectionDetector.detect_heading("Claims") == "claims"
    assert SectionDetector.detect_heading("Patent Claims") == "claims"
    assert SectionDetector.detect_heading("What is claimed is:") == "claims"
    assert SectionDetector.detect_heading("Technical Field") == "technical_field"
    assert SectionDetector.detect_heading("Commercial Applications") == "applications"
    assert SectionDetector.detect_heading("Conclusions and Future Work") == "conclusion"


def test_section_detector_unknown_fallback():
    """Verify that arbitrary narrative lines return None/unknown."""
    assert SectionDetector.detect_heading("The rotor turns at 5000 RPM.") is None
    assert SectionDetector.classify_segment("Random paragraph text.") == "unknown"


def test_claim_detection_in_chunker():
    """Verify detection of claim numbers across standard patent numbering patterns."""
    assert PatentAwareChunker.detect_claim_number("Claim 1: A method comprising...")[0] == 1
    assert PatentAwareChunker.detect_claim_number("Patent Claim 4. The device of claim 1...")[0] == 4
    assert PatentAwareChunker.detect_claim_number("12. An apparatus comprising...", is_claims_section=True)[0] == 12
    assert PatentAwareChunker.detect_claim_number("(3) The system of claim 1...", is_claims_section=True)[0] == 3
    assert PatentAwareChunker.detect_claim_number("Just normal text.")[0] is None


def test_chunker_keeps_claims_intact():
    """Verify that claims under max_chars are each preserved as discrete, unbroken chunks."""
    segments = [
        ExtractedSegment(
            text="Claim 1: A first component coupled to a second component.\n\n"
                 "Claim 2: The system of claim 1, further comprising a sensor.",
            section="claims",
            page_number=3,
            source_reference="page:3",
        )
    ]
    chunker = PatentAwareChunker(max_chars=500, overlap_chars=100)
    chunks = chunker.chunk_document(segments)

    assert len(chunks) == 2
    assert chunks[0].claim_number == 1
    assert chunks[0].section == "claims"
    assert chunks[0].page_number == 3
    assert chunks[1].claim_number == 2
    assert chunks[1].section == "claims"


def test_chunker_respects_section_boundaries():
    """Verify chunks never merge text from different sections."""
    segments = [
        ExtractedSegment(text="Short abstract text.", section="abstract", page_number=1),
        ExtractedSegment(text="Short background text.", section="background", page_number=1),
    ]
    chunker = PatentAwareChunker(max_chars=1000, overlap_chars=200)
    chunks = chunker.chunk_document(segments)

    assert len(chunks) == 2
    assert chunks[0].section == "abstract"
    assert chunks[1].section == "background"


def test_chunker_splits_oversized_narrative_with_overlap():
    """Verify long paragraphs are split into overlapping chunks snapping to sentences."""
    sentence = "This is an important technical statement regarding rotor stability. "
    long_text = sentence * 25  # ~1750 chars

    segments = [
        ExtractedSegment(text=long_text, section="detailed_description", page_number=2)
    ]
    chunker = PatentAwareChunker(max_chars=600, overlap_chars=100)
    chunks = chunker.chunk_document(segments)

    assert len(chunks) > 1
    for c in chunks:
        assert len(c.text) <= 650  # Snapping allows slight variation
        assert c.section == "detailed_description"
        assert c.token_estimate > 0

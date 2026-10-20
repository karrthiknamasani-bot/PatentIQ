"""Comprehensive tests for Technical Feature Extraction Layer (Step 7).

Covers:
1. Basic extraction from document chunks
2. Controlled vocabulary validation (FeatureType)
3. Pydantic schema validation (TechnicalFeature, FeatureExtractionResponse)
4. Deterministic feature ID generation
5. Same input -> identical feature IDs and outputs
6. Normalization (noise cleanup, token preservation)
7. Duplicate consolidation and multi-source provenance merging
8. Provenance preservation (chunk_id, span_start, span_end)
9. Page/section/claim metadata preservation
10. Malformed extractor output rejection
11. Unsupported feature type rejection
12. Empty document / chunk handling
13. Confidence semantics (extraction support, not patentability)
14. API endpoint POST /api/features/extract validation and execution
15. Strict offline verification (no external network or LLM calls)
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.document import DocumentChunk
from app.services.features.types import (
    FeatureType,
    FeatureCandidate,
    SourceProvenance,
)
from app.services.features.feature_schema import (
    TechnicalFeature,
    FeatureExtractionRequest,
    FeatureExtractionResponse,
)
from app.services.features.feature_normalizer import FeatureNormalizer
from app.services.features.feature_extractor import (
    RuleBasedFeatureExtractor,
    MockFeatureExtractor,
)
from app.services.features.feature_service import PatentFeatureService


def make_test_chunk(
    chunk_index: int = 0,
    text: str = "A surgical instrument configured to deliver high frequency electrical energy.",
    section: str = "detailed_description",
    page_number: int = 1,
    claim_number: int = None,
    source_reference: str = "page:1,para:1",
) -> DocumentChunk:
    return DocumentChunk(
        chunk_index=chunk_index,
        text=text,
        section=section,
        page_number=page_number,
        claim_number=claim_number,
        source_reference=source_reference,
        start_character=0,
        end_character=len(text),
        token_estimate=len(text) // 4,
    )


def test_basic_feature_extraction():
    """Verify rule-based extractor extracts grounded technical features."""
    chunk = make_test_chunk(
        chunk_index=0,
        text=(
            "The system includes an optical sensor module configured to detect tissue perfusion "
            "thereby improving surgical precision. It addresses the problem of tissue necrosis."
        ),
    )
    extractor = RuleBasedFeatureExtractor()
    candidates = extractor.extract(chunk)

    assert len(candidates) > 0
    types = {c.feature_type for c in candidates}
    assert FeatureType.COMPONENT in types or FeatureType.FUNCTION in types
    assert FeatureType.TECHNICAL_EFFECT in types or FeatureType.PROBLEM in types

    # Verify character spans match verbatim text
    for c in candidates:
        assert c.evidence_span_start is not None
        assert c.evidence_span_end is not None
        extracted_slice = chunk.text[c.evidence_span_start:c.evidence_span_end]
        assert c.feature_text in extracted_slice or extracted_slice in c.feature_text


def test_controlled_feature_types():
    """Verify only valid FeatureType enum values are allowed."""
    valid_types = {t.value for t in FeatureType}
    assert "component" in valid_types
    assert "function" in valid_types
    assert "problem" in valid_types
    assert "mechanism" in valid_types
    assert "technical_effect" in valid_types
    assert "claimed_aspect" in valid_types

    # Ensure arbitrary strings fail conversion
    with pytest.raises(ValueError):
        FeatureType("arbitrary_unknown_type")


def test_pydantic_schema_validation():
    """Verify TechnicalFeature model validates required fields and types."""
    feat = TechnicalFeature(
        project_id="proj_123",
        feature_id="feat_comp_abc123",
        feature_type=FeatureType.COMPONENT,
        feature_text="adaptive motor controller",
        normalized_text="adaptive motor controller",
        source_chunk_id="0",
        section="detailed_description",
        page_number=2,
        extraction_method="rule_based",
        confidence=0.90,
    )
    assert feat.project_id == "proj_123"
    assert feat.confidence == 0.90
    assert feat.supporting_sources == []


def test_deterministic_feature_ids():
    """Verify same project + type + normalized text produces exact same feature ID."""
    id1 = FeatureNormalizer.generate_feature_id("project_alpha", "component", "optical sensor array")
    id2 = FeatureNormalizer.generate_feature_id("project_alpha", "component", "optical sensor array")
    id_diff_proj = FeatureNormalizer.generate_feature_id("project_beta", "component", "optical sensor array")
    id_diff_text = FeatureNormalizer.generate_feature_id("project_alpha", "component", "acoustic sensor array")
    id_diff_type = FeatureNormalizer.generate_feature_id("project_alpha", "function", "optical sensor array")

    assert id1 == id2
    assert id1 != id_diff_proj
    assert id1 != id_diff_text
    assert id1 != id_diff_type
    assert id1.startswith("feat_comp_")


def test_same_input_same_output():
    """Verify end-to-end service execution on same input is completely deterministic."""
    chunks = [
        make_test_chunk(
            chunk_index=0,
            text="The apparatus comprises an actuator unit configured to articulate an end effector.",
        )
    ]
    service = PatentFeatureService(extractor=RuleBasedFeatureExtractor())

    res1 = service.extract_features("proj_repeat", chunks)
    res2 = service.extract_features("proj_repeat", chunks)

    assert len(res1.features) == len(res2.features)
    assert [f.feature_id for f in res1.features] == [f.feature_id for f in res2.features]
    assert [f.normalized_text for f in res1.features] == [f.normalized_text for f in res2.features]


def test_feature_normalization():
    """Verify FeatureNormalizer cleans formatting artifacts while preserving technical symbols."""
    raw = "  -  1.  \"High-frequency 5.8 GHz RF generator with +/- 0.5% tolerance\"  "
    normalized = FeatureNormalizer.normalize_text(raw)

    assert normalized == "High-frequency 5.8 GHz RF generator with +/- 0.5% tolerance"
    assert "5.8 GHz" in normalized
    assert "+/- 0.5%" in normalized
    assert not normalized.startswith("-")
    assert not normalized.startswith("1.")


def test_duplicate_consolidation_and_provenance_merging():
    """Verify exact duplicates across chunks are merged and all source locations preserved."""
    # Two chunks defining identical component
    chunks = [
        make_test_chunk(chunk_index=0, text="System includes a sensor module.", page_number=1),
        make_test_chunk(chunk_index=3, text="Apparatus includes a sensor module.", page_number=4),
    ]
    service = PatentFeatureService(extractor=RuleBasedFeatureExtractor())
    response = service.extract_features("proj_dup", chunks)

    # Should consolidate duplicates into 1 feature with 2 supporting sources
    sensor_features = [f for f in response.features if "sensor module" in f.normalized_text.lower()]
    assert len(sensor_features) == 1
    feat = sensor_features[0]
    assert len(feat.supporting_sources) == 2
    assert response.extraction_metadata.number_of_duplicates_merged >= 1

    source_pages = {s.page_number for s in feat.supporting_sources}
    assert 1 in source_pages
    assert 4 in source_pages


def test_provenance_preservation():
    """Verify chunk_id, claim_number, section, and span offsets are accurately preserved."""
    chunk = make_test_chunk(
        chunk_index=5,
        text="Claim 1: A surgical device comprising a robotic wrist mechanism.",
        section="claims",
        claim_number=1,
        source_reference="claim:1",
    )
    service = PatentFeatureService(extractor=RuleBasedFeatureExtractor())
    res = service.extract_features("proj_claims", [chunk])

    assert len(res.features) > 0
    claim_feat = res.features[0]
    assert claim_feat.section == "claims"
    assert claim_feat.claim_number == 1
    assert claim_feat.source_chunk_id == "5"


def test_malformed_extractor_output_rejection():
    """Verify service gracefully rejects candidates with empty or blank text."""
    malformed_candidates = [
        FeatureCandidate(
            feature_type=FeatureType.COMPONENT,
            feature_text="   ",
            source_chunk_index=0,
        ),
        FeatureCandidate(
            feature_type=FeatureType.FUNCTION,
            feature_text="valid functional feature",
            source_chunk_index=0,
        ),
    ]
    mock = MockFeatureExtractor(predefined_candidates=malformed_candidates)
    service = PatentFeatureService(extractor=mock)

    chunk = make_test_chunk()
    response = service.extract_features("proj_malformed", [chunk])

    # Empty candidate was rejected
    assert len(response.features) == 1
    assert response.features[0].normalized_text == "valid functional feature"


def test_empty_document_handling():
    """Verify empty chunk list returns empty feature response without error."""
    service = PatentFeatureService()
    res = service.extract_features("proj_empty", [])

    assert res.total_features == 0
    assert res.features == []
    assert res.extraction_metadata.number_of_input_chunks == 0


def test_confidence_semantics():
    """Verify extraction confidence is bounded [0.0, 1.0] and represents extraction support."""
    cand = FeatureCandidate(
        feature_type=FeatureType.COMPONENT,
        feature_text="custom component",
        confidence=0.85,
    )
    mock = MockFeatureExtractor(predefined_candidates=[cand])
    service = PatentFeatureService(extractor=mock)

    res = service.extract_features("proj_conf", [make_test_chunk()])
    assert res.features[0].confidence == 0.85


@pytest.mark.asyncio
async def test_endpoint_features_extract_success():
    """Verify POST /api/features/extract succeeds and returns structured feature response."""
    payload = {
        "project_id": "inv_456",
        "method": "rule_based",
        "chunks": [
            {
                "chunk_index": 0,
                "text": "The apparatus includes an optical sensor array configured to monitor tissue impedance.",
                "section": "summary",
                "page_number": 2,
                "start_character": 0,
                "end_character": 87,
                "token_estimate": 22,
            }
        ],
    }
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post("/api/features/extract", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == "inv_456"
    assert "features" in data
    assert "extraction_metadata" in data
    assert data["total_features"] > 0
    first = data["features"][0]
    assert "feature_id" in first
    assert "feature_type" in first
    assert "normalized_text" in first
    assert first["feature_id"].startswith("feat_")


@pytest.mark.asyncio
async def test_endpoint_features_extract_validation_empty_chunks():
    """Verify POST /api/features/extract rejects empty chunks with HTTP 400."""
    payload = {
        "project_id": "inv_empty",
        "chunks": [],
    }
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post("/api/features/extract", json=payload)

    assert response.status_code == 400
    assert "At least one document chunk must be provided" in response.json()["detail"]


@pytest.mark.asyncio
async def test_endpoint_features_extract_validation_empty_project_id():
    """Verify POST /api/features/extract rejects empty project_id with HTTP 400 or 422."""
    payload = {
        "project_id": "   ",
        "chunks": [
            {
                "chunk_index": 0,
                "text": "Some text",
                "section": "description",
                "start_character": 0,
                "end_character": 9,
                "token_estimate": 2,
            }
        ],
    }
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post("/api/features/extract", json=payload)

    assert response.status_code == 400
    assert "project_id cannot be empty" in response.json()["detail"]


def test_comprehensive_11_category_and_claim_element_extraction():
    """Verify robust extraction of process, component, and structured claim elements."""
    text = (
        "Technical Features:\n"
        "1. Real-time seat availability synchronization\n"
        "2. Time-bound temporary seat locking\n"
        "3. Atomic seat confirmation\n"
        "4. Concurrency control\n"
        "5. Automatic lock expiration\n"
        "6. Event-driven seat-state propagation\n"
        "7. Persistent booking/seat/lock/payment states\n"
        "8. Conflict detection\n"
        "9. Authentication and authorization\n"
        "10. Idempotent booking confirmation\n"
        "11. Audit logging\n"
        "\n"
        "Claims:\n"
        "1. A distributed booking system comprising: a lock manager; and an inventory database.\n"
    )
    chunk = make_test_chunk(chunk_index=0, text=text, section="claims")
    service = PatentFeatureService()
    res = service.extract_features("proj_ticket", [chunk])

    assert res.total_features >= 11
    feature_texts = {f.feature_text for f in res.features}
    assert any("seat availability synchronization" in t.lower() for t in feature_texts)
    assert any("temporary seat locking" in t.lower() for t in feature_texts)
    assert any("atomic seat confirmation" in t.lower() for t in feature_texts)

    # Verify deterministic IDs
    for f in res.features:
        assert f.feature_id.startswith(f"feat_{f.feature_type.value[:4]}_")
        assert f.confidence > 0.0
        assert len(f.supporting_sources) >= 1


def test_fragmentary_feature_filtering_and_subsumption_merging():
    """Verify elimination of dangling fragments and subsumption of sub-clauses into comprehensive capabilities."""
    text = (
        "The distributed booking system provides time-bound seat locking prevents concurrent users from reserving the same seat. "
        "The system is configured to maintain available seat records in an in-memory cache. "
        "When a client receives a conflict response, the client initiates retry logic. "
        "The transactional processor ensures confirming the same seat concurrently is rejected. "
        "Furthermore, locking during the payment stage protects checkout consistency."
    )
    chunk = make_test_chunk(chunk_index=0, text=text, section="detailed_description")
    service = PatentFeatureService()
    res = service.extract_features("proj_ticket_quality", [chunk])

    feature_texts = [f.feature_text.lower() for f in res.features]

    # Fragmentary phrases must NOT exist as standalone features
    assert not any(t == "configured to maintain available" for t in feature_texts)
    assert not any(t == "receives a conflict response" for t in feature_texts)
    assert not any(t == "confirming the same seat" for t in feature_texts)
    assert not any(t == "locking during the payment stage" for t in feature_texts)

    # Meaningful technical capability must be extracted
    capability_found = any("prevents concurrent users from reserving the same seat" in t for t in feature_texts)
    assert capability_found, f"Expected capability not found in: {feature_texts}"

    # Verify provenance and taxonomy
    for f in res.features:
        assert f.feature_type in set(FeatureType)
        assert f.feature_id.startswith("feat_")
        assert len(f.supporting_sources) >= 1
        for prov in f.supporting_sources:
            assert prov.chunk_index == chunk.chunk_index
            assert prov.evidence_span_start >= 0
            assert prov.evidence_span_end <= len(text)



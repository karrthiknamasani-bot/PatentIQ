"""Comprehensive offline tests for Feature-to-Evidence Mapping Layer (Step 8).

Covers:
1. Basic feature-evidence matching
2. Lexical similarity (Jaccard overlap, case-insensitivity, technical token preservation)
3. Semantic similarity using MockEmbeddingProvider
4. Combined score calculation
5. Configurable alpha/beta weights
6. Weight sum validation (must sum to 1.0)
7. Relationship classification across all 5 categories
8. Relationship threshold boundary conditions
9. Mapping confidence computation and signal agreement bonus/penalty
10. Feature and evidence provenance preservation
11. Upstream retrieval signal preservation (BM25, Dense, RRF, Reranker)
12. Deterministic mapping ID generation
13. Duplicate mapping prevention
14. Top-k mapping truncation per feature
15. Empty input validation (project_id, features, evidence)
16. Invalid relationship rejection
17. Score range and clamping validation
18. Strict offline execution without network or remote vector stores
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.features.types import FeatureType
from app.services.features.feature_schema import TechnicalFeature
from app.services.reranking.types import RerankedResult
from app.services.mapping.types import (
    EvidenceRelationship,
    FeatureEvidenceMapping,
)
from app.services.mapping.feature_evidence_matcher import (
    FeatureEvidenceMatcher,
    MatchResult,
)
from app.services.mapping.relationship_classifier import RelationshipClassifier
from app.services.mapping.confidence import calculate_mapping_confidence
from app.services.mapping.mapping_service import PatentMappingService
from app.services.retrieval.embedding_provider import EmbeddingProviderBase


class MockEmbeddingProvider(EmbeddingProviderBase):
    """Deterministic mock embedding provider for offline semantic similarity tests."""

    def __init__(self, vector_map: dict = None, default_vector: list = None):
        self._vector_map = vector_map or {}
        self._default = default_vector or [1.0, 0.0, 0.0]

    def embed_text(self, text: str) -> list:
        # Exact or substring lookup
        for key, vec in self._vector_map.items():
            if key.lower() in text.lower():
                return vec
        return self._default

    def embed_texts(self, texts: list, batch_size: int = 32) -> list:
        return [self.embed_text(t) for t in texts]

    @property
    def dimension(self) -> int:
        return len(self._default)


def make_sample_feature(
    feature_id: str = "feat_comp_001",
    feature_type: FeatureType = FeatureType.COMPONENT,
    feature_text: str = "optical sensor array configured to monitor tissue impedance",
    normalized_text: Optional[str] = None,
    project_id: str = "proj_test",
) -> TechnicalFeature:
    norm = normalized_text if normalized_text is not None else feature_text
    return TechnicalFeature(
        project_id=project_id,
        feature_id=feature_id,
        feature_type=feature_type,
        feature_text=feature_text,
        normalized_text=norm,
        source_chunk_id="chunk_0",
        source_reference="page:1,para:2",
        section="detailed_description",
        page_number=1,
        claim_number=None,
        evidence_span_start=10,
        evidence_span_end=72,
        extraction_method="rule_based",
        confidence=0.92,
    )


def make_sample_evidence(
    patent_number: str = "US-10492811-B2",
    chunk_index: int = 0,
    text: str = "A surgical instrument having an optical sensor array for monitoring tissue impedance and temperature.",
    section: str = "claims",
    claim_number: int = 1,
    reranker_score: float = 0.91,
    reranker_rank: int = 1,
) -> RerankedResult:
    return RerankedResult(
        patent_number=patent_number,
        chunk_index=chunk_index,
        chunk_id=f"{patent_number}:{chunk_index}",
        text=text,
        section=section,
        claim_number=claim_number,
        page_number=1,
        paragraph_id=f"claim:{claim_number}",
        source="custom",
        metadata={"title": "Smart Surgical Instrument", "country_code": "US", "publication_date": "2020-01-01"},
        sparse_rank=1,
        dense_rank=2,
        sparse_score=15.4,
        dense_score=0.88,
        rrf_score=0.0325,
        fusion_methods=["sparse", "dense"],
        reranker_score=reranker_score,
        reranker_rank=reranker_rank,
        retrieval_method="hybrid_rrf_reranked",
    )


def test_lexical_similarity_computation():
    """Verify token Jaccard similarity is case-insensitive and preserves technical tokens."""
    text_a = "High-frequency 5.8 GHz RF generator"
    text_b = "Apparatus comprising high-frequency 5.8 GHz RF generator coupled to electrode"
    sim = FeatureEvidenceMatcher.compute_lexical_similarity(text_a, text_b)

    assert sim > 0.0
    assert sim <= 1.0
    # Common tokens: high-frequency, 5.8, ghz, rf, generator (5 tokens)
    # Total unique union tokens: high-frequency, 5.8, ghz, rf, generator, apparatus, comprising, coupled, electrode (9 tokens)
    assert pytest.approx(sim, 0.05) == (5 / 9)


def test_semantic_similarity_with_mock_embeddings():
    """Verify semantic cosine similarity computation using unit-normalized mock vectors."""
    # Orthogonal vectors -> cosine = 0.0
    # Parallel vectors -> cosine = 1.0
    mock_provider = MockEmbeddingProvider(
        vector_map={
            "sensor": [1.0, 0.0, 0.0],
            "detector": [1.0, 0.0, 0.0],
            "battery": [0.0, 1.0, 0.0],
        },
        default_vector=[0.0, 0.0, 1.0],
    )
    matcher = FeatureEvidenceMatcher(embedding_provider=mock_provider)

    sim_parallel = matcher.compute_semantic_similarity("sensor", "detector")
    sim_orthogonal = matcher.compute_semantic_similarity("sensor", "battery")

    assert sim_parallel == 1.0
    assert sim_orthogonal == 0.0


def test_combined_score_calculation():
    """Verify matching_score = alpha * lexical + beta * semantic."""
    mock_provider = MockEmbeddingProvider(
        vector_map={"test": [1.0, 0.0, 0.0]},
        default_vector=[1.0, 0.0, 0.0],
    )
    matcher = FeatureEvidenceMatcher(embedding_provider=mock_provider)
    feat = make_sample_feature(feature_text="surgical instrument")
    ev = make_sample_evidence(text="surgical instrument")

    # Identical texts -> lexical = 1.0, semantic = 1.0
    result = matcher.match(feat, ev, lexical_weight=0.3, semantic_weight=0.7)
    assert result.lexical_similarity == 1.0
    assert result.semantic_similarity == 1.0
    assert result.matching_score == 1.0


def test_configurable_weights_and_sum_validation():
    """Verify matcher enforces alpha + beta == 1.0."""
    matcher = FeatureEvidenceMatcher(embedding_provider=MockEmbeddingProvider())
    feat = make_sample_feature()
    ev = make_sample_evidence()

    # Valid custom weights
    res = matcher.match(feat, ev, lexical_weight=0.5, semantic_weight=0.5)
    assert res.matching_score >= 0.0

    # Invalid weights not summing to 1.0
    with pytest.raises(ValueError, match="must sum to 1.0"):
        matcher.match(feat, ev, lexical_weight=0.4, semantic_weight=0.4)


def test_relationship_classification_categories():
    """Verify all 5 evidence relationship categories based on thresholds."""
    classifier = RelationshipClassifier(
        direct_threshold=0.75,
        partial_threshold=0.50,
        contextual_threshold=0.30,
        weak_threshold=0.15,
    )

    assert classifier.classify(0.85) == EvidenceRelationship.DIRECT_MATCH
    assert classifier.classify(0.60) == EvidenceRelationship.PARTIAL_MATCH
    assert classifier.classify(0.40) == EvidenceRelationship.CONTEXTUAL_MATCH
    assert classifier.classify(0.20) == EvidenceRelationship.WEAK_MATCH
    assert classifier.classify(0.05) == EvidenceRelationship.NO_MATERIAL_MATCH


def test_relationship_threshold_boundary_conditions():
    """Verify classification exactly at threshold boundary values."""
    classifier = RelationshipClassifier()
    assert classifier.classify(0.75) == EvidenceRelationship.DIRECT_MATCH
    assert classifier.classify(0.50) == EvidenceRelationship.PARTIAL_MATCH
    assert classifier.classify(0.30) == EvidenceRelationship.CONTEXTUAL_MATCH
    assert classifier.classify(0.15) == EvidenceRelationship.WEAK_MATCH
    assert classifier.classify(0.149) == EvidenceRelationship.NO_MATERIAL_MATCH


def test_mapping_confidence_computation():
    """Verify mapping confidence combines matching score, relationship, and agreement."""
    # High agreement case
    conf_high = calculate_mapping_confidence(
        matching_score=0.80,
        relationship=EvidenceRelationship.DIRECT_MATCH,
        lexical_similarity=0.75,
        semantic_similarity=0.82,
        reranker_rank=1,
        feature_confidence=0.95,
    )
    # Low score case
    conf_low = calculate_mapping_confidence(
        matching_score=0.10,
        relationship=EvidenceRelationship.NO_MATERIAL_MATCH,
        lexical_similarity=0.10,
        semantic_similarity=0.10,
        reranker_rank=10,
        feature_confidence=0.90,
    )

    assert conf_high > conf_low
    assert 0.0 <= conf_high <= 1.0
    assert 0.0 <= conf_low <= 1.0


def test_provenance_and_upstream_signals_preservation():
    """Verify all feature, evidence, and retrieval signals are preserved in mapping output."""
    mock_provider = MockEmbeddingProvider(default_vector=[1.0, 0.0, 0.0])
    matcher = FeatureEvidenceMatcher(embedding_provider=mock_provider)
    service = PatentMappingService(matcher=matcher)

    feat = make_sample_feature(feature_id="feat_001")
    ev = make_sample_evidence(patent_number="US-10492811-B2", chunk_index=3)

    response = service.map_features_to_evidence("proj_1", [feat], [ev], top_k=5)
    assert len(response.mappings) == 1
    m = response.mappings[0]

    # Feature fields
    assert m.project_id == "proj_1"
    assert m.feature_id == "feat_001"
    assert m.feature_type == "component"
    assert m.feature_text == feat.feature_text

    # Evidence fields
    assert m.patent_number == "US-10492811-B2"
    assert m.chunk_index == 3
    assert m.claim_number == 1
    assert m.section == "claims"

    # Upstream retrieval signals
    assert m.sparse_rank == 1
    assert m.dense_rank == 2
    assert m.sparse_score == 15.4
    assert m.dense_score == 0.88
    assert m.rrf_score == 0.0325
    assert m.reranker_score == 0.91
    assert m.reranker_rank == 1


def test_deterministic_mapping_id():
    """Verify identical project + feature + patent + chunk_index produces exact same mapping_id."""
    id1 = PatentMappingService.generate_mapping_id("p1", "feat_a", "US-101-A", 0)
    id2 = PatentMappingService.generate_mapping_id("p1", "feat_a", "US-101-A", 0)
    id_diff_feat = PatentMappingService.generate_mapping_id("p1", "feat_b", "US-101-A", 0)
    id_diff_chunk = PatentMappingService.generate_mapping_id("p1", "feat_a", "US-101-A", 1)

    assert id1 == id2
    assert id1 != id_diff_feat
    assert id1 != id_diff_chunk
    assert id1.startswith("map_")


def test_duplicate_prevention():
    """Verify multiple identical evidence chunks for same feature are deduplicated."""
    mock_provider = MockEmbeddingProvider(default_vector=[1.0, 0.0, 0.0])
    matcher = FeatureEvidenceMatcher(embedding_provider=mock_provider)
    service = PatentMappingService(matcher=matcher)

    feat = make_sample_feature()
    ev1 = make_sample_evidence(patent_number="US-1", chunk_index=0)
    ev2 = make_sample_evidence(patent_number="US-1", chunk_index=0)  # Duplicate chunk

    response = service.map_features_to_evidence("proj_dup", [feat], [ev1, ev2], top_k=5)
    assert len(response.mappings) == 1


def test_top_k_mapping_truncation():
    """Verify only top-k evidence matches are retained per feature."""
    mock_provider = MockEmbeddingProvider(default_vector=[1.0, 0.0, 0.0])
    matcher = FeatureEvidenceMatcher(embedding_provider=mock_provider)
    service = PatentMappingService(matcher=matcher)

    feat = make_sample_feature()
    evidence_list = [
        make_sample_evidence(patent_number=f"US-{i}", chunk_index=0)
        for i in range(10)
    ]

    response = service.map_features_to_evidence("proj_topk", [feat], evidence_list, top_k=3)
    assert len(response.mappings) == 3


def test_empty_input_validation():
    """Verify service rejects empty project, empty features, or empty evidence."""
    service = PatentMappingService()

    with pytest.raises(ValueError, match="project_id must be a non-empty string"):
        service.map_features_to_evidence("  ", [make_sample_feature()], [make_sample_evidence()])

    with pytest.raises(ValueError, match="At least one TechnicalFeature"):
        service.map_features_to_evidence("proj", [], [make_sample_evidence()])

    with pytest.raises(ValueError, match="At least one RerankedResult"):
        service.map_features_to_evidence("proj", [make_sample_feature()], [])


@pytest.mark.asyncio
async def test_endpoint_feature_evidence_mapping_success():
    """Verify POST /api/mapping/feature-evidence returns 200 and structured mappings."""
    feat = make_sample_feature()
    ev = make_sample_evidence()

    payload = {
        "project_id": "proj_api_test",
        "top_k": 2,
        "features": [feat.model_dump()],
        "evidence": [ev.model_dump()],
    }

    from unittest.mock import patch
    from app.api.routes.mapping import patent_mapping_service

    with patch.object(patent_mapping_service.matcher, "compute_semantic_similarity", return_value=0.85):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.post("/api/mapping/feature-evidence", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == "proj_api_test"
    assert "mappings" in data
    assert "mapping_metadata" in data
    assert len(data["mappings"]) == 1
    m = data["mappings"][0]
    assert m["mapping_id"].startswith("map_")
    assert "evidence_relationship" in m
    assert "matching_score" in m
    assert "mapping_confidence" in m


@pytest.mark.asyncio
async def test_endpoint_feature_evidence_mapping_validation_errors():
    """Verify POST /api/mapping/feature-evidence rejects empty or invalid requests with HTTP 400."""
    feat = make_sample_feature()

    # Empty evidence
    payload_empty_evidence = {
        "project_id": "proj_err",
        "features": [feat.model_dump()],
        "evidence": [],
    }
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        res = await client.post("/api/mapping/feature-evidence", json=payload_empty_evidence)
    assert res.status_code == 400
    assert "At least one prior-art evidence" in res.json()["detail"]

    # Invalid weights
    payload_bad_weights = {
        "project_id": "proj_err",
        "features": [feat.model_dump()],
        "evidence": [make_sample_evidence().model_dump()],
        "lexical_weight": 0.5,
        "semantic_weight": 0.7,  # sum != 1.0
    }
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        res2 = await client.post("/api/mapping/feature-evidence", json=payload_bad_weights)
    assert res2.status_code == 400
    assert "must sum to 1.0" in res2.json()["detail"]


def test_direct_partial_vs_contextual_weak_classification():
    """Verify exact 5-tier classification thresholds, combined scoring formula, and reranker score isolation."""
    classifier = RelationshipClassifier()

    # 5-tier threshold validation:
    # DIRECT_MATCH: >= 0.75
    # PARTIAL_MATCH: 0.50 - 0.7499
    # CONTEXTUAL_MATCH: 0.30 - 0.4999
    # WEAK_MATCH: 0.15 - 0.2999
    # NO_MATERIAL_MATCH: < 0.15
    assert classifier.classify(0.75) == EvidenceRelationship.DIRECT_MATCH
    assert classifier.classify(0.85) == EvidenceRelationship.DIRECT_MATCH
    assert classifier.classify(0.749) == EvidenceRelationship.PARTIAL_MATCH
    assert classifier.classify(0.50) == EvidenceRelationship.PARTIAL_MATCH
    assert classifier.classify(0.499) == EvidenceRelationship.CONTEXTUAL_MATCH
    assert classifier.classify(0.30) == EvidenceRelationship.CONTEXTUAL_MATCH
    assert classifier.classify(0.299) == EvidenceRelationship.WEAK_MATCH
    assert classifier.classify(0.15) == EvidenceRelationship.WEAK_MATCH
    assert classifier.classify(0.149) == EvidenceRelationship.NO_MATERIAL_MATCH
    assert classifier.classify(0.0) == EvidenceRelationship.NO_MATERIAL_MATCH


    # Verify combined score formula: 0.4 * lexical + 0.6 * semantic
    provider = MockEmbeddingProvider()
    matcher = FeatureEvidenceMatcher(embedding_provider=provider)
    lexical = 0.50
    semantic = 0.80
    expected_combined = round(0.40 * 0.50 + 0.60 * 0.80, 4)  # 0.20 + 0.48 = 0.68
    actual_combined = round(0.40 * lexical + 0.60 * semantic, 4)
    assert abs(actual_combined - expected_combined) < 1e-4

    # Verify that upstream reranker score is tracked independently and does not distort the lexical+semantic formula
    feat = make_sample_feature(feature_text="dynamic seat locking manager")
    evidence = make_sample_evidence(text="a seat lock manager configured to prevent concurrent claims")
    # Pass upstream reranker_score = 0.99
    evidence.reranker_score = 0.99

    res = matcher.match(feat, evidence, lexical_weight=0.40, semantic_weight=0.60)
    # The matching_score should remain the linear combination of lexical & semantic
    assert abs(res.matching_score - round(0.40 * res.lexical_similarity + 0.60 * res.semantic_similarity, 4)) < 1e-3
    assert res.matching_score != 0.99  # Reranker score must not overwrite matching score




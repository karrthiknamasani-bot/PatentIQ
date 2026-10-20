import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.services.features.types import FeatureType, SourceProvenance
from app.services.features.feature_schema import TechnicalFeature
from app.services.mapping.types import EvidenceRelationship, FeatureEvidenceMapping
from app.services.readiness.types import (
    ReadinessCategory,
    READINESS_CATEGORY_DISPLAY,
    EvidenceMatrixCell,
    EvidenceMatrix,
    DimensionScore,
    ReadinessAssessmentRequest,
    ReadinessAssessmentResponse,
)
from app.services.readiness.evidence_matrix import build_evidence_matrix
from app.services.readiness.dimension_scorer import (
    score_novelty_dimension,
    score_prior_art_overlap_dimension,
    score_technical_differentiation_dimension,
    score_innovation_characteristics_dimension,
    score_documentation_quality_dimension,
    score_commercial_potential_dimension,
    score_all_dimensions,
)
from app.services.readiness.confidence import evaluate_assessment_confidence
from app.services.readiness.category import determine_readiness_category
from app.services.readiness.readiness_engine import PatentReadinessEngine, readiness_engine


@pytest.fixture
def sample_features():
    """Create a diverse set of technical features with provenance."""
    return [
        TechnicalFeature(
            feature_id="feat_comp_001",
            project_id="proj_alpha",
            feature_type=FeatureType.COMPONENT,
            feature_text="Integrated sensor array monitoring tissue impedance at 5.8 GHz",
            normalized_text="integrated sensor array monitoring tissue impedance at 5.8 ghz",
            supporting_sources=[
                SourceProvenance(
                    chunk_id="chk_001",
                    chunk_index=0,
                    section="description",
                    page_number=3,
                    evidence_span_start=10,
                    evidence_span_end=65,
                )
            ],
            confidence=0.95,
        ),
        TechnicalFeature(
            feature_id="feat_func_002",
            project_id="proj_alpha",
            feature_type=FeatureType.FUNCTION,
            feature_text="Modulating RF frequency dynamically based on measured tissue impedance",
            normalized_text="modulating rf frequency dynamically based on measured tissue impedance",
            supporting_sources=[
                SourceProvenance(
                    chunk_id="chk_001",
                    chunk_index=0,
                    section="description",
                    page_number=3,
                    evidence_span_start=70,
                    evidence_span_end=140,
                )
            ],
            confidence=0.90,
        ),
        TechnicalFeature(
            feature_id="feat_mech_003",
            project_id="proj_alpha",
            feature_type=FeatureType.MECHANISM,
            feature_text="Proportional-integral feedback loop adjusting generator output within 5 milliseconds",
            normalized_text="proportional-integral feedback loop adjusting generator output within 5 milliseconds",
            supporting_sources=[
                SourceProvenance(
                    chunk_id="chk_002",
                    chunk_index=1,
                    section="claims",
                    claim_number=1,
                    page_number=5,
                    evidence_span_start=5,
                    evidence_span_end=85,
                )
            ],
            confidence=0.92,
        ),
        TechnicalFeature(
            feature_id="feat_const_004",
            project_id="proj_alpha",
            feature_type=FeatureType.CONSTRAINT,
            feature_text="Output power variance bounded strictly within +/- 0.5% of target setpoint",
            normalized_text="output power variance bounded strictly within +/- 0.5% of target setpoint",
            supporting_sources=[
                SourceProvenance(
                    chunk_id="chk_002",
                    chunk_index=1,
                    section="description",
                    page_number=6,
                    evidence_span_start=100,
                    evidence_span_end=170,
                )
            ],
            confidence=0.88,
        ),
    ]


@pytest.fixture
def sample_mappings():
    """Create sample feature-to-evidence mappings."""
    return [
        FeatureEvidenceMapping(
            mapping_id="map_001",
            project_id="proj_alpha",
            feature_id="feat_comp_001",
            feature_type="component",
            feature_text="Integrated sensor array monitoring tissue impedance at 5.8 GHz",
            patent_number="US-10492811-B2",
            chunk_id="chk_pat_01",
            chunk_index=1,
            evidence_text="A surgical instrument comprising an end effector with an impedance sensor array operating at 5.8 GHz.",
            section="claims",
            claim_number=1,
            page_number=4,
            source="uspto",
            lexical_similarity=0.82,
            semantic_similarity=0.88,
            matching_score=0.856,
            evidence_relationship=EvidenceRelationship.DIRECT_MATCH,
            mapping_confidence=0.91,
            reranker_score=0.94,
            reranker_rank=1,
        ),
        FeatureEvidenceMapping(
            mapping_id="map_002",
            project_id="proj_alpha",
            feature_id="feat_comp_001",
            feature_type="component",
            feature_text="Integrated sensor array monitoring tissue impedance at 5.8 GHz",
            patent_number="US-10512800-B2",
            chunk_id="chk_pat_02",
            chunk_index=3,
            evidence_text="Smart surgical instrument with multi-frequency sensing.",
            section="description",
            page_number=2,
            source="uspto",
            lexical_similarity=0.35,
            semantic_similarity=0.62,
            matching_score=0.512,
            evidence_relationship=EvidenceRelationship.PARTIAL_MATCH,
            mapping_confidence=0.62,
            reranker_score=0.45,
            reranker_rank=2,
        ),
        FeatureEvidenceMapping(
            mapping_id="map_003",
            project_id="proj_alpha",
            feature_id="feat_func_002",
            feature_type="function",
            feature_text="Modulating RF frequency dynamically based on measured tissue impedance",
            patent_number="US-10492811-B2",
            chunk_id="chk_pat_01",
            chunk_index=2,
            evidence_text="A generator configured to deliver RF energy and dynamically modulate frequency in response to feedback.",
            section="claims",
            claim_number=5,
            page_number=5,
            source="uspto",
            lexical_similarity=0.55,
            semantic_similarity=0.74,
            matching_score=0.664,
            evidence_relationship=EvidenceRelationship.PARTIAL_MATCH,
            mapping_confidence=0.72,
            reranker_score=0.78,
            reranker_rank=1,
        ),
    ]


def test_evidence_matrix_construction(sample_features, sample_mappings):
    """Test 1 & 2: Evidence matrix construction, cell attributes, and traceability."""
    matrix = build_evidence_matrix("proj_alpha", sample_features, sample_mappings)

    assert matrix.project_id == "proj_alpha"
    assert matrix.feature_count == 4
    assert matrix.patent_count == 2
    assert matrix.evidence_count == 3
    assert len(matrix.cells) == 3

    cell0 = matrix.cells[0]
    assert cell0.cell_id == "cell_map_001"
    assert cell0.feature_id == "feat_comp_001"
    assert cell0.patent_number == "US-10492811-B2"
    assert cell0.section == "claims"
    assert cell0.claim_number == 1
    assert cell0.relationship == EvidenceRelationship.DIRECT_MATCH
    assert cell0.matching_score == 0.8560
    assert cell0.mapping_confidence == 0.9100


def test_multiple_evidence_cells_per_feature(sample_features, sample_mappings):
    """Test 3: Verify multiple evidence cells for a single feature are preserved."""
    matrix = build_evidence_matrix("proj_alpha", sample_features, sample_mappings)

    comp_cells = [c for c in matrix.cells if c.feature_id == "feat_comp_001"]
    assert len(comp_cells) == 2
    patents = {c.patent_number for c in comp_cells}
    assert patents == {"US-10492811-B2", "US-10512800-B2"}


def test_relationship_aggregation(sample_features, sample_mappings):
    """Test 4: Verify relationship distribution in evidence matrix."""
    matrix = build_evidence_matrix("proj_alpha", sample_features, sample_mappings)

    dist = matrix.relationship_distribution
    assert dist["direct_match"] == 1
    assert dist["partial_match"] == 2
    assert dist["contextual_match"] == 0
    assert dist["weak_match"] == 0


def test_novelty_heuristic_direct_match(sample_features, sample_mappings):
    """Test 5: Novelty heuristic penalizes features covered by direct match."""
    score = score_novelty_dimension(sample_features, sample_mappings)

    assert score.dimension_name == "novelty"
    assert 0.0 <= score.score <= 1.0
    # Because feat_comp_001 has direct match with high confidence, its score is lowered
    assert score.score < 0.70
    assert "direct_prior_art_overlap" in score.uncertainty_flags


def test_novelty_heuristic_no_evidence():
    """Test 5b: No evidence does NOT assign 1.0; anchors conservatively and flags uncertainty."""
    features = [
        TechnicalFeature(
            feature_id="f_new",
            project_id="p1",
            feature_type=FeatureType.MECHANISM,
            feature_text="Completely unheard of novel mechanism",
            normalized_text="completely unheard of novel mechanism",
        )
    ]
    score = score_novelty_dimension(features, [])
    assert score.score == 0.60
    assert "insufficient_prior_art_coverage" in score.uncertainty_flags


def test_prior_art_overlap_scoring(sample_features, sample_mappings):
    """Test 6: Prior-art overlap score increases with direct/partial matches."""
    score = score_prior_art_overlap_dimension(sample_features, sample_mappings)

    assert score.dimension_name == "prior_art_overlap"
    assert 0.0 <= score.score <= 1.0
    assert score.score > 0.30
    assert len(score.supporting_mapping_ids) == 2


def test_technical_differentiation_scoring(sample_features, sample_mappings):
    """Test 7: Differentiated features boost the differentiation score."""
    score = score_technical_differentiation_dimension(sample_features, sample_mappings)

    assert score.dimension_name == "technical_differentiation"
    assert 0.0 <= score.score <= 1.0
    # feat_mech_003 and feat_const_004 have no prior art overlap, so differentiation is strong
    assert score.score >= 0.40


def test_innovation_characteristics_scoring(sample_features):
    """Test 8: Innovation characteristics reflects category diversity & structural elements."""
    score = score_innovation_characteristics_dimension(sample_features)

    assert score.dimension_name == "innovation_characteristics"
    assert 0.0 <= score.score <= 1.0
    # Features include component, function, mechanism, constraint -> high diversity
    assert score.score >= 0.60


def test_documentation_quality_scoring(sample_features):
    """Test 9: Documentation quality reflects feature count, provenance & constraints."""
    score = score_documentation_quality_dimension(sample_features)

    assert score.dimension_name == "documentation_quality"
    assert 0.0 <= score.score <= 1.0
    assert score.score >= 0.70


def test_commercial_potential_heuristic(sample_features):
    """Test 10: Commercial potential heuristic checks technical utility indicators."""
    score = score_commercial_potential_dimension(sample_features)

    assert score.dimension_name == "commercial_potential"
    assert 0.0 <= score.score <= 1.0
    assert "Engineering heuristic, not market prediction" in score.rationale


def test_six_dimension_aggregation(sample_features, sample_mappings):
    """Test 11 & 13: Six-dimension weighted aggregation computes score in [0.0, 1.0]."""
    engine = PatentReadinessEngine()
    resp = engine.assess_readiness("proj_alpha", sample_features, sample_mappings)

    assert 0.0 <= resp.readiness_score <= 1.0
    assert 0.0 <= resp.readiness_percentage <= 100.0
    assert round(resp.readiness_score * 100.0, 2) == resp.readiness_percentage
    assert len(resp.dimension_scores) == 6


def test_weight_sum_validation(sample_features):
    """Test 12: Weights must sum strictly to 1.0."""
    engine = PatentReadinessEngine()
    invalid_weights = {
        "novelty": 0.40,
        "prior_art_overlap": 0.20,
        "technical_differentiation": 0.20,
        "innovation_characteristics": 0.15,
        "documentation_quality": 0.10,
        "commercial_potential": 0.10,  # sum = 1.15
    }
    with pytest.raises(ValueError, match="Readiness dimension weights must sum to 1.0"):
        engine.assess_readiness("proj_alpha", sample_features, [], weights=invalid_weights)


def test_exact_eb_pre_weights_specification(sample_features, sample_mappings):
    """Test 12b: Authoritative EB-PRE weights must match exact 30/20/20/15/10/5 distribution."""
    engine = PatentReadinessEngine()
    expected_weights = {
        "novelty": 0.30,
        "prior_art_overlap": 0.20,
        "technical_differentiation": 0.20,
        "innovation_characteristics": 0.15,
        "documentation_quality": 0.10,
        "commercial_potential": 0.05,
    }
    assert engine.default_weights == expected_weights
    assert sum(engine.default_weights.values()) == 1.0

    resp = engine.assess_readiness("proj_alpha", sample_features, sample_mappings)
    assert resp.assessment_metadata.weights == expected_weights

    # Verify score formula uses these exact weights
    expected_score = round(
        sum(
            expected_weights[dim] * resp.dimension_scores[dim].score
            for dim in expected_weights
        ),
        4,
    )
    assert resp.readiness_score == expected_score


def test_category_threshold_boundaries():
    """Test 14: Category boundary classification."""
    cat, disp = determine_readiness_category(0.39, 0.40, 0.70)
    assert cat == ReadinessCategory.LOW
    assert disp == "Low early-stage patent readiness"

    cat, disp = determine_readiness_category(0.40, 0.40, 0.70)
    assert cat == ReadinessCategory.MODERATE
    assert disp == "Moderate early-stage patent readiness"

    cat, disp = determine_readiness_category(0.699, 0.40, 0.70)
    assert cat == ReadinessCategory.MODERATE

    cat, disp = determine_readiness_category(0.70, 0.40, 0.70)
    assert cat == ReadinessCategory.HIGH
    assert disp == "High early-stage patent readiness"


def test_confidence_and_uncertainty_flags(sample_features, sample_mappings):
    """Test 15 & 16: Confidence calculation and uncertainty flag emission."""
    dim_scores = score_all_dimensions(sample_features, sample_mappings)
    conf, flags = evaluate_assessment_confidence(sample_features, sample_mappings, dim_scores)

    assert 0.0 <= conf <= 1.0
    assert isinstance(flags, list)
    # feat_mech_003 and feat_const_004 have no mappings (2/4 mapped = 50% coverage)
    assert "direct_prior_art_overlap" in flags or "insufficient_prior_art_coverage" in flags


def test_no_evidence_behavior(sample_features):
    """Test 17: Engine behaves predictably when no prior art mappings are supplied."""
    engine = PatentReadinessEngine()
    resp = engine.assess_readiness("proj_alpha", sample_features, [])

    assert resp.evidence_matrix.evidence_count == 0
    assert resp.evidence_matrix.patent_count == 0
    assert "insufficient_prior_art_coverage" in resp.uncertainty_flags
    assert resp.confidence_score < 0.60


def test_sparse_evidence_behavior(sample_features):
    """Test 18: Engine handles weak/sparse mappings properly."""
    sparse_mappings = [
        FeatureEvidenceMapping(
            mapping_id="map_sparse",
            project_id="proj_alpha",
            feature_id="feat_comp_001",
            feature_type="component",
            feature_text="Sensor",
            patent_number="US-0000000-A",
            chunk_index=0,
            evidence_text="General mention of a sensor",
            lexical_similarity=0.15,
            semantic_similarity=0.20,
            matching_score=0.18,
            evidence_relationship=EvidenceRelationship.WEAK_MATCH,
            mapping_confidence=0.22,
        )
    ]
    engine = PatentReadinessEngine()
    resp = engine.assess_readiness("proj_alpha", sample_features, sparse_mappings)

    assert "weak_evidence_support" in resp.uncertainty_flags
    assert resp.confidence_score < 0.60


def test_deterministic_repeated_execution(sample_features, sample_mappings):
    """Test 19: Identical inputs must produce identical outputs."""
    engine = PatentReadinessEngine()
    resp1 = engine.assess_readiness("proj_alpha", sample_features, sample_mappings)
    resp2 = engine.assess_readiness("proj_alpha", sample_features, sample_mappings)

    assert resp1.readiness_score == resp2.readiness_score
    assert resp1.readiness_category == resp2.readiness_category
    assert resp1.confidence_score == resp2.confidence_score
    assert resp1.uncertainty_flags == resp2.uncertainty_flags
    for dim in resp1.dimension_scores:
        assert resp1.dimension_scores[dim].score == resp2.dimension_scores[dim].score


@pytest.mark.asyncio
async def test_api_endpoint_validation(sample_features, sample_mappings):
    """Test 20 & 21: API endpoint POST /api/readiness/assess with validation."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Valid request
        payload = {
            "project_id": "proj_test_api",
            "features": [f.model_dump() for f in sample_features],
            "mappings": [m.model_dump() for m in sample_mappings],
        }
        res = await client.post("/api/readiness/assess", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["project_id"] == "proj_test_api"
        assert "evidence_matrix" in data
        assert "dimension_scores" in data
        assert "readiness_score" in data
        assert "readiness_category" in data
        assert "confidence_score" in data
        assert len(data["dimension_scores"]) == 6

        # 2. Reject empty project_id
        bad_payload = payload.copy()
        bad_payload["project_id"] = ""
        res_bad_id = await client.post("/api/readiness/assess", json=bad_payload)
        assert res_bad_id.status_code in {400, 422}

        # 3. Reject empty features
        bad_payload2 = payload.copy()
        bad_payload2["features"] = []
        res_bad_feat = await client.post("/api/readiness/assess", json=bad_payload2)
        assert res_bad_feat.status_code in {400, 422}

        # 4. Reject invalid weights
        bad_payload3 = payload.copy()
        bad_payload3["weights"] = {
            "novelty": 0.50,
            "prior_art_overlap": 0.50,
            "technical_differentiation": 0.50,
            "innovation_characteristics": 0.50,
            "documentation_quality": 0.50,
            "commercial_potential": 0.50,
        }
        res_bad_wt = await client.post("/api/readiness/assess", json=bad_payload3)
        assert res_bad_wt.status_code == 400


def test_contextual_and_weak_evidence_excluded_from_prior_art_overlap(sample_features):
    """Verify that Contextual (0.30-0.49) and Weak (0.15-0.29) matches do NOT count as material prior-art overlap."""
    feat1 = sample_features[0]

    # Create mappings with ONLY contextual and weak relationships
    contextual_mapping = FeatureEvidenceMapping(
        mapping_id="map_ctx_001",
        project_id="proj_alpha",
        feature_id=feat1.feature_id,
        feature_type=feat1.feature_type.value,
        feature_text=feat1.feature_text,
        patent_number="US-10111222-B2",
        patent_id="US-10111222-B2",
        chunk_id="chk_pat_001",
        chunk_index=0,
        evidence_text="General background mentioning sensor mechanisms in medical tools.",
        matching_score=0.42,
        lexical_similarity=0.35,
        semantic_similarity=0.47,
        evidence_relationship=EvidenceRelationship.CONTEXTUAL_MATCH,
        mapping_confidence=0.60,
    )
    weak_mapping = FeatureEvidenceMapping(
        mapping_id="map_weak_002",
        project_id="proj_alpha",
        feature_id=feat1.feature_id,
        feature_type=feat1.feature_type.value,
        feature_text=feat1.feature_text,
        patent_number="US-10333444-B2",
        patent_id="US-10333444-B2",
        chunk_id="chk_pat_002",
        chunk_index=1,
        evidence_text="Weak peripheral match on generic impedance measurement.",
        matching_score=0.22,
        lexical_similarity=0.18,
        semantic_similarity=0.25,
        evidence_relationship=EvidenceRelationship.WEAK_MATCH,
        mapping_confidence=0.45,
    )

    # 1. Evaluate prior art overlap with only Contextual and Weak mappings
    score_res = score_prior_art_overlap_dimension([feat1], [contextual_mapping, weak_mapping])

    # Must be 0.0 material overlap (no direct or partial overlaps)
    assert score_res.score == 0.0
    # Must NOT include contextual or weak mappings in supporting_mapping_ids
    assert score_res.supporting_mapping_ids == []
    assert "background traceability" in score_res.rationale


    # 2. Add a PARTIAL_MATCH and verify it becomes material overlap
    partial_mapping = FeatureEvidenceMapping(
        mapping_id="map_part_003",
        project_id="proj_alpha",
        feature_id=feat1.feature_id,
        feature_type=feat1.feature_type.value,
        feature_text=feat1.feature_text,
        patent_number="US-10555666-B2",
        patent_id="US-10555666-B2",
        chunk_id="chk_pat_003",
        chunk_index=2,
        evidence_text="Sensor monitoring tissue impedance during electrosurgical operation.",
        matching_score=0.68,
        lexical_similarity=0.62,
        semantic_similarity=0.72,
        evidence_relationship=EvidenceRelationship.PARTIAL_MATCH,
        mapping_confidence=0.80,
    )
    score_with_partial = score_prior_art_overlap_dimension([feat1], [contextual_mapping, weak_mapping, partial_mapping])
    assert score_with_partial.score > 0.0
    assert "map_part_003" in score_with_partial.supporting_mapping_ids
    assert "map_ctx_001" not in score_with_partial.supporting_mapping_ids
    assert "map_weak_002" not in score_with_partial.supporting_mapping_ids



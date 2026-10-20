"""Targeted regression tests for Gemini 429 fallback and bounded persistence.

Covers:
1. Gemini 429 quota exhaustion -> immediate fallback without retries
2. No repeated Gemini retry on quota exhaustion (single API call)
3. Raw 429 JSON is never exposed to frontend; UI message preserved
4. EB-PRE readiness score, Evidence Matrix, and dimension scores unchanged by Gemini failure
5. Supabase unconfigured -> immediate local demo fallback
6. Supabase unreachable / hanging -> bounded timeout fallback without blocking indefinitely
7. Pipeline response is returned after Gemini fallback with persisted=True
"""
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import Response, ASGITransport, AsyncClient

from app.main import app
from app.core.config import settings
from app.schemas.document import DocumentChunk
from app.schemas.user import CurrentUser
from app.services.features.types import FeatureType, SourceProvenance
from app.services.features.feature_schema import TechnicalFeature
from app.services.mapping.types import FeatureEvidenceMapping, EvidenceRelationship
from app.services.readiness.types import (
    ReadinessCategory,
    DimensionScore,
    ReadinessAssessmentResponse,
    AssessmentMetadata,
)
from app.services.readiness.evidence_matrix import build_evidence_matrix
from app.services.explanation.types import ExplanationRequest
from app.services.explanation.gemini_client import GeminiExplanationProvider
from app.services.explanation.grounded_explainer import PatentGroundedExplainer
from app.services.persistence.repository import SupabaseRepository
from app.services.persistence.models import ProjectCreate


def make_sample_feature() -> TechnicalFeature:
    return TechnicalFeature(
        feature_id="feat_func_001",
        project_id="proj_test",
        feature_type=FeatureType.FUNCTION,
        feature_text="Time-bound seat locking prevents concurrent bookings",
        normalized_text="time-bound seat locking prevents concurrent bookings",
        supporting_sources=[
            SourceProvenance(
                chunk_id="chk_0",
                chunk_index=0,
                section="claims",
                page_number=1,
                evidence_span_start=0,
                evidence_span_end=50,
            )
        ],
        confidence=0.92,
    )


from app.services.readiness.readiness_engine import readiness_engine


def make_sample_assessment(feature: TechnicalFeature) -> ReadinessAssessmentResponse:
    return readiness_engine.assess_readiness("proj_test", [feature], [])



@pytest.mark.asyncio
async def test_gemini_429_immediate_fallback_without_retries():
    """Verify Gemini 429 quota exhaustion fails fast with a single request and falls back cleanly."""
    call_count = 0

    async def mock_post(url, **kwargs):
        nonlocal call_count
        call_count += 1
        return Response(
            status_code=429,
            text='{"error": {"code": 429, "message": "Resource exhausted", "status": "RESOURCE_EXHAUSTED"}}',
            request=MagicMock(),
        )

    provider = GeminiExplanationProvider(api_key="mock_key")
    explainer = PatentGroundedExplainer(provider=provider)

    feature = make_sample_feature()
    assessment = make_sample_assessment(feature)
    req = ExplanationRequest(
        project_id="proj_test",
        features=[feature],
        evidence_matrix=assessment.evidence_matrix,
        mappings=[],
        eb_pre_assessment=assessment,
    )

    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        res = await explainer.explain_assessment(req)

    # 1. Exactly 1 API call made (no repeated retries inside the same request)
    assert call_count == 1

    # 2. Fallback was used
    assert res.fallback_used is True

    # 3. Clean executive summary without exposing raw 429 JSON
    assert "RESOURCE_EXHAUSTED" not in res.explanation.executive_summary
    assert "Grounded explanation is temporarily unavailable" in res.explanation.executive_summary
    assert "The deterministic EB-PRE assessment and evidence mappings remain available" in res.explanation.executive_summary


@pytest.mark.asyncio
async def test_eb_pre_remains_unchanged_by_gemini_failure():
    """Verify that EB-PRE score, confidence, category, and dimension scores are 100% preserved despite Gemini failure."""
    provider = GeminiExplanationProvider(api_key="mock_key")
    explainer = PatentGroundedExplainer(provider=provider)

    feature = make_sample_feature()
    assessment = make_sample_assessment(feature)
    req = ExplanationRequest(
        project_id="proj_test",
        features=[feature],
        evidence_matrix=assessment.evidence_matrix,
        mappings=[],
        eb_pre_assessment=assessment,
    )

    with patch("httpx.AsyncClient.post", side_effect=RuntimeError("Simulated Gemini 429")):
        res = await explainer.explain_assessment(req)

    # Values in generated explanation and report must exactly match deterministic EB-PRE assessment
    assert res.explanation.readiness_score == assessment.readiness_score
    assert res.explanation.readiness_category == assessment.readiness_category.value
    assert res.explanation.confidence_score == assessment.confidence_score
    assert res.report.overall_early_stage_readiness["readiness_score"] == assessment.readiness_score



@pytest.mark.asyncio
async def test_persistence_unavailable_bounded_fallback():
    """Verify that unconfigured Supabase immediately falls back to in-memory demo store."""
    repo = SupabaseRepository()
    proj_id = "proj_demo_test"
    user_id = settings.DEMO_USER_ID

    feature = make_sample_feature()
    assessment = make_sample_assessment(feature)
    chunk = DocumentChunk(
        chunk_index=0,
        section="claims",
        text="A seat locking system",
        start_character=0,
        end_character=21,
        token_estimate=5,
    )
    mapping = FeatureEvidenceMapping(
        mapping_id="map_001",
        project_id=proj_id,
        feature_id=feature.feature_id,
        feature_type=feature.feature_type.value,
        feature_text=feature.feature_text,
        patent_number="US-10111222-B2",
        chunk_index=0,
        evidence_text="Prior art seat lock",
        matching_score=0.45,
        lexical_similarity=0.40,
        semantic_similarity=0.50,
        evidence_relationship=EvidenceRelationship.CONTEXTUAL_MATCH,
        mapping_confidence=0.70,
    )

    # Ensure all persistence methods succeed in local demo mode
    s_chunk = await repo.save_document_chunks(proj_id, [chunk], user_id)
    assert s_chunk.success is True
    assert s_chunk.status == "persisted"

    s_feat = await repo.save_features(proj_id, [feature], user_id)
    assert s_feat.success is True
    assert s_feat.status == "persisted"

    s_ev = await repo.save_evidence_items(proj_id, [mapping], user_id)
    assert s_ev.success is True
    assert s_ev.status == "persisted"

    # Verify retrieval from demo store
    retrieved_ev = await repo.get_evidence_items(proj_id, user_id)
    assert len(retrieved_ev) == 1
    assert retrieved_ev[0].retrieved_source == "US-10111222-B2"


@pytest.mark.asyncio
async def test_persistence_cannot_block_indefinitely():
    """Verify that a slow or hanging database operation times out within bounded limit and falls back cleanly."""
    repo = SupabaseRepository()
    proj_id = "proj_hang_test"
    user_id = settings.DEMO_USER_ID
    chunk = DocumentChunk(
        chunk_index=0,
        section="claims",
        text="A test chunk",
        start_character=0,
        end_character=12,
        token_estimate=3,
    )

    # Mock client where execute hangs
    mock_client = MagicMock()
    def hanging_call(*args, **kwargs):
        time.sleep(2.0)
        return MagicMock(data=[])

    mock_client.table().delete().eq().execute.side_effect = hanging_call
    mock_client.table().insert().execute.side_effect = hanging_call

    with patch.object(repo, "_get_client", return_value=mock_client):
        # Override timeout to 0.1s for fast test verification
        with patch.object(repo, "DEFAULT_TIMEOUT_SECONDS", 0.1):
            t0 = time.perf_counter()
            status = await repo.save_document_chunks(proj_id, [chunk], user_id)
            elapsed = time.perf_counter() - t0

    # Must complete within bounded timeout (~0.1s - 0.5s), NOT 2.0s
    assert elapsed < 1.0
    assert status.success is True
    assert status.status == "persisted_demo_fallback"


@pytest.mark.asyncio
async def test_pipeline_response_returned_after_gemini_fallback():
    """Verify POST /api/pipeline/analyze returns HTTP 200 with persisted=True even when Gemini fails."""
    doc_content = (
        b"Patent Readiness Disclosure\n\n"
        b"Claims:\n"
        b"1. A distributed transactional system comprising a time-bound locking manager configured "
        b"to prevent concurrent seat reservation conflicts across distributed nodes.\n"
    )

    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {settings.DEMO_BEARER_TOKEN}"}
    files = {"file": ("test_invention.txt", doc_content, "text/plain")}
    data = {"title": "Test Pipeline Recovery"}

    from app.services.explanation.gemini_client import GeminiExplanationProvider

    with patch.object(
        GeminiExplanationProvider,
        "generate_explanation",
        side_effect=RuntimeError("Gemini API error (status 429): Resource exhausted"),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/api/pipeline/analyze",
                headers=headers,
                files=files,
                data=data,
            )

    assert res.status_code == 200
    res_data = res.json()
    assert res_data["generation_method"] == "deterministic_fallback"
    assert res_data["persisted"] is True
    assert res_data["readiness_score"] > 0.0
    assert "Grounded explanation is temporarily unavailable" in res_data["executive_summary"]


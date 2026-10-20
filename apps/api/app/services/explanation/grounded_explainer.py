import time
import logging
from typing import Optional, List, Dict, Any, Tuple
from app.core.config import settings
from app.services.features.feature_schema import TechnicalFeature
from app.services.mapping.types import FeatureEvidenceMapping, EvidenceRelationship
from app.services.readiness.types import ReadinessAssessmentResponse
from app.services.explanation.types import (
    EvidenceItem,
    GroundedContext,
    GroundedExplanation,
    EvidenceBasedReport,
    ExplanationRequest,
    ExplanationResponse,
)
from app.services.explanation.gemini_client import (
    BaseExplanationProvider,
    GeminiExplanationProvider,
)
from app.services.explanation.grounding_validator import validate_grounding, GroundingValidationResult
from app.services.explanation.report_builder import (
    build_evidence_based_report,
    build_fallback_explanation,
)

logger = logging.getLogger("patentiq.explanation.explainer")

RELATIONSHIP_SEVERITY = {
    "direct_match": 4,
    "partial_match": 3,
    "contextual_match": 2,
    "weak_match": 1,
    "no_material_match": 0,
}


_DEFAULT = object()


class PatentGroundedExplainer:
    """Orchestrator for grounded AI explanation and structured reporting.
    
    Transforms deterministic EB-PRE outputs into auditable, human-readable
    assessments while strictly enforcing numerical integrity and evidence grounding.
    """

    def __init__(
        self,
        provider: Any = _DEFAULT,
        max_evidence_items: Optional[int] = None,
        force_fallback: bool = False,
    ):
        self.max_evidence_items = max_evidence_items or settings.EXPLANATION_MAX_EVIDENCE_ITEMS
        if force_fallback or provider is None:
            self.provider = None
        elif provider is not _DEFAULT:
            self.provider = provider
        elif settings.GEMINI_API_KEY:
            self.provider = GeminiExplanationProvider()
        else:
            self.provider = None

    def build_grounded_context(
        self,
        project_id: str,
        features: List[TechnicalFeature],
        mappings: List[FeatureEvidenceMapping],
        eb_pre_assessment: ReadinessAssessmentResponse,
    ) -> GroundedContext:
        """Assign stable short evidence IDs (E1, E2, ...) and assemble GroundedContext."""
        # Sort mappings by relationship severity descending, mapping confidence descending, reranker rank ascending
        def sort_key(m: FeatureEvidenceMapping):
            rel_val = m.evidence_relationship.value if hasattr(m.evidence_relationship, "value") else str(m.evidence_relationship)
            severity = RELATIONSHIP_SEVERITY.get(rel_val, 0)
            conf = m.mapping_confidence
            rr_rank = m.reranker_rank if m.reranker_rank is not None else 999
            return (-severity, -conf, rr_rank)

        sorted_mappings = sorted(mappings, key=sort_key)
        selected_mappings = sorted_mappings[: self.max_evidence_items]

        evidence_items: List[EvidenceItem] = []
        for idx, m in enumerate(selected_mappings, 1):
            rel_val = m.evidence_relationship.value if hasattr(m.evidence_relationship, "value") else str(m.evidence_relationship)
            item = EvidenceItem(
                evidence_id=f"E{idx}",
                patent_number=m.patent_number,
                patent_id=m.patent_id,
                chunk_id=m.chunk_id,
                chunk_index=m.chunk_index,
                section=m.section,
                claim_number=m.claim_number,
                page_number=m.page_number,
                text=m.evidence_text,
                feature_id=m.feature_id,
                feature_type=m.feature_type,
                feature_text=m.feature_text,
                relationship=rel_val,
                matching_score=m.matching_score,
                mapping_confidence=m.mapping_confidence,
                reranker_score=m.reranker_score,
                reranker_rank=m.reranker_rank,
                source=m.source,
            )
            evidence_items.append(item)

        cat_val = (
            eb_pre_assessment.readiness_category.value
            if hasattr(eb_pre_assessment.readiness_category, "value")
            else str(eb_pre_assessment.readiness_category)
        )

        return GroundedContext(
            project_id=project_id,
            features=features,
            evidence_items=evidence_items,
            dimension_scores=eb_pre_assessment.dimension_scores,
            readiness_score=eb_pre_assessment.readiness_score,
            readiness_percentage=eb_pre_assessment.readiness_percentage,
            readiness_category=cat_val,
            category_display=eb_pre_assessment.category_display,
            confidence_score=eb_pre_assessment.confidence_score,
            uncertainty_flags=eb_pre_assessment.uncertainty_flags,
        )

    async def explain_assessment(
        self,
        request: ExplanationRequest,
    ) -> ExplanationResponse:
        """Execute grounded explanation pipeline with validation and fallback."""
        start_time = time.perf_counter()

        context = self.build_grounded_context(
            project_id=request.project_id,
            features=request.features,
            mappings=request.mappings,
            eb_pre_assessment=request.eb_pre_assessment,
        )

        model_name = settings.GEMINI_EXPLANATION_MODEL
        fallback_used = False
        grounding_valid = True
        validation_errors: List[str] = []

        if self.provider is not None:
            try:
                explanation = await self.provider.generate_explanation(context)
                val_result: GroundingValidationResult = validate_grounding(explanation, context)

                if val_result.is_valid:
                    report = build_evidence_based_report(context, explanation, fallback_used=False)
                    elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
                    return ExplanationResponse(
                        project_id=request.project_id,
                        explanation=explanation,
                        report=report,
                        grounding_valid=True,
                        model=getattr(self.provider, "model_name", model_name),
                        fallback_used=False,
                        metadata={
                            "model": getattr(self.provider, "model_name", model_name),
                            "evidence_count": len(context.evidence_items),
                            "feature_count": len(context.features),
                            "mapping_count": len(request.mappings),
                            "generation_latency_ms": elapsed_ms,
                            "grounding_validation_status": "passed",
                        },
                    )
                else:
                    logger.warning("Grounding validation failed: %s. Using fallback.", val_result.errors)
                    grounding_valid = False
                    validation_errors = val_result.errors
                    fallback_used = True
                    explanation = build_fallback_explanation(
                        context,
                        reason=f"Grounding validation failed: {'; '.join(val_result.errors[:2])}",
                    )
            except Exception as e:
                err_str = str(e)
                if "status 429" in err_str or "quota" in err_str.lower():
                    logger.warning("Gemini quota exhausted (status 429). Using deterministic fallback.")
                else:
                    logger.warning("Explanation provider error: %s. Using fallback.", e)
                fallback_used = True
                grounding_valid = False
                validation_errors = ["Grounded explanation temporarily unavailable"]
                explanation = build_fallback_explanation(
                    context,
                    reason="Grounded explanation temporarily unavailable",
                )

        else:
            fallback_used = True
            grounding_valid = True
            explanation = build_fallback_explanation(context, reason="GEMINI_API_KEY not configured")

        report = build_evidence_based_report(context, explanation, fallback_used=True)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        return ExplanationResponse(
            project_id=request.project_id,
            explanation=explanation,
            report=report,
            grounding_valid=grounding_valid,
            model="deterministic_fallback" if fallback_used and self.provider is None else getattr(self.provider, "model_name", model_name),
            fallback_used=fallback_used,
            metadata={
                "model": "deterministic_fallback" if fallback_used and self.provider is None else getattr(self.provider, "model_name", model_name),
                "evidence_count": len(context.evidence_items),
                "feature_count": len(context.features),
                "mapping_count": len(request.mappings),
                "generation_latency_ms": elapsed_ms,
                "grounding_validation_status": "passed" if grounding_valid else f"failed: {validation_errors}",
            },
        )


grounded_explainer = PatentGroundedExplainer()

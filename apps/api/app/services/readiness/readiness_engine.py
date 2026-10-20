import time
from typing import List, Optional, Dict
from app.core.config import settings
from app.services.features.feature_schema import TechnicalFeature
from app.services.mapping.types import FeatureEvidenceMapping
from app.services.readiness.types import (
    ReadinessAssessmentRequest,
    ReadinessAssessmentResponse,
    AssessmentMetadata,
    DimensionScore,
)
from app.services.readiness.evidence_matrix import build_evidence_matrix
from app.services.readiness.dimension_scorer import score_all_dimensions
from app.services.readiness.confidence import evaluate_assessment_confidence
from app.services.readiness.category import determine_readiness_category


class PatentReadinessEngine:
    """Evidence-Based Patent Readiness Engine (EB-PRE).
    
    A deterministic, transparent decision-support engine aggregating
    feature-to-evidence mappings across six independent dimensions to produce
    an early-stage patent readiness indication.
    
    (Strictly NOT an affirmative legal determination of patentability).
    """

    def __init__(self):
        self.default_weights: Dict[str, float] = {
            "novelty": settings.READINESS_WEIGHT_NOVELTY,
            "prior_art_overlap": settings.READINESS_WEIGHT_PRIOR_ART_OVERLAP,
            "technical_differentiation": settings.READINESS_WEIGHT_TECH_DIFFERENTIATION,
            "innovation_characteristics": settings.READINESS_WEIGHT_INNOVATION_CHARS,
            "documentation_quality": settings.READINESS_WEIGHT_DOC_QUALITY,
            "commercial_potential": settings.READINESS_WEIGHT_COMMERCIAL_POTENTIAL,
        }
        self.default_thresholds: Dict[str, float] = {
            "moderate": settings.READINESS_THRESHOLD_MODERATE,
            "high": settings.READINESS_THRESHOLD_HIGH,
        }

    def validate_weights(self, weights: Dict[str, float]) -> None:
        """Ensure all required dimensions are present and weights strictly sum to 1.0."""
        required_dims = {
            "novelty",
            "prior_art_overlap",
            "technical_differentiation",
            "innovation_characteristics",
            "documentation_quality",
            "commercial_potential",
        }
        if set(weights.keys()) != required_dims:
            missing = required_dims - set(weights.keys())
            extra = set(weights.keys()) - required_dims
            raise ValueError(f"Invalid dimension weights. Missing: {missing}, Extra: {extra}")

        for k, v in weights.items():
            if v < 0.0 or v > 1.0:
                raise ValueError(f"Weight for dimension '{k}' must be within [0.0, 1.0], got {v}")

        weight_sum = sum(weights.values())
        if abs(weight_sum - 1.0) > 1e-4:
            raise ValueError(f"Readiness dimension weights must sum to 1.0 (got {weight_sum:.6f})")

    def assess_readiness(
        self,
        project_id: str,
        features: List[TechnicalFeature],
        mappings: Optional[List[FeatureEvidenceMapping]] = None,
        weights: Optional[Dict[str, float]] = None,
        thresholds: Optional[Dict[str, float]] = None,
    ) -> ReadinessAssessmentResponse:
        """Execute deterministic EB-PRE assessment."""
        start_time = time.perf_counter()

        if not project_id or not project_id.strip():
            raise ValueError("project_id must not be empty")
        if not features:
            raise ValueError("features list must not be empty")

        if mappings is None:
            mappings = []

        active_weights = weights if weights is not None else self.default_weights
        self.validate_weights(active_weights)

        active_thresholds = thresholds if thresholds is not None else self.default_thresholds
        thresh_mod = active_thresholds.get("moderate", 0.40)
        thresh_high = active_thresholds.get("high", 0.70)
        if thresh_mod >= thresh_high:
            raise ValueError(f"moderate threshold ({thresh_mod}) must be strictly less than high threshold ({thresh_high})")

        # 1. Build Evidence Matrix
        matrix = build_evidence_matrix(
            project_id=project_id,
            features=features,
            mappings=mappings,
        )

        # 2. Score Six EB-PRE Dimensions
        dimension_scores = score_all_dimensions(
            features=features,
            mappings=mappings,
        )

        # 3. Calculate Weighted Readiness Score
        raw_readiness = sum(
            active_weights[dim] * dimension_scores[dim].score
            for dim in active_weights
        )
        readiness_score = round(max(0.0, min(1.0, raw_readiness)), 4)
        readiness_pct = round(readiness_score * 100.0, 2)

        # 4. Categorize Readiness
        category, category_display = determine_readiness_category(
            score=readiness_score,
            threshold_moderate=thresh_mod,
            threshold_high=thresh_high,
        )

        # 5. Evaluate Confidence & Uncertainty Flags
        confidence_score, uncertainty_flags = evaluate_assessment_confidence(
            features=features,
            mappings=mappings,
            dimension_scores=dimension_scores,
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        metadata = AssessmentMetadata(
            weights=active_weights,
            thresholds=active_thresholds,
            feature_count=len(features),
            patent_count=matrix.patent_count,
            evidence_count=matrix.evidence_count,
            mapping_count=len(mappings),
            elapsed_time_ms=elapsed_ms,
            engine_version="eb_pre_v1.0",
        )

        return ReadinessAssessmentResponse(
            project_id=project_id,
            evidence_matrix=matrix,
            dimension_scores=dimension_scores,
            readiness_score=readiness_score,
            readiness_percentage=readiness_pct,
            readiness_category=category,
            category_display=category_display,
            confidence_score=confidence_score,
            uncertainty_flags=uncertainty_flags,
            assessment_metadata=metadata,
        )


readiness_engine = PatentReadinessEngine()

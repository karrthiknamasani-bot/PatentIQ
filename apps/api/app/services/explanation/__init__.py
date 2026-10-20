from app.services.explanation.types import (
    EvidenceItem,
    GroundedContext,
    PriorArtFinding,
    DimensionExplanation,
    EvidenceHighlight,
    GroundedExplanation,
    EvidenceBasedReport,
    ExplanationRequest,
    ExplanationResponse,
)
from app.services.explanation.gemini_client import (
    BaseExplanationProvider,
    GeminiExplanationProvider,
    MockExplanationProvider,
)
from app.services.explanation.prompt_builder import SYSTEM_PROMPT, build_grounded_prompt
from app.services.explanation.grounding_validator import (
    validate_grounding,
    GroundingValidationResult,
    PROHIBITED_LEGAL_TERMS,
)
from app.services.explanation.report_builder import (
    build_evidence_based_report,
    build_fallback_explanation,
    LEGAL_DISCLAIMER,
)
from app.services.explanation.grounded_explainer import (
    PatentGroundedExplainer,
    grounded_explainer,
)

__all__ = [
    "EvidenceItem",
    "GroundedContext",
    "PriorArtFinding",
    "DimensionExplanation",
    "EvidenceHighlight",
    "GroundedExplanation",
    "EvidenceBasedReport",
    "ExplanationRequest",
    "ExplanationResponse",
    "BaseExplanationProvider",
    "GeminiExplanationProvider",
    "MockExplanationProvider",
    "SYSTEM_PROMPT",
    "build_grounded_prompt",
    "validate_grounding",
    "GroundingValidationResult",
    "PROHIBITED_LEGAL_TERMS",
    "build_evidence_based_report",
    "build_fallback_explanation",
    "LEGAL_DISCLAIMER",
    "PatentGroundedExplainer",
    "grounded_explainer",
]

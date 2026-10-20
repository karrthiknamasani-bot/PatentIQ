from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.services.features.feature_schema import TechnicalFeature
from app.services.mapping.types import FeatureEvidenceMapping
from app.services.readiness.types import (
    EvidenceMatrix,
    DimensionScore,
    ReadinessAssessmentResponse,
)


class EvidenceItem(BaseModel):
    """Compact, traceable evidence excerpt indexed by a stable ID (e.g. E1, E2)."""
    model_config = ConfigDict(extra="ignore")

    evidence_id: str = Field(..., description="Stable short evidence identifier (e.g. 'E1')")
    patent_number: str = Field(..., description="Target patent number (e.g. 'US-10492811-B2')")
    patent_id: Optional[str] = None
    chunk_id: Optional[str] = None
    chunk_index: int = Field(..., ge=0)
    section: str = Field(default="description")
    claim_number: Optional[int] = None
    page_number: Optional[int] = None
    text: str = Field(..., description="Verbatim text excerpt of the prior art")
    feature_id: str = Field(..., description="Mapped technical feature ID")
    feature_type: Optional[str] = None
    feature_text: Optional[str] = None
    relationship: str = Field(..., description="Classified technical relationship")
    matching_score: float = Field(..., ge=0.0, le=1.0)
    mapping_confidence: float = Field(..., ge=0.0, le=1.0)
    reranker_score: Optional[float] = None
    reranker_rank: Optional[int] = None
    source: Optional[str] = "custom"


class GroundedContext(BaseModel):
    """Structured evidence bundle provided to the explanation layer."""
    model_config = ConfigDict(extra="ignore")

    project_id: str
    features: List[TechnicalFeature]
    evidence_items: List[EvidenceItem]
    dimension_scores: Dict[str, DimensionScore]
    readiness_score: float = Field(..., ge=0.0, le=1.0)
    readiness_percentage: float = Field(..., ge=0.0, le=100.0)
    readiness_category: str
    category_display: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    uncertainty_flags: List[str] = Field(default_factory=list)


class PriorArtFinding(BaseModel):
    """Specific prior-art finding tied directly to supplied evidence IDs."""
    model_config = ConfigDict(extra="ignore")

    statement: str = Field(..., description="Factual finding supported by evidence")
    evidence_ids: List[str] = Field(default_factory=list, description="Citations to supplied evidence IDs (e.g. ['E1'])")


class DimensionExplanation(BaseModel):
    """Explanation for a specific EB-PRE dimension reproducing its exact score."""
    model_config = ConfigDict(extra="ignore")

    dimension: str = Field(..., description="Canonical dimension name")
    score: float = Field(..., ge=0.0, le=1.0, description="Exact reproduced EB-PRE dimension score")
    explanation: str = Field(..., description="Evidence-grounded rationale for the score")
    evidence_ids: List[str] = Field(default_factory=list, description="Referenced evidence citations")


class EvidenceHighlight(BaseModel):
    """Key feature-to-evidence correspondence highlight."""
    model_config = ConfigDict(extra="ignore")

    feature_id: str
    patent_number: str
    relationship: str
    mapping_confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_id: str
    relevance_explanation: str


class GroundedExplanation(BaseModel):
    """Structured response schema returned by the grounded explainer."""
    model_config = ConfigDict(extra="ignore")

    executive_summary: str
    invention_summary: str
    key_technical_features: List[str] = Field(default_factory=list)
    prior_art_findings: List[PriorArtFinding] = Field(default_factory=list)
    dimension_explanations: List[DimensionExplanation] = Field(default_factory=list)
    differentiation_analysis: str
    evidence_highlights: List[EvidenceHighlight] = Field(default_factory=list)
    uncertainty_explanation: str
    limitations: List[str] = Field(default_factory=list)
    conclusion: str
    evidence_references: List[str] = Field(default_factory=list)

    # Numerical integrity validation fields (must match EB-PRE exactly)
    readiness_score: float = Field(..., ge=0.0, le=1.0)
    readiness_percentage: float = Field(..., ge=0.0, le=100.0)
    readiness_category: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class EvidenceBasedReport(BaseModel):
    """Comprehensive 10-section final assessment report."""
    model_config = ConfigDict(extra="ignore")

    project_id: str
    executive_summary: str
    invention_overview: str
    technical_feature_analysis: List[Dict[str, Any]] = Field(default_factory=list)
    prior_art_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_matrix_summary: Dict[str, Any] = Field(default_factory=dict)
    eb_pre_dimension_assessment: List[Dict[str, Any]] = Field(default_factory=list)
    technical_differentiation: str
    uncertainty_and_limitations: Dict[str, Any] = Field(default_factory=dict)
    overall_early_stage_readiness: Dict[str, Any] = Field(default_factory=dict)
    legal_disclaimer: str


class ExplanationRequest(BaseModel):
    """Request payload to generate a grounded explanation from EB-PRE results."""
    model_config = ConfigDict(extra="ignore")

    project_id: str = Field(..., min_length=1, max_length=128)
    features: List[TechnicalFeature] = Field(..., min_length=1)
    evidence_matrix: EvidenceMatrix
    mappings: List[FeatureEvidenceMapping] = Field(default_factory=list)
    eb_pre_assessment: ReadinessAssessmentResponse


class ExplanationResponse(BaseModel):
    """Complete grounded explanation and structured evidence-based report."""
    model_config = ConfigDict(extra="ignore")

    project_id: str
    explanation: GroundedExplanation
    report: EvidenceBasedReport
    grounding_valid: bool
    model: str
    fallback_used: bool
    metadata: Dict[str, Any] = Field(default_factory=dict)

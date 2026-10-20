from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.services.features.feature_schema import TechnicalFeature
from app.services.mapping.types import FeatureEvidenceMapping, EvidenceRelationship


class ReadinessCategory(str, Enum):
    """Decision-support categorization for early-stage patent readiness indication.
    (NOTE: This is an engineering decision-support label, NOT a legal patentability finding).
    """
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


READINESS_CATEGORY_DISPLAY = {
    ReadinessCategory.LOW: "Low early-stage patent readiness",
    ReadinessCategory.MODERATE: "Moderate early-stage patent readiness",
    ReadinessCategory.HIGH: "High early-stage patent readiness",
}


class EvidenceMatrixCell(BaseModel):
    """Atomic cell representing feature-to-prior-art evidence correspondence."""
    model_config = ConfigDict(extra="ignore")

    cell_id: str = Field(..., description="Deterministic cell identifier")
    mapping_id: str = Field(..., description="Originating mapping identifier")
    feature_id: str = Field(..., description="Target technical feature identifier")
    feature_type: str = Field(..., description="Feature type category")
    feature_text: str = Field(..., description="Verbatim text of the feature")
    patent_number: str = Field(..., description="Target prior-art patent number")
    patent_id: Optional[str] = Field(None, description="Prior-art patent ID if available")
    chunk_id: Optional[str] = Field(None, description="Corpus chunk ID")
    chunk_index: int = Field(..., ge=0, description="Sequential chunk index")
    evidence_text: str = Field(..., description="Verbatim excerpt of prior-art evidence")
    relationship: EvidenceRelationship = Field(..., description="Classified evidence relationship")
    matching_score: float = Field(..., ge=0.0, le=1.0, description="Combined lexical/semantic matching score")
    mapping_confidence: float = Field(..., ge=0.0, le=1.0, description="Mapping correspondence confidence")
    reranker_score: Optional[float] = Field(None, description="Upstream Cross-Encoder reranker score")
    reranker_rank: Optional[int] = Field(None, description="Upstream Cross-Encoder reranker rank")
    section: str = Field(default="description", description="Patent section ('claims', 'abstract', etc.)")
    claim_number: Optional[int] = Field(None, description="Patent claim number if applicable")
    page_number: Optional[int] = Field(None, description="Page number of the excerpt")
    source: Optional[str] = Field(default="custom", description="Corpus source origin")


class EvidenceMatrix(BaseModel):
    """Structured Evidence Matrix preserving feature-by-patent correspondences."""
    model_config = ConfigDict(extra="ignore")

    project_id: str = Field(..., description="Project identifier")
    cells: List[EvidenceMatrixCell] = Field(default_factory=list, description="All matrix correspondence cells")
    feature_count: int = Field(..., ge=0, description="Total number of evaluated features")
    patent_count: int = Field(..., ge=0, description="Distinct count of referenced patents")
    evidence_count: int = Field(..., ge=0, description="Total count of evidence chunks linked")
    relationship_distribution: Dict[str, int] = Field(default_factory=dict, description="Counts by relationship tier")


class DimensionScore(BaseModel):
    """Score and explanatory rationale for one of the six EB-PRE dimensions."""
    model_config = ConfigDict(extra="ignore")

    dimension_name: str = Field(..., description="Canonical name of the dimension")
    score: float = Field(..., ge=0.0, le=1.0, description="Normalized dimension score [0.0, 1.0]")
    supporting_feature_ids: List[str] = Field(default_factory=list, description="Feature IDs influencing this score")
    supporting_mapping_ids: List[str] = Field(default_factory=list, description="Mapping IDs providing direct evidence")
    rationale: str = Field(..., description="Transparent engineering explanation of score derivation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in this specific dimension estimate")
    uncertainty_flags: List[str] = Field(default_factory=list, description="Identified uncertainty signals")


class AssessmentMetadata(BaseModel):
    """Execution telemetry and configuration state for the EB-PRE assessment."""
    model_config = ConfigDict(extra="ignore")

    weights: Dict[str, float] = Field(..., description="Dimension weight distribution (sums to 1.0)")
    thresholds: Dict[str, float] = Field(..., description="Readiness category boundary thresholds")
    feature_count: int = Field(..., ge=0)
    patent_count: int = Field(..., ge=0)
    evidence_count: int = Field(..., ge=0)
    mapping_count: int = Field(..., ge=0)
    elapsed_time_ms: float = Field(..., ge=0.0)
    engine_version: str = Field(default="eb_pre_v1.0")


class ReadinessAssessmentRequest(BaseModel):
    """Request payload to execute the EB-PRE readiness assessment."""
    model_config = ConfigDict(extra="ignore")

    project_id: str = Field(..., min_length=1, max_length=128, description="Project identifier")
    features: List[TechnicalFeature] = Field(..., min_length=1, description="List of extracted technical features")
    mappings: List[FeatureEvidenceMapping] = Field(default_factory=list, description="Feature-to-evidence mappings")
    weights: Optional[Dict[str, float]] = Field(default=None, description="Optional custom dimension weights")
    thresholds: Optional[Dict[str, float]] = Field(default=None, description="Optional custom category thresholds")


class ReadinessAssessmentResponse(BaseModel):
    """Comprehensive, deterministic assessment result from EB-PRE."""
    model_config = ConfigDict(extra="ignore")

    project_id: str
    evidence_matrix: EvidenceMatrix
    dimension_scores: Dict[str, DimensionScore]
    readiness_score: float = Field(..., ge=0.0, le=1.0, description="Weighted composite readiness score [0.0, 1.0]")
    readiness_percentage: float = Field(..., ge=0.0, le=100.0, description="Readiness score represented as percentage")
    readiness_category: ReadinessCategory = Field(..., description="Categorical readiness tier")
    category_display: str = Field(..., description="Human-readable decision-support label")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall assessment confidence [0.0, 1.0]")
    uncertainty_flags: List[str] = Field(default_factory=list, description="All active uncertainty indicators")
    assessment_metadata: AssessmentMetadata

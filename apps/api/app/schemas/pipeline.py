from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class PipelineAnalysisResponse(BaseModel):
    """Complete, unified end-to-end patent readiness assessment payload."""
    model_config = ConfigDict(extra="ignore")

    project_id: str
    title: str
    filename: str
    file_type: str
    file_size: int
    chunk_count: int
    feature_count: int
    prior_art_hit_count: int
    mapping_count: int

    # Core EB-PRE Assessment
    readiness_score: float = Field(..., ge=0.0, le=1.0, description="Raw deterministic readiness score")
    readiness_percentage: float = Field(..., ge=0.0, le=100.0, description="Readiness score formatted as percentage")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence level")
    readiness_category: str
    category_display: str
    dimension_scores: Dict[str, Any]
    weights: Dict[str, float] = Field(default_factory=dict, description="Active EB-PRE dimension weights")
    uncertainty_flags: List[str] = Field(default_factory=list)

    # Detailed Evidence & Tracing
    features: List[Dict[str, Any]] = Field(default_factory=list)
    mappings: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_matrix: Dict[str, Any] = Field(default_factory=dict)

    # Grounded Report & Explanation
    report: Dict[str, Any] = Field(default_factory=dict)
    executive_summary: str
    generation_method: str = "deterministic_fallback"
    generation_latency_ms: int = 0
    persisted: bool = True

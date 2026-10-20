from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.document import DocumentChunk
from app.services.features.types import FeatureType, SourceProvenance


class TechnicalFeature(BaseModel):
    """Canonical representation of an extracted technical feature from an invention document."""
    model_config = ConfigDict(extra="ignore")

    project_id: str = Field(..., description="Project or document identifier")
    feature_id: str = Field(..., description="Stable deterministic feature identifier")
    feature_type: FeatureType = Field(..., description="Controlled technical feature category")
    feature_text: str = Field(..., min_length=1, description="Verbatim text passage extracted from the document")
    normalized_text: str = Field(..., min_length=1, description="Standardized text for downstream evidence matching")

    # Primary origin provenance
    source_chunk_id: Optional[str] = Field(None, description="Identifier of primary source chunk")
    source_reference: Optional[str] = Field(None, description="Primary source reference (e.g. claim:1, page:2)")
    section: Optional[str] = Field(None, description="Document section of primary occurrence")
    page_number: Optional[int] = Field(None, description="Page number of primary occurrence")
    claim_number: Optional[int] = Field(None, description="Claim number if originating from claims")
    evidence_span_start: Optional[int] = Field(None, description="Start character offset within primary chunk")
    evidence_span_end: Optional[int] = Field(None, description="End character offset within primary chunk")

    extraction_method: str = Field(default="rule_based", description="Extraction mechanism used ('rule_based', 'llm_gemini')")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence that the document text supports this extracted technical feature (NOT patentability)",
    )

    # Consolidated multi-chunk provenance
    supporting_sources: List[SourceProvenance] = Field(
        default_factory=list,
        description="All document locations supporting this exact technical feature",
    )


class ExtractionMetadata(BaseModel):
    """Execution telemetry and extraction summary metadata."""
    model_config = ConfigDict(extra="ignore")

    number_of_input_chunks: int = Field(..., ge=0)
    number_of_raw_candidates: int = Field(..., ge=0)
    number_of_validated_features: int = Field(..., ge=0)
    number_of_duplicates_merged: int = Field(..., ge=0)
    extraction_method: str
    processing_status: str


class FeatureExtractionRequest(BaseModel):
    """Request payload for extracting technical features from processed document chunks."""
    model_config = ConfigDict(extra="ignore")

    project_id: str = Field(..., min_length=1, max_length=128, description="Target project identifier")
    chunks: List[DocumentChunk] = Field(..., description="List of processed document chunks to analyze")
    method: str = Field(default="auto", description="Extraction engine: 'auto', 'rule_based', or 'gemini'")


class FeatureExtractionResponse(BaseModel):
    """Response containing structured technical features and extraction telemetry."""
    model_config = ConfigDict(extra="ignore")

    project_id: str
    features: List[TechnicalFeature]
    total_features: int
    extraction_metadata: ExtractionMetadata

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class FeatureType(str, Enum):
    """Controlled vocabulary for technical feature categories."""
    PROBLEM = "problem"
    COMPONENT = "component"
    FUNCTION = "function"
    RELATIONSHIP = "relationship"
    INPUT = "input"
    OUTPUT = "output"
    PROCESS = "process"
    CONSTRAINT = "constraint"
    MECHANISM = "mechanism"
    TECHNICAL_EFFECT = "technical_effect"
    CLAIMED_ASPECT = "claimed_aspect"


class SourceProvenance(BaseModel):
    """Traceable provenance link to an originating passage in the user's document."""
    model_config = ConfigDict(extra="ignore")

    chunk_id: Optional[str] = Field(None, description="UUID or deterministic ID of the source chunk")
    chunk_index: int = Field(..., ge=0, description="Sequential index of the source chunk")
    source_reference: Optional[str] = Field(None, description="Traceable reference (e.g. page:1, claim:1)")
    section: Optional[str] = Field(None, description="Document section ('claims', 'abstract', etc.)")
    page_number: Optional[int] = Field(None, description="Page number if available")
    claim_number: Optional[int] = Field(None, description="Claim number if originating from claims")
    evidence_span_start: Optional[int] = Field(None, description="Start character offset within chunk")
    evidence_span_end: Optional[int] = Field(None, description="End character offset within chunk")


class FeatureCandidate(BaseModel):
    """Unvalidated raw feature candidate extracted directly from a document chunk."""
    model_config = ConfigDict(extra="ignore")

    feature_type: FeatureType
    feature_text: str = Field(..., min_length=1)
    source_chunk_id: Optional[str] = None
    source_chunk_index: int = Field(default=0, ge=0)
    source_reference: Optional[str] = None
    section: Optional[str] = None
    page_number: Optional[int] = None
    claim_number: Optional[int] = None
    evidence_span_start: Optional[int] = None
    evidence_span_end: Optional[int] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    extraction_method: str = "rule_based"

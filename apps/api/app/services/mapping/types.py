from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.services.features.feature_schema import TechnicalFeature
from app.services.reranking.types import RerankedResult


class EvidenceRelationship(str, Enum):
    """Controlled vocabulary for feature-to-evidence technical relationships.

    Semantics:
    - direct_match: Evidence closely corresponds to the full technical feature.
    - partial_match: Only part of the feature elements are represented.
    - contextual_match: Provides technically relevant context without directly disclosing the full feature.
    - weak_match: Limited technical correspondence or incidental keyword overlap.
    - no_material_match: Insufficient technical correspondence.
    (NOTE: This is NOT a legal patentability, novelty, or obviousness decision).
    """
    DIRECT_MATCH = "direct_match"
    PARTIAL_MATCH = "partial_match"
    CONTEXTUAL_MATCH = "contextual_match"
    WEAK_MATCH = "weak_match"
    NO_MATERIAL_MATCH = "no_material_match"


class FeatureEvidenceMapping(BaseModel):
    """Canonical representation connecting a technical feature to prior-art evidence."""
    model_config = ConfigDict(extra="ignore")

    mapping_id: str = Field(..., description="Stable deterministic mapping identifier")
    project_id: str = Field(..., description="Project identifier")

    # Feature traceability
    feature_id: str = Field(..., description="Originating technical feature ID")
    feature_type: str = Field(..., description="Feature category (component, function, etc.)")
    feature_text: str = Field(..., description="Verbatim text of the technical feature")
    normalized_text: Optional[str] = Field(None, description="Normalized feature text")

    # Evidence traceability
    patent_number: str = Field(..., description="Target prior-art patent number")
    patent_id: Optional[str] = Field(None, description="Prior-art database ID if available")
    chunk_id: Optional[str] = Field(None, description="Chunk UUID or point ID")
    chunk_index: int = Field(..., ge=0, description="Sequential index of the evidence chunk")
    evidence_text: str = Field(..., description="Verbatim text of the prior-art passage")
    section: str = Field(default="description", description="Patent section ('claims', 'abstract', etc.)")
    claim_number: Optional[int] = Field(None, description="Specific claim number if section is 'claims'")
    page_number: Optional[int] = Field(None, description="Evidence page number")
    paragraph_id: Optional[str] = Field(None, description="Paragraph or claim identifier")
    title: Optional[str] = Field(None, description="Prior-art patent title")
    country_code: Optional[str] = Field(None, description="Country jurisdiction (e.g. 'US')")
    publication_date: Optional[str] = Field(None, description="Patent publication date (YYYY-MM-DD)")
    ipc_classes: List[str] = Field(default_factory=list, description="IPC classification codes")
    cpc_classes: List[str] = Field(default_factory=list, description="CPC classification codes")
    source: Optional[str] = Field(default="custom", description="Corpus source origin")

    # Upstream retrieval signals
    retrieval_method: str = Field(default="hybrid_rrf_reranked")
    sparse_rank: Optional[int] = Field(None, description="Rank in BM25 lexical pool")
    dense_rank: Optional[int] = Field(None, description="Rank in BGE dense pool")
    sparse_score: Optional[float] = Field(None, description="Raw BM25 score")
    dense_score: Optional[float] = Field(None, description="Cosine semantic similarity score")
    rrf_score: Optional[float] = Field(None, description="Reciprocal Rank Fusion score")
    reranker_score: Optional[float] = Field(None, description="Raw Cross-Encoder relevance score")
    reranker_rank: Optional[int] = Field(None, description="Rank in BGE reranked pool")
    fusion_methods: List[str] = Field(default_factory=list)

    # Mapping signals
    lexical_similarity: float = Field(..., ge=0.0, le=1.0, description="Token-level Jaccard overlap similarity")
    semantic_similarity: float = Field(..., ge=0.0, le=1.0, description="Dense embedding cosine similarity")
    matching_score: float = Field(..., ge=0.0, le=1.0, description="Combined weighted matching score")
    evidence_relationship: EvidenceRelationship = Field(..., description="Classified technical relationship")
    mapping_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in correspondence quality (NOT patentability/novelty)",
    )


class MappingMetadata(BaseModel):
    """Metadata and execution telemetry for feature-to-evidence mapping."""
    model_config = ConfigDict(extra="ignore")

    number_of_features: int = Field(..., ge=0)
    number_of_evidence_candidates: int = Field(..., ge=0)
    number_of_mappings: int = Field(..., ge=0)
    relationship_distribution: Dict[str, int] = Field(default_factory=dict)
    average_matching_score: float = Field(..., ge=0.0, le=1.0)
    average_mapping_confidence: float = Field(..., ge=0.0, le=1.0)
    mapping_top_k: int = Field(..., ge=1)
    lexical_weight: float = Field(..., ge=0.0, le=1.0)
    semantic_weight: float = Field(..., ge=0.0, le=1.0)
    threshold_configuration: Dict[str, float] = Field(default_factory=dict)
    mapping_method: str = Field(default="hybrid_lexical_semantic")


class FeatureEvidenceMappingRequest(BaseModel):
    """Request payload for mapping technical features to retrieved prior-art evidence."""
    model_config = ConfigDict(extra="ignore")

    project_id: str = Field(..., max_length=128)
    features: List[TechnicalFeature] = Field(default_factory=list)
    evidence: List[RerankedResult] = Field(default_factory=list)
    top_k: Optional[int] = Field(default=5, ge=1, le=50)
    lexical_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    semantic_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class FeatureEvidenceMappingResponse(BaseModel):
    """Response containing structured feature-to-evidence mappings and execution metadata."""
    model_config = ConfigDict(extra="ignore")

    project_id: str
    mappings: List[FeatureEvidenceMapping]
    total_mappings: int
    mapping_metadata: MappingMetadata

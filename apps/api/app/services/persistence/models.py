from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ProjectCreate(BaseModel):
    """Payload for creating a new user project workspace."""
    model_config = ConfigDict(extra="ignore")

    user_id: str = Field(..., description="Owner UUID (auth.uid())")
    title: str = Field(..., description="Project workspace title")
    description: Optional[str] = Field(None, description="Invention overview/description")
    original_file_name: str = Field(..., description="Original name of uploaded document")
    stored_file_name: str = Field(..., description="UUID or sanitized filename on disk/storage")
    file_path: str = Field(..., description="Relative or absolute storage path")
    file_type: str = Field(..., description="Document type (pdf, docx, txt)")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    status: str = Field(default="uploaded", description="Lifecycle status")
    processing_stage: str = Field(default="uploaded", description="Current pipeline stage")


class ProjectRecord(BaseModel):
    """Database representation of public.projects."""
    model_config = ConfigDict(extra="ignore")

    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    original_file_name: str
    stored_file_name: str
    file_path: str
    file_type: str
    file_size: int
    status: str = "uploaded"
    processing_stage: str = "uploaded"
    extracted_text: Optional[str] = None
    extracted_metadata: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    report_generated: bool = False
    progress: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DocumentChunkRecord(BaseModel):
    """Database representation of public.document_chunks."""
    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = None
    project_id: str
    chunk_index: int
    section: Optional[str] = "unknown"
    page_number: Optional[int] = None
    source_reference: Optional[str] = None
    text: str
    start_character: int
    end_character: int
    token_estimate: int
    embedding_status: str = "pending"
    created_at: Optional[datetime] = None


class FeatureRecord(BaseModel):
    """Database representation of public.features."""
    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = None
    project_id: str
    feature_id: str
    title: str
    description: str
    technical_category: str
    importance: str = "medium"  # 'high', 'medium', 'low'
    source_text_span: str
    extraction_confidence: float
    created_at: Optional[datetime] = None


class EvidenceItemRecord(BaseModel):
    """Database representation of public.evidence_items."""
    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = None
    project_id: str
    feature_id: str  # Foreign key UUID pointing to features(id) or mapped
    patent_id: str   # Foreign key UUID pointing to patent_documents(id)
    chunk_text: str
    retrieved_source: str
    retrieval_method: str = "hybrid_rrf"
    retrieval_similarity: float
    reranker_score: Optional[float] = None
    rank: Optional[int] = None
    section: Optional[str] = None
    claim_number: Optional[int] = None
    page_number: Optional[int] = None
    evidence_strength: float
    confidence: float = 1.0
    evidence_relationship: str
    created_at: Optional[datetime] = None


class AnalysisRecord(BaseModel):
    """Database representation of public.analyses."""
    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = None
    project_id: str
    readiness_score: int  # 0-100 integer
    confidence_score: float  # 0.0-1.0
    readiness_category: str
    novelty_score: int
    overlap_score: int
    differentiation_score: int
    documentation_score: int
    innovation_characteristics: Dict[str, Any] = Field(default_factory=dict)
    commercial_potential: Dict[str, Any] = Field(default_factory=dict)
    explanation: str
    recommendations: List[str] = Field(default_factory=list)
    uncertainty_flags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    model_used: str
    processing_time: int
    retrieved_chunk_count: int = 0
    retrieved_patents: List[str] = Field(default_factory=list)
    status: str = "completed"
    created_at: Optional[datetime] = None


class ReportRecord(BaseModel):
    """Database representation of public.reports."""
    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = None
    project_id: str
    type: str = "json"  # 'pdf', 'json', 'markdown'
    file_path: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


class PatentDocumentRecord(BaseModel):
    """Database representation of public.patent_documents."""
    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = None
    patent_number: str
    publication_number: Optional[str] = None
    application_number: Optional[str] = None
    country_code: str = "US"
    title: str
    abstract: str
    inventors: List[str] = Field(default_factory=list)
    assignee: Optional[str] = None
    publication_date: Optional[str] = None
    filing_date: Optional[str] = None
    priority_date: Optional[str] = None
    ipc_classes: List[str] = Field(default_factory=list)
    cpc_classes: List[str] = Field(default_factory=list)
    language: str = "en"
    source: str = "custom"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


class PatentChunkRecord(BaseModel):
    """Database representation of public.patent_chunks."""
    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = None
    patent_id: str
    chunk_index: int
    section: Optional[str] = None
    claim_number: Optional[int] = None
    page_number: Optional[int] = None
    paragraph_id: Optional[str] = None
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding_status: str = "pending"
    created_at: Optional[datetime] = None


class PersistenceStatus(BaseModel):
    """Standardized response status for database persistence operations."""
    success: bool
    status: str  # 'persisted', 'unconfigured', 'failed', 'partial'
    record_id: Optional[str] = None
    affected_count: int = 0
    details: Optional[str] = None
    error: Optional[str] = None

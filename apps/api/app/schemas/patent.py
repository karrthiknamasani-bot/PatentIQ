from datetime import date
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator


class PatentProvenance(BaseModel):
    """Origin and retrieval metadata for patent records."""
    model_config = ConfigDict(extra="ignore")

    source: str = Field(default="custom", description="Source repository or dataset (e.g., 'uspto', 'google_patents')")
    source_url: Optional[str] = Field(default=None, description="Direct URL to official publication")
    source_dataset: Optional[str] = Field(default=None, description="Dataset release or collection name")
    retrieved_at: Optional[str] = Field(default=None, description="ISO timestamp of data retrieval")


class PatentDocumentBase(BaseModel):
    """Canonical representation of a prior-art patent document, matching public.patent_documents schema."""
    model_config = ConfigDict(extra="ignore")

    patent_number: str = Field(default="", description="Unique patent identifier, e.g. 'US-10492811-B2'")
    publication_number: Optional[str] = Field(default=None, description="Official publication number")
    application_number: Optional[str] = Field(default=None, description="Filing application number")
    country_code: str = Field(default="US", description="Two-letter ISO/WIPO issuing jurisdiction")
    title: str = Field(default="", description="Official patent title")
    abstract: str = Field(default="", description="Patent abstract text")
    inventors: List[str] = Field(default_factory=list, description="List of inventor full names")
    assignee: Optional[str] = Field(default=None, description="Assignee or applicant organisation")
    publication_date: Optional[Union[date, str]] = Field(default=None, description="Publication date (YYYY-MM-DD)")
    filing_date: Optional[Union[date, str]] = Field(default=None, description="Filing date (YYYY-MM-DD)")
    priority_date: Optional[Union[date, str]] = Field(default=None, description="Earliest priority date (YYYY-MM-DD)")
    ipc_classes: List[str] = Field(default_factory=list, description="International Patent Classification codes")
    cpc_classes: List[str] = Field(default_factory=list, description="Cooperative Patent Classification codes")
    language: str = Field(default="en", description="ISO 639-1 language code")
    source: str = Field(default="custom", description="Corpus source origin")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary provenance and supplemental metadata")

    # Optional extended text content used during corpus ingestion/chunking
    claims: Optional[Union[List[str], str]] = Field(default=None, description="Raw claims text or list of individual claims")
    description: Optional[str] = Field(default=None, description="Full or summary description body")

    @field_validator("country_code")
    @classmethod
    def normalize_country(cls, v: str) -> str:
        return v.strip().upper() if v else "US"


class PatentDocumentCreate(PatentDocumentBase):
    """Payload for creating a patent document in the corpus."""
    pass


class PatentDocument(PatentDocumentBase):
    """Fully realized patent document with database identifier."""
    id: Optional[str] = Field(default=None, description="UUID matching public.patent_documents.id")
    created_at: Optional[str] = None


class PatentChunkBase(BaseModel):
    """Canonical representation of an evidence passage, matching public.patent_chunks schema."""
    model_config = ConfigDict(extra="ignore")

    patent_number: str = Field(..., description="Reference to parent patent number")
    patent_id: Optional[str] = Field(default=None, description="UUID of parent patent_documents record")
    chunk_index: int = Field(..., ge=0, description="Zero-based sequence index within patent")
    section: str = Field(default="description", description="Section: 'claims', 'abstract', 'description', 'background', etc.")
    claim_number: Optional[int] = Field(default=None, ge=1, description="Claim index if section is 'claims'")
    page_number: Optional[int] = Field(default=None, description="Source page number")
    paragraph_id: Optional[str] = Field(default=None, description="Source paragraph identifier, e.g. '[0042]' or 'claim:1'")
    text: str = Field(..., min_length=1, description="Verbatim chunk text")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary for citations and search")
    embedding_status: str = Field(default="pending", description="'pending', 'synced', 'failed'")


class PatentChunkCreate(PatentChunkBase):
    """Payload for creating a patent chunk."""
    pass


class PatentChunk(PatentChunkBase):
    """Fully realized patent chunk with database identifier."""
    id: Optional[str] = Field(default=None, description="UUID matching public.patent_chunks.id")
    created_at: Optional[str] = None


class ValidationIssue(BaseModel):
    """A single validation finding (error or warning)."""
    severity: str = Field(..., description="'ERROR' or 'WARNING'")
    patent_number: Optional[str] = Field(default=None)
    field: Optional[str] = Field(default=None)
    message: str = Field(...)


class CorpusValidationReport(BaseModel):
    """Detailed validation report across a corpus batch or directory."""
    total_records_inspected: int = 0
    valid_records_count: int = 0
    invalid_records_count: int = 0
    warning_count: int = 0
    duplicate_patent_count: int = 0
    duplicate_chunk_count: int = 0
    issues: List[ValidationIssue] = Field(default_factory=list)
    is_valid: bool = True


class CorpusQualityStats(BaseModel):
    """Aggregated statistics demonstrating prior-art corpus completeness and balance."""
    total_patents: int = 0
    total_chunks: int = 0
    avg_chunks_per_patent: float = 0.0
    claims_count: int = 0
    abstract_chunks_count: int = 0
    description_chunks_count: int = 0
    chunks_by_section: Dict[str, int] = Field(default_factory=dict)
    missing_metadata: Dict[str, int] = Field(default_factory=dict)
    jurisdictions: Dict[str, int] = Field(default_factory=dict)
    languages: Dict[str, int] = Field(default_factory=dict)
    duplicate_records: int = 0
    invalid_records: int = 0


class CorpusManifest(BaseModel):
    """Reproducible manifest describing an ingested patent prior-art corpus."""
    model_config = ConfigDict(extra="ignore")

    corpus_name: str = Field(default="PatentIQ-PriorArt-Core")
    version: str = Field(default="1.0.0")
    source: str = Field(default="USPTO / Google Patents Public Data")
    acquisition_date: str = Field(...)
    num_patents: int = 0
    num_chunks: int = 0
    languages: List[str] = Field(default_factory=lambda: ["en"])
    jurisdictions: List[str] = Field(default_factory=lambda: ["US"])
    schema_version: str = Field(default="1.0.0")
    checksums: Dict[str, str] = Field(default_factory=dict, description="SHA-256 integrity hashes for data files")
    metadata: Dict[str, Any] = Field(default_factory=dict)

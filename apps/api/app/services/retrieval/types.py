from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class RetrievalFilters(BaseModel):
    """Optional metadata filters for narrowing retrieval scope."""
    model_config = ConfigDict(extra="ignore")

    country_code: Optional[str] = Field(default=None, description="2-letter jurisdiction code, e.g. 'US'")
    cpc_class: Optional[str] = Field(default=None, description="Cooperative Patent Classification prefix, e.g. 'G06F'")
    ipc_class: Optional[str] = Field(default=None, description="International Patent Classification prefix, e.g. 'A61B'")
    language: Optional[str] = Field(default=None, description="Language code, e.g. 'en'")
    date_from: Optional[str] = Field(default=None, description="Publication date lower bound (YYYY-MM-DD)")
    date_to: Optional[str] = Field(default=None, description="Publication date upper bound (YYYY-MM-DD)")
    section: Optional[str] = Field(default=None, description="Specific section filter ('claims', 'abstract', etc.)")
    claim_only: Optional[bool] = Field(default=None, description="If True, restricts results strictly to patent claims")


class RetrievalResult(BaseModel):
    """Canonical representation of a retrieved prior-art passage."""
    model_config = ConfigDict(extra="ignore")

    patent_number: str = Field(..., description="Unique patent identifier, e.g. 'US-10492811-B2'")
    patent_id: Optional[str] = Field(default=None, description="Parent document UUID if registered in DB")
    chunk_id: Optional[str] = Field(default=None, description="Chunk UUID or deterministic point ID")
    chunk_index: int = Field(..., ge=0, description="Sequential chunk index within patent")
    text: str = Field(..., description="Verbatim retrieved passage text")
    section: str = Field(default="description", description="Patent section ('claims', 'abstract', etc.)")
    claim_number: Optional[int] = Field(default=None, description="Specific claim number if section is 'claims'")
    page_number: Optional[int] = Field(default=None, description="Source page number")
    paragraph_id: Optional[str] = Field(default=None, description="Source paragraph or claim identifier")
    retrieval_method: str = Field(..., description="'sparse_bm25' or 'dense'")
    retrieval_score: float = Field(..., description="Score assigned by retrieval algorithm")
    rank: int = Field(..., ge=1, description="1-based rank in retrieved candidate list")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata for citation, title, assignee, date")


class RRFResult(BaseModel):
    """Canonical representation of a fused prior-art candidate via Reciprocal Rank Fusion."""
    model_config = ConfigDict(extra="ignore")

    patent_number: str = Field(..., description="Unique patent identifier, e.g. 'US-10492811-B2'")
    chunk_index: int = Field(..., ge=0, description="Sequential chunk index within patent")
    chunk_id: Optional[str] = Field(default=None, description="Chunk UUID or deterministic point ID")
    text: str = Field(..., description="Verbatim retrieved passage text")
    section: str = Field(default="description", description="Patent section ('claims', 'abstract', etc.)")
    claim_number: Optional[int] = Field(default=None, description="Specific claim number if section is 'claims'")
    page_number: Optional[int] = Field(default=None, description="Source page number")
    paragraph_id: Optional[str] = Field(default=None, description="Source paragraph or claim identifier")
    source: str = Field(default="custom", description="Corpus source origin")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata for citation, title, assignee, date")

    sparse_rank: Optional[int] = Field(default=None, description="1-based rank in BM25 results, or None if absent")
    dense_rank: Optional[int] = Field(default=None, description="1-based rank in Dense results, or None if absent")
    sparse_score: Optional[float] = Field(default=None, description="Original BM25 lexical score")
    dense_score: Optional[float] = Field(default=None, description="Original Dense semantic similarity score")
    rrf_score: float = Field(..., description="Fused score calculated as sum of 1 / (k + rank)")
    fusion_methods: List[str] = Field(default_factory=list, description="Methods that retrieved this candidate")
    final_rank: int = Field(..., ge=1, description="Final 1-based rank in unified fused candidate list")
    retrieval_method: str = Field(default="hybrid_rrf", description="Fixed identifier 'hybrid_rrf'")


from app.services.reranking.types import RerankedResult


class SearchRequest(BaseModel):
    """Request payload for hybrid/separate prior art search."""
    model_config = ConfigDict(extra="ignore")

    query: str = Field(..., min_length=1, description="Invention feature, disclosure text, or search query")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of top results to return per method")
    rerank: bool = Field(default=False, description="If True, applies BGE cross-encoder reranking to hybrid RRF candidates")
    filters: Optional[RetrievalFilters] = Field(default=None, description="Optional metadata constraints")
    methods: List[str] = Field(
        default_factory=lambda: ["sparse", "dense"],
        description="Retrieval methods to execute: ['sparse'], ['dense'], or ['sparse', 'dense']",
    )


class SearchResponse(BaseModel):
    """Unified search response returning distinct sparse, dense, hybrid, and reranked candidate sets."""
    model_config = ConfigDict(extra="ignore")

    query: str
    top_k: int
    sparse_results: Optional[List[RetrievalResult]] = Field(default=None, description="Ranked BM25 lexical results")
    dense_results: Optional[List[RetrievalResult]] = Field(default=None, description="Ranked BGE dense semantic results")
    hybrid_results: Optional[List[RRFResult]] = Field(default=None, description="Ranked hybrid results fused via RRF")
    reranked_results: Optional[List[RerankedResult]] = Field(default=None, description="Ranked candidates scored by BGE Cross-Encoder")
    total_sparse_hits: Optional[int] = None
    total_dense_hits: Optional[int] = None
    total_hybrid_hits: Optional[int] = None
    total_reranked_hits: Optional[int] = None

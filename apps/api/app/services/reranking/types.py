from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class BaseReranker(ABC):
    """Abstract base interface for pairwise cross-encoder relevance models."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns the canonical model identifier."""
        ...

    @abstractmethod
    def score(
        self,
        pairs: List[Tuple[str, str]],
        batch_size: int = 8,
    ) -> List[float]:
        """Calculates pairwise relevance scores for a list of (query, passage) tuples.

        Args:
            pairs: List of (query, candidate_text) tuples.
            batch_size: Batch size for model inference.

        Returns:
            List of raw float relevance scores directly from the model.
        """
        ...


class RerankedResult(BaseModel):
    """Canonical representation of a prior-art passage reranked by a Cross-Encoder."""
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
    source: Optional[str] = Field(default="custom", description="Corpus source origin")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata for citation, title, assignee, date")

    # Original retrieval & fusion traceability
    sparse_rank: Optional[int] = Field(default=None, description="1-based rank in BM25 lexical results")
    dense_rank: Optional[int] = Field(default=None, description="1-based rank in Dense semantic results")
    sparse_score: Optional[float] = Field(default=None, description="Original BM25 lexical score")
    dense_score: Optional[float] = Field(default=None, description="Original Dense semantic similarity score")
    rrf_score: float = Field(..., description="Fused RRF score")
    fusion_methods: List[str] = Field(default_factory=list, description="Methods that retrieved this candidate")

    # Cross-encoder reranking outputs
    reranker_score: float = Field(..., description="Raw relevance score computed by the Cross-Encoder model")
    reranker_rank: int = Field(..., ge=1, description="1-based rank assigned after cross-encoder scoring")
    retrieval_method: str = Field(default="hybrid_rrf_reranked", description="Fixed identifier 'hybrid_rrf_reranked'")

"""Patent Prior-Art Hybrid Retrieval Package (Step 5: Separate Sparse and Dense layers)."""
from app.services.retrieval.types import (
    RetrievalResult,
    RRFResult,
    RetrievalFilters,
    SearchRequest,
    SearchResponse,
)
from app.services.retrieval.corpus_loader import RetrievalCorpusLoader
from app.services.retrieval.bm25_retriever import BM25Retriever
from app.services.retrieval.embedding_provider import (
    EmbeddingProviderBase,
    BGEEmbeddingProvider,
    MockEmbeddingProvider,
)
from app.services.retrieval.qdrant_store import QdrantVectorStore, generate_point_id
from app.services.retrieval.dense_retriever import DenseRetriever
from app.services.retrieval.metadata_filter import MetadataFilterMatcher
from app.services.retrieval.rrf_fusion import ReciprocalRankFusion
from app.services.retrieval.retrieval_service import PatentRetrievalService, retrieval_service

__all__ = [
    "RetrievalResult",
    "RRFResult",
    "RetrievalFilters",
    "SearchRequest",
    "SearchResponse",
    "RetrievalCorpusLoader",
    "BM25Retriever",
    "EmbeddingProviderBase",
    "BGEEmbeddingProvider",
    "MockEmbeddingProvider",
    "QdrantVectorStore",
    "generate_point_id",
    "DenseRetriever",
    "MetadataFilterMatcher",
    "ReciprocalRankFusion",
    "PatentRetrievalService",
    "retrieval_service",
]

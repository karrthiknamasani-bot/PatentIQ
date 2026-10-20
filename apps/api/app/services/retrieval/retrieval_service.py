import logging
from typing import List, Optional, Any
from app.schemas.patent import PatentChunkCreate
from app.services.retrieval.types import (
    SearchRequest,
    SearchResponse,
    RetrievalResult,
    RRFResult,
    RetrievalFilters,
)
from app.services.retrieval.bm25_retriever import BM25Retriever
from app.services.retrieval.dense_retriever import DenseRetriever
from app.services.retrieval.corpus_loader import RetrievalCorpusLoader
from app.services.retrieval.rrf_fusion import ReciprocalRankFusion
from app.services.reranking.types import RerankedResult
from app.core.config import settings

logger = logging.getLogger("patentiq.retrieval")


class PatentRetrievalService:
    """Unified service orchestrating sparse BM25, dense BGE vector searches,
    Reciprocal Rank Fusion (RRF), and BGE Cross-Encoder reranking over the patent corpus.
    """

    def __init__(
        self,
        bm25_retriever: Optional[BM25Retriever] = None,
        dense_retriever: Optional[DenseRetriever] = None,
        rrf_fusion: Optional[ReciprocalRankFusion] = None,
        reranker_service: Optional[Any] = None,
    ):
        self.bm25_retriever = bm25_retriever or BM25Retriever()
        self.dense_retriever = dense_retriever or DenseRetriever()
        self.rrf = rrf_fusion or ReciprocalRankFusion(k=settings.RRF_K)
        self._reranker_service = reranker_service
        self._is_sparse_indexed = False
        self._is_dense_indexed = False

    @property
    def reranker_service(self) -> Any:
        if self._reranker_service is None:
            from app.services.reranking.reranking_service import PatentRerankingService
            self._reranker_service = PatentRerankingService()
        return self._reranker_service

    @reranker_service.setter
    def reranker_service(self, service: Any) -> None:
        self._reranker_service = service

    def initialize_from_corpus(
        self,
        corpus_path: Optional[str] = None,
        index_dense: bool = True,
        force: bool = False,
    ) -> int:
        """Loads canonical chunks from disk and initializes the retrieval indices."""
        import os
        import pickle

        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
        bm25_pilot_path = os.path.join(repo_root, "data", "real_patents_pilot", "bm25_index.pkl")

        # 1. Index BM25 (load prebuilt pilot index if available and no custom corpus specified)
        if not self._is_sparse_indexed or force:
            if not corpus_path and os.path.exists(bm25_pilot_path) and not force:
                try:
                    with open(bm25_pilot_path, "rb") as f:
                        self.bm25_retriever = pickle.load(f)
                    self._is_sparse_indexed = True
                    logger.info("Loaded prebuilt BM25 index with %d chunks from %s", len(self.bm25_retriever.chunks), bm25_pilot_path)
                except Exception as e:
                    logger.warning("Failed to load prebuilt BM25 index: %s. Falling back to fresh indexing.", e)

            if not self._is_sparse_indexed:
                chunks = RetrievalCorpusLoader.load_chunks(corpus_path)
                logger.info(f"Indexing {len(chunks)} prior-art chunks into retrieval engines...")
                self.bm25_retriever.index_chunks(chunks)
                self._is_sparse_indexed = True

        # 2. Index Dense (check if Qdrant collection already populated)
        if (index_dense and not self._is_dense_indexed) or force:
            try:
                client = self.dense_retriever.vector_store.get_client()
                coll_name = self.dense_retriever.vector_store.collection_name
                count = client.count(coll_name).count if client else 0
                if count > 0 and not force:
                    self._is_dense_indexed = True
                    logger.info("Found %d existing vector points in Qdrant collection '%s'. Skipping dense re-indexing.", count, coll_name)
                else:
                    chunks = RetrievalCorpusLoader.load_chunks(corpus_path)
                    self.dense_retriever.index_chunks(chunks)
                    self._is_dense_indexed = True
            except Exception as e:
                logger.warning(f"Dense indexing deferred or failed: {e}")

        return len(self.bm25_retriever.chunks) if self.bm25_retriever else 0

    def search_sparse(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[RetrievalFilters] = None,
    ) -> List[RetrievalResult]:
        """Executes BM25 sparse lexical retrieval."""
        if not self._is_sparse_indexed:
            # Auto-index from canonical corpus if not yet loaded
            self.initialize_from_corpus(index_dense=False)
        return self.bm25_retriever.search(query, top_k=top_k, filters=filters)

    def search_dense(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[RetrievalFilters] = None,
    ) -> List[RetrievalResult]:
        """Executes BGE dense vector retrieval against Qdrant."""
        if not self._is_dense_indexed:
            try:
                self.initialize_from_corpus(index_dense=True)
            except Exception as exc:
                logger.warning("Dense auto-indexing deferred or failed: %s", exc)
        try:
            return self.dense_retriever.search(query, top_k=top_k, filters=filters)
        except Exception as exc:
            logger.warning("Dense retrieval unavailable or failed: %s", exc)
            return []

    def search_hybrid(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[RetrievalFilters] = None,
        candidate_depth: Optional[int] = None,
    ) -> List[RRFResult]:
        """Executes hybrid retrieval by querying sparse and dense retrieval engines at depth

        candidate_depth, then fusing candidate ranks via Reciprocal Rank Fusion (RRF).
        """
        # Retrieve candidate pool (defaulting to max(top_k * 2, RRF_CANDIDATE_DEPTH))
        depth = candidate_depth or max(top_k * 2, settings.RRF_CANDIDATE_DEPTH)

        sparse_pool = self.search_sparse(query=query, top_k=depth, filters=filters)
        dense_pool = self.search_dense(query=query, top_k=depth, filters=filters)

        return self.rrf.fuse(sparse_results=sparse_pool, dense_results=dense_pool, top_k=top_k)

    def search(self, request: SearchRequest) -> SearchResponse:
        """Executes search according to requested methods.

        If both sparse and dense (or hybrid) are requested, fuses candidate ranks into hybrid_results.
        """
        normalized_methods = [m.lower().strip() for m in request.methods]
        is_hybrid_requested = (
            ("sparse" in normalized_methods and "dense" in normalized_methods)
            or "hybrid" in normalized_methods
            or "rrf" in normalized_methods
        )

        sparse_results: Optional[List[RetrievalResult]] = None
        dense_results: Optional[List[RetrievalResult]] = None
        hybrid_results: Optional[List[RRFResult]] = None
        reranked_results: Optional[List[RerankedResult]] = None

        if "sparse" in normalized_methods or "bm25" in normalized_methods or is_hybrid_requested:
            sparse_results = self.search_sparse(
                query=request.query,
                top_k=request.top_k,
                filters=request.filters,
            )

        if "dense" in normalized_methods or "vector" in normalized_methods or is_hybrid_requested:
            dense_results = self.search_dense(
                query=request.query,
                top_k=request.top_k,
                filters=request.filters,
            )

        if is_hybrid_requested:
            # For hybrid fusion & reranking, fetch wider candidate pools
            pool_depth = max(request.top_k * 2, settings.RRF_CANDIDATE_DEPTH)
            if request.rerank:
                pool_depth = max(pool_depth, settings.RERANKER_CANDIDATE_DEPTH * 2)

            sparse_pool = (
                sparse_results
                if (sparse_results and len(sparse_results) >= pool_depth)
                else self.search_sparse(query=request.query, top_k=pool_depth, filters=request.filters)
            )
            dense_pool = (
                dense_results
                if (dense_results and len(dense_results) >= pool_depth)
                else self.search_dense(query=request.query, top_k=pool_depth, filters=request.filters)
            )

            hybrid_results = self.rrf.fuse(
                sparse_results=sparse_pool,
                dense_results=dense_pool,
                top_k=request.top_k,
            )

            if request.rerank:
                rerank_depth = max(request.top_k, settings.RERANKER_CANDIDATE_DEPTH)
                rrf_candidates = self.rrf.fuse(
                    sparse_results=sparse_pool,
                    dense_results=dense_pool,
                    top_k=rerank_depth,
                )
                reranked_results = self.reranker_service.rerank(
                    query=request.query,
                    candidates=rrf_candidates,
                    top_k=request.top_k,
                )
        elif request.rerank:
            raise ValueError(
                "Reranking requires hybrid retrieval candidates (both 'sparse' and 'dense' methods must be specified)."
            )

        return SearchResponse(
            query=request.query,
            top_k=request.top_k,
            sparse_results=sparse_results,
            dense_results=dense_results,
            hybrid_results=hybrid_results,
            reranked_results=reranked_results,
            total_sparse_hits=len(sparse_results) if sparse_results is not None else None,
            total_dense_hits=len(dense_results) if dense_results is not None else None,
            total_hybrid_hits=len(hybrid_results) if hybrid_results is not None else None,
            total_reranked_hits=len(reranked_results) if reranked_results is not None else None,
        )


# Global singleton instance for FastAPI dependency injection
retrieval_service = PatentRetrievalService()

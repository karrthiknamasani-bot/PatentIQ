from typing import List, Dict, Tuple, Optional
from app.services.retrieval.types import RetrievalResult, RRFResult
from app.core.config import settings


class ReciprocalRankFusion:
    """Combines ranked candidate lists from disparate retrieval mechanisms (e.g. BM25 and Dense BGE)

    using standard Reciprocal Rank Fusion (RRF):

        RRF(d) = \\sum_{m \\in M} \\frac{1}{k + rank_m(d)}

    Why Rank-Based Fusion?
        BM25 produces unbounded lexical relevance scores based on TF-IDF statistics, while dense models
        produce bounded cosine similarity scores. Direct score normalization (e.g. min-max or z-score)
        is sensitive to score distribution skews and outliers. RRF uses ordinal ranking rather than
        raw magnitude, providing robust, calibration-free fusion across heterogeneous searchers.
    """

    def __init__(self, k: Optional[int] = None):
        """Initializes RRF engine.

        Args:
            k: Smoothing constant balancing penalty of higher vs lower ranks. Default 60 (standard Cormack et al.).
        """
        self.k = k if k is not None else settings.RRF_K

    @classmethod
    def get_candidate_key(cls, item: RetrievalResult) -> str:
        """Returns stable, collision-free candidate identity (patent_number + chunk_index)."""
        return f"{item.patent_number.strip().upper()}#{item.chunk_index}"

    def fuse(
        self,
        sparse_results: List[RetrievalResult],
        dense_results: List[RetrievalResult],
        top_k: Optional[int] = None,
    ) -> List[RRFResult]:
        """Fuses sparse and dense retrieval result lists into a single ranked list.

        Args:
            sparse_results: Ranked list from BM25 lexical retrieval.
            dense_results: Ranked list from BGE semantic vector retrieval.
            top_k: Optional cutoff for final output candidate count.

        Returns:
            Ranked list of RRFResult instances sorted by rrf_score descending with deterministic tie-breaking.
        """
        # 1. Deduplicate candidates within each list (preserving earliest / best rank)
        deduped_sparse: Dict[str, RetrievalResult] = {}
        for item in sparse_results:
            key = self.get_candidate_key(item)
            if key not in deduped_sparse:
                deduped_sparse[key] = item

        deduped_dense: Dict[str, RetrievalResult] = {}
        for item in dense_results:
            key = self.get_candidate_key(item)
            if key not in deduped_dense:
                deduped_dense[key] = item

        # 2. Collect union of all unique candidate keys
        all_keys = set(deduped_sparse.keys()).union(set(deduped_dense.keys()))

        candidates_data = []

        for key in all_keys:
            sp_item = deduped_sparse.get(key)
            dn_item = deduped_dense.get(key)

            rrf_score = 0.0
            fusion_methods = []

            sparse_rank = sp_item.rank if sp_item is not None else None
            sparse_score = sp_item.retrieval_score if sp_item is not None else None
            if sparse_rank is not None:
                rrf_score += 1.0 / (self.k + sparse_rank)
                fusion_methods.append("sparse_bm25")

            dense_rank = dn_item.rank if dn_item is not None else None
            dense_score = dn_item.retrieval_score if dn_item is not None else None
            if dense_rank is not None:
                rrf_score += 1.0 / (self.k + dense_rank)
                fusion_methods.append("dense")

            # Representative item providing text and metadata
            rep_item = sp_item or dn_item
            assert rep_item is not None

            candidates_data.append({
                "patent_number": rep_item.patent_number,
                "chunk_index": rep_item.chunk_index,
                "chunk_id": rep_item.chunk_id,
                "text": rep_item.text,
                "section": rep_item.section,
                "claim_number": rep_item.claim_number,
                "page_number": rep_item.page_number,
                "paragraph_id": rep_item.paragraph_id,
                "source": rep_item.metadata.get("source", "custom") if rep_item.metadata else "custom",
                "metadata": rep_item.metadata or {},
                "sparse_rank": sparse_rank,
                "dense_rank": dense_rank,
                "sparse_score": sparse_score,
                "dense_score": dense_score,
                "rrf_score": rrf_score,
                "fusion_methods": fusion_methods,
            })

        # 3. Sort candidates:
        #    Primary: rrf_score descending (-x["rrf_score"])
        #    Tie-breaker 1: patent_number ascending (lexicographical)
        #    Tie-breaker 2: chunk_index ascending (integer)
        candidates_data.sort(
            key=lambda x: (-x["rrf_score"], x["patent_number"], x["chunk_index"])
        )

        # 4. Truncate to top_k and assign final sequential rank
        cutoff = top_k if top_k is not None else len(candidates_data)
        final_results: List[RRFResult] = []

        for final_rank, data in enumerate(candidates_data[:cutoff], start=1):
            final_results.append(
                RRFResult(
                    patent_number=data["patent_number"],
                    chunk_index=data["chunk_index"],
                    chunk_id=data["chunk_id"],
                    text=data["text"],
                    section=data["section"],
                    claim_number=data["claim_number"],
                    page_number=data["page_number"],
                    paragraph_id=data["paragraph_id"],
                    source=data["source"],
                    metadata=data["metadata"],
                    sparse_rank=data["sparse_rank"],
                    dense_rank=data["dense_rank"],
                    sparse_score=data["sparse_score"],
                    dense_score=data["dense_score"],
                    rrf_score=round(data["rrf_score"], 6),
                    fusion_methods=data["fusion_methods"],
                    final_rank=final_rank,
                    retrieval_method="hybrid_rrf",
                )
            )

        return final_results

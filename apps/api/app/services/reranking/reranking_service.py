import logging
from typing import List, Optional
from app.services.retrieval.types import RRFResult
from app.services.reranking.types import BaseReranker, RerankedResult
from app.services.reranking.bge_reranker import BGEReranker

logger = logging.getLogger("patentiq.reranking")


class PatentRerankingService:
    """Service orchestrating cross-encoder pairwise reranking over RRF candidate passages."""

    def __init__(self, reranker: Optional[BaseReranker] = None):
        self.reranker = reranker or BGEReranker()

    def rerank(
        self,
        query: str,
        candidates: List[RRFResult],
        top_k: int = 10,
    ) -> List[RerankedResult]:
        """Reranks candidate passages using the cross-encoder relevance model.

        Algorithm:
        1. Validates inputs and handles empty candidate list.
        2. Deduplicates candidates at chunk-level (patent_number#chunk_index) preserving earliest.
        3. Constructs (query, candidate_text) pairs.
        4. Runs batched cross-encoder inference.
        5. Attaches raw reranker_score.
        6. Applies deterministic tie-breaking:
           - Primary: reranker_score descending
           - Secondary: rrf_score descending
           - Tertiary: patent_number ascending
           - Quaternary: chunk_index ascending
        7. Assigns 1-based reranker_rank.
        8. Returns top_k reranked results.

        Args:
            query: Invention disclosure feature or query text.
            candidates: Ranked list of RRFResult candidate chunks.
            top_k: Number of final reranked passages to return.

        Returns:
            List of RerankedResult objects preserving all prior traceability.
        """
        if not candidates or not query.strip():
            return []

        # 1. Chunk-level deduplication
        seen_keys = set()
        deduped_candidates: List[RRFResult] = []
        for c in candidates:
            key = f"{c.patent_number}#{c.chunk_index}"
            if key not in seen_keys:
                seen_keys.add(key)
                deduped_candidates.append(c)

        if not deduped_candidates:
            return []

        # 2. Construct (query, candidate_text) pairs
        pairs = [(query, c.text) for c in deduped_candidates]

        # 3. Predict pairwise relevance scores
        scores = self.reranker.score(pairs)

        # 4. Pair candidate with computed score
        scored_candidates = list(zip(deduped_candidates, scores))

        # 5. Deterministic tie-breaking sort:
        #    - Primary: reranker_score descending (-score)
        #    - Secondary: rrf_score descending (-rrf_score)
        #    - Tertiary: patent_number ascending
        #    - Quaternary: chunk_index ascending
        scored_candidates.sort(
            key=lambda item: (
                -item[1],
                -item[0].rrf_score,
                item[0].patent_number,
                item[0].chunk_index,
            )
        )

        # 6. Truncate to top_k
        truncated = scored_candidates[:top_k]

        # 7. Construct RerankedResult objects with 1-based reranker_rank
        reranked_results: List[RerankedResult] = []
        for rank, (cand, score) in enumerate(truncated, start=1):
            reranked_results.append(
                RerankedResult(
                    patent_number=cand.patent_number,
                    patent_id=cand.metadata.get("patent_id") if cand.metadata else None,
                    chunk_id=cand.chunk_id,
                    chunk_index=cand.chunk_index,
                    text=cand.text,
                    section=cand.section,
                    claim_number=cand.claim_number,
                    page_number=cand.page_number,
                    paragraph_id=cand.paragraph_id,
                    source=cand.source,
                    metadata=cand.metadata,
                    sparse_rank=cand.sparse_rank,
                    dense_rank=cand.dense_rank,
                    sparse_score=cand.sparse_score,
                    dense_score=cand.dense_score,
                    rrf_score=cand.rrf_score,
                    fusion_methods=cand.fusion_methods,
                    reranker_score=round(float(score), 6),
                    reranker_rank=rank,
                    retrieval_method="hybrid_rrf_reranked",
                )
            )

        return reranked_results

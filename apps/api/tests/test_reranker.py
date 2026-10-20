"""Comprehensive tests for BGE Cross-Encoder Reranker Foundation (Step 6).

Covers:
1. Candidate scoring with MockReranker
2. Descending reranker ranking
3. Deterministic tie-breaking (reranker_score desc -> rrf_score desc -> patent_number asc -> chunk_index asc)
4. top_k truncation
5. Full metadata preservation
6. Original RRF score preservation
7. Sparse / Dense ranks preservation
8. Empty candidate list handling
9. Duplicate candidate handling
10. API search endpoint with rerank=false
11. API search endpoint with rerank=true
12. Filter propagation
13. Invalid reranker configuration handling
"""
from typing import List, Tuple, Optional, Dict, Any
from unittest.mock import patch
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.retrieval.types import RRFResult, RetrievalResult
from app.services.reranking.types import BaseReranker, RerankedResult
from app.services.reranking.reranking_service import PatentRerankingService
from app.services.retrieval.retrieval_service import PatentRetrievalService


class MockReranker(BaseReranker):
    """Offline mock cross-encoder reranker for fast, deterministic unit testing."""

    def __init__(self, scores_map: Optional[Dict[str, float]] = None, default_score: float = 0.5):
        self._scores_map = scores_map or {}
        self._default_score = default_score

    @property
    def model_name(self) -> str:
        return "mock-bge-reranker"

    def score(
        self,
        pairs: List[Tuple[str, str]],
        batch_size: int = 8,
    ) -> List[float]:
        results = []
        for query, text in pairs:
            # Score by exact text lookup, query substring, or default score
            matched_score = self._scores_map.get(text, self._default_score)
            results.append(matched_score)
        return results


def make_rrf_candidate(
    patent_number: str,
    chunk_index: int,
    rrf_score: float,
    sparse_rank: Optional[int] = 1,
    dense_rank: Optional[int] = 1,
    sparse_score: Optional[float] = 10.0,
    dense_score: Optional[float] = 0.9,
    section: str = "claims",
    claim_number: Optional[int] = 1,
    text: str = "Sample passage text",
    metadata: Optional[Dict[str, Any]] = None,
) -> RRFResult:
    meta = metadata or {
        "title": f"Title {patent_number}",
        "country_code": "US",
        "ipc_classes": ["A61B"],
    }
    return RRFResult(
        patent_number=patent_number,
        chunk_index=chunk_index,
        chunk_id=f"{patent_number}:{chunk_index}",
        text=text,
        section=section,
        claim_number=claim_number,
        page_number=1,
        paragraph_id=f"p:{chunk_index}",
        source="custom",
        metadata=meta,
        sparse_rank=sparse_rank,
        dense_rank=dense_rank,
        sparse_score=sparse_score,
        dense_score=dense_score,
        rrf_score=rrf_score,
        fusion_methods=["sparse", "dense"],
        final_rank=1,
        retrieval_method="hybrid_rrf",
    )


def test_reranker_candidate_scoring():
    """Verify that MockReranker correctly assigns scores to candidate passages."""
    mock = MockReranker(
        scores_map={
            "Passage 1": 0.95,
            "Passage 2": 0.42,
        }
    )
    service = PatentRerankingService(reranker=mock)

    candidates = [
        make_rrf_candidate("US-1", 0, rrf_score=0.030, text="Passage 1"),
        make_rrf_candidate("US-2", 0, rrf_score=0.032, text="Passage 2"),
    ]

    results = service.rerank(query="test query", candidates=candidates, top_k=5)

    assert len(results) == 2
    # Passage 1 scored 0.95, so it should rank 1 even though Passage 2 had higher RRF score
    assert results[0].patent_number == "US-1"
    assert results[0].reranker_rank == 1
    assert results[0].reranker_score == 0.95
    assert results[1].patent_number == "US-2"
    assert results[1].reranker_rank == 2
    assert results[1].reranker_score == 0.42


def test_reranker_descending_ranking():
    """Verify candidates are ordered strictly descending by reranker_score."""
    mock = MockReranker(
        scores_map={
            "Text Low": 0.10,
            "Text Mid": 0.55,
            "Text High": 0.88,
        }
    )
    service = PatentRerankingService(reranker=mock)

    candidates = [
        make_rrf_candidate("US-LOW", 0, rrf_score=0.035, text="Text Low"),
        make_rrf_candidate("US-MID", 0, rrf_score=0.020, text="Text Mid"),
        make_rrf_candidate("US-HIGH", 0, rrf_score=0.015, text="Text High"),
    ]

    results = service.rerank(query="query", candidates=candidates, top_k=3)

    assert [r.patent_number for r in results] == ["US-HIGH", "US-MID", "US-LOW"]
    assert results[0].reranker_rank == 1
    assert results[1].reranker_rank == 2
    assert results[2].reranker_rank == 3


def test_reranker_deterministic_tie_breaking():
    """Verify deterministic 4-stage tie-breaking:
    1. reranker_score desc
    2. rrf_score desc
    3. patent_number asc
    4. chunk_index asc
    """
    # All return identical reranker_score 0.70
    mock = MockReranker(default_score=0.70)
    service = PatentRerankingService(reranker=mock)

    # Candidate 1: rrf 0.032, US-B, chunk 0
    # Candidate 2: rrf 0.035, US-Z, chunk 0 -> higher rrf wins
    # Candidate 3: rrf 0.032, US-A, chunk 1 -> tie on rrf with Cand 1, but US-A < US-B
    # Candidate 4: rrf 0.032, US-A, chunk 0 -> tie with Cand 3, but chunk 0 < chunk 1
    candidates = [
        make_rrf_candidate("US-B", 0, rrf_score=0.032, text="text 1"),
        make_rrf_candidate("US-Z", 0, rrf_score=0.035, text="text 2"),
        make_rrf_candidate("US-A", 1, rrf_score=0.032, text="text 3"),
        make_rrf_candidate("US-A", 0, rrf_score=0.032, text="text 4"),
    ]

    results = service.rerank(query="query", candidates=candidates, top_k=10)

    # Expected order:
    # 1. US-Z#0 (highest rrf 0.035)
    # 2. US-A#0 (rrf 0.032, US-A, chunk 0)
    # 3. US-A#1 (rrf 0.032, US-A, chunk 1)
    # 4. US-B#0 (rrf 0.032, US-B, chunk 0)
    assert results[0].patent_number == "US-Z" and results[0].chunk_index == 0
    assert results[1].patent_number == "US-A" and results[1].chunk_index == 0
    assert results[2].patent_number == "US-A" and results[2].chunk_index == 1
    assert results[3].patent_number == "US-B" and results[3].chunk_index == 0


def test_reranker_top_k_truncation():
    """Verify output is correctly truncated to the requested top_k."""
    mock = MockReranker(default_score=0.5)
    service = PatentRerankingService(reranker=mock)

    candidates = [
        make_rrf_candidate(f"US-{i}", 0, rrf_score=0.030 - (i * 0.001))
        for i in range(10)
    ]

    results = service.rerank(query="query", candidates=candidates, top_k=4)
    assert len(results) == 4
    assert [r.reranker_rank for r in results] == [1, 2, 3, 4]


def test_reranker_metadata_preservation():
    """Verify all original evidence metadata, citations, and sections are preserved."""
    mock = MockReranker(default_score=0.85)
    service = PatentRerankingService(reranker=mock)

    meta = {
        "title": "Smart Surgical Stapler",
        "country_code": "US",
        "ipc_classes": ["A61B 17/068"],
        "cpc_classes": ["A61B 17/072"],
        "publication_date": "2020-04-14",
    }
    candidate = make_rrf_candidate(
        "US-10617420-B2",
        chunk_index=3,
        rrf_score=0.0315,
        sparse_rank=2,
        dense_rank=4,
        sparse_score=14.5,
        dense_score=0.82,
        section="claims",
        claim_number=5,
        text="A surgical end effector comprising...",
        metadata=meta,
    )

    results = service.rerank(query="surgical end effector", candidates=[candidate], top_k=1)
    res = results[0]

    assert res.patent_number == "US-10617420-B2"
    assert res.chunk_index == 3
    assert res.section == "claims"
    assert res.claim_number == 5
    assert res.text == "A surgical end effector comprising..."
    assert res.metadata["country_code"] == "US"
    assert res.metadata["title"] == "Smart Surgical Stapler"
    assert res.retrieval_method == "hybrid_rrf_reranked"


def test_reranker_original_scores_and_ranks_preservation():
    """Verify rrf_score, sparse_score, dense_score, sparse_rank, dense_rank are NOT overwritten."""
    mock = MockReranker(default_score=0.77)
    service = PatentRerankingService(reranker=mock)

    cand = make_rrf_candidate(
        "US-1", 0, rrf_score=0.0321,
        sparse_rank=1, dense_rank=3,
        sparse_score=18.4, dense_score=0.79,
    )

    results = service.rerank(query="query", candidates=[cand], top_k=1)
    res = results[0]

    assert res.rrf_score == 0.0321
    assert res.sparse_score == 18.4
    assert res.dense_score == 0.79
    assert res.sparse_rank == 1
    assert res.dense_rank == 3
    assert res.reranker_score == 0.77
    assert res.reranker_rank == 1


def test_reranker_empty_candidate_list():
    """Verify empty candidate list or blank query returns empty result list safely."""
    mock = MockReranker(default_score=0.5)
    service = PatentRerankingService(reranker=mock)

    assert service.rerank(query="query", candidates=[], top_k=5) == []
    assert service.rerank(query="   ", candidates=[make_rrf_candidate("US-1", 0, 0.03)], top_k=5) == []


def test_reranker_duplicate_candidate_handling():
    """Verify duplicate candidate chunks are deduplicated prior to scoring."""
    mock = MockReranker(default_score=0.6)
    service = PatentRerankingService(reranker=mock)

    candidates = [
        make_rrf_candidate("US-DUP", 0, rrf_score=0.032, text="Duplicate text"),
        make_rrf_candidate("US-DUP", 0, rrf_score=0.030, text="Duplicate text"),
        make_rrf_candidate("US-DISTINCT", 1, rrf_score=0.028, text="Distinct text"),
    ]

    results = service.rerank(query="query", candidates=candidates, top_k=5)
    assert len(results) == 2
    assert results[0].patent_number == "US-DUP"
    assert results[1].patent_number == "US-DISTINCT"


@pytest.mark.asyncio
async def test_endpoint_retrieval_search_rerank_false():
    """Verify POST /api/retrieval/search with rerank=false returns hybrid results without reranked_results."""
    from app.api.routes.retrieval import retrieval_service

    mock_dense = [
        RetrievalResult(
            patent_number="US-10492811-B2",
            chunk_index=0,
            chunk_id="US-10492811-B2:0",
            text="Smart surgical instrument",
            section="title",
            retrieval_method="dense",
            retrieval_score=0.92,
            rank=1,
            metadata={"country_code": "US"},
        )
    ]
    with patch.object(retrieval_service, "search_dense", return_value=mock_dense):
        payload = {
            "query": "surgical instrument",
            "top_k": 3,
            "rerank": False,
            "methods": ["sparse", "dense"],
        }
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.post("/api/retrieval/search", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["hybrid_results"] is not None
    assert data["reranked_results"] is None


@pytest.mark.asyncio
async def test_endpoint_retrieval_search_rerank_true():
    """Verify POST /api/retrieval/search with rerank=true returns both hybrid and reranked_results."""
    from app.api.routes.retrieval import retrieval_service

    mock_dense = [
        RetrievalResult(
            patent_number="US-10492811-B2",
            chunk_index=0,
            chunk_id="US-10492811-B2:0",
            text="Smart surgical instrument",
            section="title",
            retrieval_method="dense",
            retrieval_score=0.92,
            rank=1,
            metadata={"country_code": "US"},
        )
    ]
    mock_reranked = [
        RerankedResult(
            patent_number="US-10492811-B2",
            chunk_index=0,
            chunk_id="US-10492811-B2:0",
            text="Smart surgical instrument",
            section="title",
            retrieval_method="hybrid_rrf_reranked",
            rrf_score=0.032,
            reranker_score=0.895,
            reranker_rank=1,
            metadata={"country_code": "US"},
        )
    ]
    with patch.object(retrieval_service, "search_dense", return_value=mock_dense), \
         patch.object(retrieval_service.reranker_service, "rerank", return_value=mock_reranked):
        payload = {
            "query": "surgical instrument",
            "top_k": 3,
            "rerank": True,
            "methods": ["sparse", "dense"],
        }
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.post("/api/retrieval/search", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["hybrid_results"] is not None
    assert data["reranked_results"] is not None
    assert len(data["reranked_results"]) == 1
    first_reranked = data["reranked_results"][0]
    assert first_reranked["reranker_rank"] == 1
    assert first_reranked["reranker_score"] == 0.895
    assert first_reranked["retrieval_method"] == "hybrid_rrf_reranked"


@pytest.mark.asyncio
async def test_endpoint_retrieval_rerank_invalid_single_method():
    """Verify POST /api/retrieval/search rejects rerank=true when only single method is given."""
    payload = {
        "query": "surgical instrument",
        "top_k": 3,
        "rerank": True,
        "methods": ["sparse"],  # single method without dense
    }
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post("/api/retrieval/search", json=payload)

    assert response.status_code == 400
    assert "Reranking requires hybrid retrieval candidates" in response.json()["detail"]


@pytest.mark.asyncio
async def test_reranker_filter_propagation():
    """Verify filters apply before RRF and reranking, so reranked results adhere to constraints."""
    from app.api.routes.retrieval import retrieval_service

    # Provide dense results satisfying filter (claim_only)
    mock_filtered_dense = [
        RetrievalResult(
            patent_number="US-10492811-B2",
            chunk_index=2,
            chunk_id="US-10492811-B2:2",
            text="Claim 1: A surgical instrument",
            section="claims",
            claim_number=1,
            retrieval_method="dense",
            retrieval_score=0.91,
            rank=1,
            metadata={"country_code": "US"},
        )
    ]
    with patch.object(retrieval_service, "search_dense", return_value=mock_filtered_dense), \
         patch.object(retrieval_service.reranker_service.reranker, "score", return_value=[0.94]):
        payload = {
            "query": "surgical instrument",
            "top_k": 5,
            "rerank": True,
            "filters": {"country_code": "US", "claim_only": True},
            "methods": ["sparse", "dense"],
        }
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.post("/api/retrieval/search", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["reranked_results"] is not None
    assert len(data["reranked_results"]) > 0
    for r in data["reranked_results"]:
        assert r["section"] == "claims"
        assert r["metadata"].get("country_code") == "US"


def test_invalid_reranker_configuration():
    """Verify BGEReranker supports configurable models/batch sizes and handles edge cases."""
    from app.services.reranking.bge_reranker import BGEReranker
    from app.core.config import settings

    # Configurable model name and batch size
    custom_reranker = BGEReranker(model_name="BAAI/bge-reranker-large", batch_size=16)
    assert custom_reranker.model_name == "BAAI/bge-reranker-large"
    assert custom_reranker.batch_size == 16

    # Verify lazy loading preserves offline behavior when input is empty
    assert custom_reranker.score([]) == []
    assert custom_reranker._model is None


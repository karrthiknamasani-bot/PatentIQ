import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.services.retrieval.types import (
    RetrievalResult,
    SearchRequest,
    RetrievalFilters,
)
from app.services.retrieval.rrf_fusion import ReciprocalRankFusion
from app.services.retrieval.retrieval_service import PatentRetrievalService


def make_sample_result(
    patent_number: str,
    chunk_index: int,
    rank: int,
    score: float,
    method: str = "sparse_bm25",
    text: str = "Sample patent text passage.",
    section: str = "claims",
    claim_number: int = 1,
    metadata: Optional[Dict[str, Any]] = None,
) -> RetrievalResult:
    meta = metadata or {"title": f"Patent Title {patent_number}", "country_code": "US"}
    return RetrievalResult(
        patent_number=patent_number,
        chunk_index=chunk_index,
        chunk_id=f"{patent_number}:{chunk_index}",
        text=text,
        section=section,
        claim_number=claim_number,
        page_number=1,
        paragraph_id=f"claim:{claim_number}",
        retrieval_method=method,
        retrieval_score=score,
        rank=rank,
        metadata=meta,
    )


def test_rrf_mathematical_exact_calculation_and_tie_breaking():
    """Verify exact formula 1/(k + rank) calculation and deterministic tie-breaking.

    For k=60:
    Candidate A: Sparse rank 1, Dense rank 2 -> 1/61 + 1/62 = 0.01639344 + 0.01612903 = 0.03252247
    Candidate B: Sparse rank 2, Dense rank 1 -> 1/62 + 1/61 = 0.03252247 (exact mathematical tie)
    Tie breaker: patent_number ascending decides rank 1 and 2.
    """
    rrf = ReciprocalRankFusion(k=60)

    sp_a = make_sample_result("US-A", 0, rank=1, score=15.0, method="sparse_bm25")
    sp_b = make_sample_result("US-B", 0, rank=2, score=12.0, method="sparse_bm25")

    dn_b = make_sample_result("US-B", 0, rank=1, score=0.91, method="dense")
    dn_a = make_sample_result("US-A", 0, rank=2, score=0.88, method="dense")

    fused = rrf.fuse(sparse_results=[sp_a, sp_b], dense_results=[dn_b, dn_a])

    assert len(fused) == 2
    expected_score = round(1.0 / 61.0 + 1.0 / 62.0, 6)
    assert fused[0].rrf_score == expected_score
    assert fused[1].rrf_score == expected_score

    # Deterministic tie-breaker: "US-A" comes before "US-B"
    assert fused[0].patent_number == "US-A"
    assert fused[0].final_rank == 1
    assert fused[1].patent_number == "US-B"
    assert fused[1].final_rank == 2


def test_rrf_missing_rank_handling():
    """Verify that candidates appearing in only one list receive 0 contribution from the absent method."""
    rrf = ReciprocalRankFusion(k=60)

    # Cand 1: in both (Sparse 1, Dense 2) -> 1/61 + 1/62 = 0.032522
    # Cand 2: Sparse only (Sparse 2)      -> 1/62 = 0.016129
    # Cand 3: Dense only (Dense 1)       -> 1/61 = 0.016393
    c1_sp = make_sample_result("US-001", 0, rank=1, score=10.0, method="sparse_bm25")
    c2_sp = make_sample_result("US-002", 0, rank=2, score=8.0, method="sparse_bm25")
    c1_dn = make_sample_result("US-001", 0, rank=2, score=0.85, method="dense")
    c3_dn = make_sample_result("US-003", 0, rank=1, score=0.92, method="dense")

    fused = rrf.fuse(sparse_results=[c1_sp, c2_sp], dense_results=[c3_dn, c1_dn])

    assert len(fused) == 3

    # Rank 1: C1 (in both)
    assert fused[0].patent_number == "US-001"
    assert fused[0].sparse_rank == 1
    assert fused[0].dense_rank == 2
    assert fused[0].sparse_score == 10.0
    assert fused[0].dense_score == 0.85
    assert "sparse_bm25" in fused[0].fusion_methods
    assert "dense" in fused[0].fusion_methods

    # Rank 2: C3 (Dense rank 1 -> 1/61 > 1/62)
    assert fused[1].patent_number == "US-003"
    assert fused[1].sparse_rank is None
    assert fused[1].dense_rank == 1
    assert fused[1].sparse_score is None
    assert fused[1].dense_score == 0.92
    assert fused[1].fusion_methods == ["dense"]

    # Rank 3: C2 (Sparse rank 2 -> 1/62)
    assert fused[2].patent_number == "US-002"
    assert fused[2].sparse_rank == 2
    assert fused[2].dense_rank is None
    assert fused[2].sparse_score == 8.0
    assert fused[2].dense_score is None
    assert fused[2].fusion_methods == ["sparse_bm25"]


def test_rrf_duplicate_deduplication():
    """Verify that duplicate candidate occurrences within the same retrieval method are deduplicated."""
    rrf = ReciprocalRankFusion(k=60)

    # US-DUP appears twice in sparse list at rank 1 and rank 3
    sp1 = make_sample_result("US-DUP", 0, rank=1, score=20.0, method="sparse_bm25")
    sp2 = make_sample_result("US-OTHER", 0, rank=2, score=15.0, method="sparse_bm25")
    sp3 = make_sample_result("US-DUP", 0, rank=3, score=10.0, method="sparse_bm25")  # Duplicate

    fused = rrf.fuse(sparse_results=[sp1, sp2, sp3], dense_results=[])

    assert len(fused) == 2
    dup_cand = next(c for c in fused if c.patent_number == "US-DUP")
    assert dup_cand.sparse_rank == 1
    # Score should only be 1/61, NOT 1/61 + 1/63
    assert dup_cand.rrf_score == round(1.0 / 61.0, 6)


def test_rrf_top_k_truncation():
    """Verify that top_k cutoff truncates the output while maintaining correct sequential final_ranks."""
    rrf = ReciprocalRankFusion(k=60)

    sparse_list = [
        make_sample_result(f"US-00{i}", 0, rank=i, score=100.0 - i, method="sparse_bm25")
        for i in range(1, 10)
    ]
    fused = rrf.fuse(sparse_results=sparse_list, dense_results=[], top_k=3)

    assert len(fused) == 3
    assert [c.final_rank for c in fused] == [1, 2, 3]
    assert fused[0].patent_number == "US-001"
    assert fused[1].patent_number == "US-002"
    assert fused[2].patent_number == "US-003"


def test_rrf_metadata_preservation():
    """Verify original text, section, claim_number, and metadata are intact in RRFResult."""
    rrf = ReciprocalRankFusion(k=60)

    item = make_sample_result(
        "US-9999",
        2,
        rank=1,
        score=9.5,
        text="Unique technical apparatus claim.",
        section="claims",
        claim_number=3,
    )
    fused = rrf.fuse(sparse_results=[item], dense_results=[])

    assert len(fused) == 1
    res = fused[0]
    assert res.text == "Unique technical apparatus claim."
    assert res.section == "claims"
    assert res.claim_number == 3
    assert res.chunk_index == 2
    assert res.metadata["country_code"] == "US"
    assert res.retrieval_method == "hybrid_rrf"


def test_service_search_hybrid():
    """Verify search_hybrid executes sparse and dense retrieval and fuses via RRF."""
    from unittest.mock import MagicMock

    mock_bm25 = MagicMock()
    mock_bm25.search.return_value = [
        make_sample_result("US-1", 0, rank=1, score=15.0, method="sparse_bm25"),
        make_sample_result("US-2", 0, rank=2, score=10.0, method="sparse_bm25"),
    ]

    mock_dense = MagicMock()
    mock_dense.search.return_value = [
        make_sample_result("US-2", 0, rank=1, score=0.95, method="dense"),
        make_sample_result("US-3", 0, rank=2, score=0.85, method="dense"),
    ]

    service = PatentRetrievalService(bm25_retriever=mock_bm25, dense_retriever=mock_dense)
    service._is_sparse_indexed = True
    service._is_dense_indexed = True

    results = service.search_hybrid(query="surgical telemetry", top_k=2)

    assert len(results) == 2
    # US-2 appears in both (BM25 rank 2, Dense rank 1) -> 1/62 + 1/61 -> highest RRF score
    assert results[0].patent_number == "US-2"
    assert results[0].final_rank == 1
    assert results[0].sparse_rank == 2
    assert results[0].dense_rank == 1
    assert results[0].retrieval_method == "hybrid_rrf"


@pytest.mark.asyncio
async def test_endpoint_retrieval_search_hybrid_response():
    """Verify POST /api/retrieval/search with methods=['sparse', 'dense'] returns hybrid_results."""
    from unittest.mock import patch
    from app.api.routes.retrieval import retrieval_service

    mock_dense_results = [
        make_sample_result("US-10492811-B2", 0, rank=1, score=0.92, method="dense", metadata={"country_code": "US"}),
        make_sample_result("US-10772694-B2", 1, rank=2, score=0.88, method="dense", metadata={"country_code": "US"}),
    ]
    with patch.object(retrieval_service, "search_dense", return_value=mock_dense_results):
        payload = {
            "query": "surgical instrument sensor telemetry",
            "top_k": 3,
            "methods": ["sparse", "dense"],
        }
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.post("/api/retrieval/search", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == payload["query"]
    assert "sparse_results" in data
    assert "dense_results" in data
    assert "hybrid_results" in data
    assert data["hybrid_results"] is not None
    assert len(data["hybrid_results"]) > 0

    first_hybrid = data["hybrid_results"][0]
    assert first_hybrid["final_rank"] == 1
    assert "rrf_score" in first_hybrid
    assert first_hybrid["retrieval_method"] == "hybrid_rrf"
    assert "patent_number" in first_hybrid
    assert "chunk_index" in first_hybrid


@pytest.mark.asyncio
async def test_endpoint_retrieval_passes_filters_to_both_methods():
    """Verify filters are respected across hybrid retrieval."""
    from unittest.mock import patch
    from app.api.routes.retrieval import retrieval_service

    mock_filtered_dense = [
        make_sample_result(
            "US-10492811-B2", 5, rank=1, score=0.91,
            method="dense", section="claims", claim_number=1,
            metadata={"country_code": "US"},
        ),
    ]
    with patch.object(retrieval_service, "search_dense", return_value=mock_filtered_dense):
        payload = {
            "query": "surgical",
            "top_k": 5,
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
    assert data["hybrid_results"] is not None
    assert len(data["hybrid_results"]) > 0
    for item in data["hybrid_results"]:
        assert item["section"] == "claims"
        assert item["metadata"].get("country_code") == "US"

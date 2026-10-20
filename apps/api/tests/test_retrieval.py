import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.schemas.patent import PatentChunkCreate
from app.services.retrieval.types import (
    SearchRequest,
    RetrievalFilters,
    RetrievalResult,
)
from app.services.retrieval.bm25_retriever import BM25Retriever
from app.services.retrieval.embedding_provider import MockEmbeddingProvider
from app.services.retrieval.qdrant_store import QdrantVectorStore, generate_point_id
from app.services.retrieval.dense_retriever import DenseRetriever
from app.services.retrieval.metadata_filter import MetadataFilterMatcher
from app.services.retrieval.retrieval_service import PatentRetrievalService


@pytest.fixture
def sample_test_chunks():
    """Generates a diverse set of synthetic prior-art chunks for offline testing."""
    return [
        PatentChunkCreate(
            patent_number="US-10001",
            chunk_index=0,
            section="claims",
            claim_number=1,
            paragraph_id="claim:1",
            text="Claim 1: A surgical stapling instrument with an articulation joint and optical impedance sensors.",
            metadata={
                "country_code": "US",
                "cpc_classes": ["A61B 17/00"],
                "ipc_classes": ["A61B"],
                "publication_date": "2020-01-15",
                "language": "en",
            },
        ),
        PatentChunkCreate(
            patent_number="US-10001",
            chunk_index=1,
            section="abstract",
            claim_number=None,
            paragraph_id="para:1",
            text="A smart surgical instrument monitoring tissue telemetry dynamically to adjust motor torque.",
            metadata={
                "country_code": "US",
                "cpc_classes": ["A61B 17/00"],
                "ipc_classes": ["A61B"],
                "publication_date": "2020-01-15",
                "language": "en",
            },
        ),
        PatentChunkCreate(
            patent_number="US-10002",
            chunk_index=0,
            section="claims",
            claim_number=1,
            paragraph_id="claim:1",
            text="Claim 1: A neural network system for graph reasoning and multi-hop entity traversal.",
            metadata={
                "country_code": "US",
                "cpc_classes": ["G06N 3/08"],
                "ipc_classes": ["G06F"],
                "publication_date": "2021-06-20",
                "language": "en",
            },
        ),
        PatentChunkCreate(
            patent_number="EP-20001",
            chunk_index=0,
            section="abstract",
            claim_number=None,
            paragraph_id="para:1",
            text="A European patent disclosure regarding hybrid rotor balancing and piezoelectric dampers.",
            metadata={
                "country_code": "EP",
                "cpc_classes": ["F01D 5/02"],
                "ipc_classes": ["F01D"],
                "publication_date": "2019-11-10",
                "language": "en",
            },
        ),
    ]


def test_bm25_indexing_and_lexical_search(sample_test_chunks):
    """Verify BM25 index creation and ranked lexical retrieval."""
    retriever = BM25Retriever(k1=1.5, b=0.75)
    indexed_count = retriever.index_chunks(sample_test_chunks)
    assert indexed_count == 4

    # Search for surgical instrument
    results = retriever.search("surgical instrument torque", top_k=2)
    assert len(results) > 0
    assert results[0].retrieval_method == "sparse_bm25"
    assert results[0].patent_number == "US-10001"
    assert results[0].rank == 1
    assert results[0].retrieval_score > 0.0


def test_bm25_metadata_filtering(sample_test_chunks):
    """Verify BM25 search adheres to country, claim-only, and section filters."""
    retriever = BM25Retriever()
    retriever.index_chunks(sample_test_chunks)

    # Filter by EP country code
    results_ep = retriever.search("patent", top_k=5, filters=RetrievalFilters(country_code="EP"))
    assert len(results_ep) == 1
    assert results_ep[0].patent_number == "EP-20001"

    # Filter claim_only
    results_claims = retriever.search("instrument", top_k=5, filters=RetrievalFilters(claim_only=True))
    assert all(r.section == "claims" for r in results_claims)
    assert all(r.claim_number is not None for r in results_claims)


def test_deterministic_point_id_generation():
    """Verify point ID is deterministic and stable across calls."""
    id1 = generate_point_id("US-10492811-B2", 3)
    id2 = generate_point_id("US-10492811-B2", 3)
    id_diff = generate_point_id("US-10492811-B2", 4)

    assert id1 == id2
    assert id1 != id_diff
    # Valid UUID format
    assert len(id1) == 36


def test_mock_embedding_provider():
    """Verify mock embedding provider generates normalized embeddings of requested dimension."""
    provider = MockEmbeddingProvider(dimension=768)
    assert provider.dimension == 768

    vec = provider.embed_text("Test query text")
    assert len(vec) == 768

    # L2-norm should be approximately 1.0
    norm = sum(x * x for x in vec) ** 0.5
    assert pytest.approx(norm, 0.01) == 1.0


def test_dense_retrieval_with_in_memory_qdrant(sample_test_chunks):
    """Verify DenseRetriever indexes and retrieves vectors using in-memory Qdrant store."""
    from qdrant_client import QdrantClient

    in_memory_client = QdrantClient(location=":memory:")
    mock_provider = MockEmbeddingProvider(dimension=64)
    qdrant_store = QdrantVectorStore(
        collection_name="test_collection",
        client=in_memory_client,
    )

    retriever = DenseRetriever(
        embedding_provider=mock_provider,
        vector_store=qdrant_store,
    )

    indexed = retriever.index_chunks(sample_test_chunks)
    assert indexed == 4

    # Idempotent upsert verification (upsert again should not double count)
    reindexed = retriever.index_chunks(sample_test_chunks)
    assert reindexed == 4

    # Query
    results = retriever.search("surgical instrument", top_k=2)
    assert len(results) > 0
    assert results[0].retrieval_method == "dense"
    assert results[0].rank == 1
    assert results[0].chunk_id is not None
    assert results[0].text != ""


def test_dense_retrieval_filters(sample_test_chunks):
    """Verify Qdrant native filtering for country code and section."""
    from qdrant_client import QdrantClient

    in_memory_client = QdrantClient(location=":memory:")
    mock_provider = MockEmbeddingProvider(dimension=64)
    qdrant_store = QdrantVectorStore(
        collection_name="test_filtered_collection",
        client=in_memory_client,
    )

    retriever = DenseRetriever(
        embedding_provider=mock_provider,
        vector_store=qdrant_store,
    )
    retriever.index_chunks(sample_test_chunks)

    # Filter for section="claims"
    claim_results = retriever.search(
        "neural network",
        top_k=5,
        filters=RetrievalFilters(section="claims"),
    )
    assert len(claim_results) > 0
    assert all(r.section == "claims" for r in claim_results)


def test_retrieval_service_independent_modes(sample_test_chunks):
    """Verify PatentRetrievalService supports sparse-only, dense-only, and combined search without fusion."""
    from qdrant_client import QdrantClient

    in_memory_client = QdrantClient(location=":memory:")
    mock_provider = MockEmbeddingProvider(dimension=64)
    qdrant_store = QdrantVectorStore(
        collection_name="test_service_collection",
        client=in_memory_client,
    )

    bm25 = BM25Retriever()
    bm25.index_chunks(sample_test_chunks)

    dense = DenseRetriever(embedding_provider=mock_provider, vector_store=qdrant_store)
    dense.index_chunks(sample_test_chunks)

    service = PatentRetrievalService(bm25_retriever=bm25, dense_retriever=dense)
    service._is_sparse_indexed = True
    service._is_dense_indexed = True

    # 1. Sparse only
    req_sparse = SearchRequest(query="surgical", methods=["sparse"])
    res_sparse = service.search(req_sparse)
    assert res_sparse.sparse_results is not None
    assert res_sparse.dense_results is None

    # 2. Dense only
    req_dense = SearchRequest(query="neural", methods=["dense"])
    res_dense = service.search(req_dense)
    assert res_dense.sparse_results is None
    assert res_dense.dense_results is not None

    # 3. Both methods (distinct pools, NO fusion)
    req_both = SearchRequest(query="telemetry", methods=["sparse", "dense"])
    res_both = service.search(req_both)
    assert res_both.sparse_results is not None
    assert res_both.dense_results is not None


@pytest.mark.asyncio
async def test_endpoint_retrieval_search_sparse():
    """Verify POST /api/retrieval/search returns 200 with sparse results."""
    payload = {
        "query": "surgical instrument sensor telemetry",
        "top_k": 5,
        "methods": ["sparse"],
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
    assert data["dense_results"] is None
    assert len(data["sparse_results"]) > 0
    # Check claim traceability
    first = data["sparse_results"][0]
    assert "patent_number" in first
    assert "retrieval_method" in first
    assert first["retrieval_method"] == "sparse_bm25"


@pytest.mark.asyncio
async def test_endpoint_retrieval_empty_query():
    """Verify POST /api/retrieval/search rejects empty query with 400."""
    payload = {"query": "   ", "methods": ["sparse"]}
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post("/api/retrieval/search", json=payload)

    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]


@pytest.mark.asyncio
async def test_endpoint_retrieval_invalid_method():
    """Verify POST /api/retrieval/search rejects unsupported method with 400."""
    payload = {"query": "valid query", "methods": ["invalid_method"]}
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post("/api/retrieval/search", json=payload)

    assert response.status_code == 400
    assert "valid retrieval method" in response.json()["detail"]


def test_qdrant_auto_collection_creation_and_dense_search(sample_test_chunks):
    """Verify QdrantVectorStore automatically creates collection if missing and executes search without throwing."""
    from qdrant_client import QdrantClient

    client = QdrantClient(location=":memory:")
    mock_provider = MockEmbeddingProvider(dimension=64)
    store = QdrantVectorStore(
        collection_name="test_auto_created_collection",
        client=client,
    )

    # Calling search before collection exists should NOT throw collection not found
    query_vec = mock_provider.embed_text("test query")
    points = store.search(query_vector=query_vec, top_k=5)
    assert points == []

    # DenseRetriever indexing and search
    dense = DenseRetriever(embedding_provider=mock_provider, vector_store=store)
    indexed = dense.index_chunks(sample_test_chunks)
    assert indexed == 4

    results = dense.search("surgical stapling", top_k=2)
    assert len(results) > 0
    assert results[0].retrieval_method == "dense"
    assert results[0].patent_number in ["US-10001", "US-10002", "EP-20001"]

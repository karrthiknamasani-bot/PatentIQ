"""Real local smoke test script for PatentIQ hybrid retrieval foundation (Step 5).

Indexes the 78 canonical patent corpus chunks into:
1. BM25 sparse index
2. Qdrant dense vector store using BAAI/bge-base-en-v1.5 embeddings
Runs test queries, measures latency, and outputs traceable debug results.
"""
import sys
import os
import time

# Add apps/api to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from qdrant_client import QdrantClient
from app.services.retrieval.corpus_loader import RetrievalCorpusLoader
from app.services.retrieval.bm25_retriever import BM25Retriever
from app.services.retrieval.embedding_provider import BGEEmbeddingProvider
from app.services.retrieval.qdrant_store import QdrantVectorStore
from app.services.retrieval.dense_retriever import DenseRetriever
from app.services.retrieval.retrieval_service import PatentRetrievalService
from app.services.retrieval.types import SearchRequest
from app.services.reranking.bge_reranker import BGEReranker
from app.services.reranking.reranking_service import PatentRerankingService


def format_preview(text: str, max_len: int = 75) -> str:
    cleaned = " ".join(text.split())
    return cleaned[:max_len] + "..." if len(cleaned) > max_len else cleaned


def main():
    print("=" * 75)
    print("PATENTIQ RETRIEVAL FOUNDATION — REAL LOCAL SMOKE TEST (STEP 5)")
    print("=" * 75)

    # 1. Load corpus
    chunks_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "corpus", "sample", "sample_chunks.jsonl"))
    print(f"[*] Loading prior-art chunks from: {chunks_path}")
    chunks = RetrievalCorpusLoader.load_chunks(chunks_path)
    print(f"[+] Loaded {len(chunks)} canonical chunks.")

    # 2. Build BM25 index
    t0 = time.perf_counter()
    bm25 = BM25Retriever(k1=1.5, b=0.75)
    bm25_count = bm25.index_chunks(chunks)
    bm25_time = (time.perf_counter() - t0) * 1000
    print(f"[+] BM25 index built with {bm25_count} chunks ({bm25_time:.2f} ms).")

    # 3. Provision Dense BGE Embeddings & In-Memory Qdrant Store
    print("[*] Initializing BGE model ('BAAI/bge-base-en-v1.5')...")
    t0 = time.perf_counter()
    bge_provider = BGEEmbeddingProvider(model_name="BAAI/bge-base-en-v1.5")
    dimension = bge_provider.dimension
    load_time = (time.perf_counter() - t0) * 1000
    print(f"[+] BGE model initialized: dimension={dimension} ({load_time:.2f} ms).")

    print("[*] Provisioning local in-memory Qdrant collection...")
    in_memory_qdrant = QdrantClient(location=":memory:")
    qdrant_store = QdrantVectorStore(
        collection_name="patent_prior_art_smoke",
        client=in_memory_qdrant,
    )
    dense_retriever = DenseRetriever(
        embedding_provider=bge_provider,
        vector_store=qdrant_store,
    )

    t0 = time.perf_counter()
    dense_indexed = dense_retriever.index_chunks(chunks)
    indexing_time = (time.perf_counter() - t0) * 1000
    print(f"[+] Dense vector indexing complete: {dense_indexed} points indexed ({indexing_time:.2f} ms).")

    # 4. Assemble Unified Retrieval & Reranking Service
    print("[*] Initializing BGE Reranker ('BAAI/bge-reranker-base')...")
    reranker = BGEReranker(model_name="BAAI/bge-reranker-base", batch_size=8)
    reranking_service = PatentRerankingService(reranker=reranker)

    service = PatentRetrievalService(
        bm25_retriever=bm25,
        dense_retriever=dense_retriever,
        reranker_service=reranking_service,
    )
    service._is_sparse_indexed = True
    service._is_dense_indexed = True

    # 5. Execute Test Queries
    queries = [
        "system for predicting drug disease relationships using graph neural networks",
        "smart surgical instrument with sensor feedback and adaptive torque motor",
    ]

    for q_idx, query in enumerate(queries, start=1):
        print("\n" + "=" * 75)
        print(f"QUERY {q_idx}: \"{query}\"")
        print("=" * 75)

        t_start = time.perf_counter()
        response = service.search(SearchRequest(query=query, top_k=3, rerank=True, methods=["sparse", "dense"]))
        total_latency = (time.perf_counter() - t_start) * 1000

        print(f"Total Latency: {total_latency:.2f} ms | Sparse Hits: {response.total_sparse_hits} | Dense Hits: {response.total_dense_hits} | Reranked: {response.total_reranked_hits}")

        # Display Sparse Results
        print("\n[BM25 TOP RESULTS]")
        if response.sparse_results:
            for r in response.sparse_results:
                claim_info = f"Claim {r.claim_number}" if r.claim_number else "N/A"
                print(f"  Rank {r.rank:2d} | Score: {r.retrieval_score:6.3f} | {r.patent_number:15s} | {r.section:12s} | {claim_info:8s} | {format_preview(r.text)}")
        else:
            print("  (No exact lexical match)")

        # Display Dense Results
        print("\n[DENSE BGE TOP RESULTS]")
        if response.dense_results:
            for r in response.dense_results:
                claim_info = f"Claim {r.claim_number}" if r.claim_number else "N/A"
                print(f"  Rank {r.rank:2d} | Score: {r.retrieval_score:6.3f} | {r.patent_number:15s} | {r.section:12s} | {claim_info:8s} | {format_preview(r.text)}")

        # Display Hybrid RRF Results
        print("\n[RRF TOP RESULTS (k=60)]")
        if response.hybrid_results:
            for r in response.hybrid_results:
                claim_info = f"Claim {r.claim_number}" if r.claim_number else "N/A"
                sp_rank = f"BM25 #{r.sparse_rank}" if r.sparse_rank else "BM25 N/A"
                dn_rank = f"Dense #{r.dense_rank}" if r.dense_rank else "Dense N/A"
                print(f"  Rank {r.final_rank:2d} | RRF Score: {r.rrf_score:.6f} | {r.patent_number:15s} | {r.section:12s} | {claim_info:8s} | {sp_rank:9s} | {dn_rank:9s} | {format_preview(r.text)}")
        else:
            print("  (No hybrid fusion results)")

        # Display Reranked Results
        print("\n[RERANKED TOP RESULTS (BGE Cross-Encoder)]")
        if response.reranked_results:
            for r in response.reranked_results:
                claim_info = f"Claim {r.claim_number}" if r.claim_number else "N/A"
                print(f"  Rank {r.reranker_rank:2d} | Reranker Score: {r.reranker_score:8.4f} | RRF Score: {r.rrf_score:.6f} | {r.patent_number:15s} | {r.section:12s} | {claim_info:8s} | {format_preview(r.text)}")
        else:
            print("  (No reranked results)")

    print("\n" + "=" * 75)
    print("SMOKE TEST SUMMARY:")
    print(f"  - BM25 Chunks:         {bm25_count}")
    print(f"  - Dense Points:        {dense_indexed}")
    print(f"  - Vector Dimension:    {dimension}")
    print(f"  - Embedding Model:     {bge_provider.model_name}")
    print(f"  - Reranker Model:      {reranker.model_name}")
    print(f"  - Reranker Batch Size: {reranker.batch_size}")
    print(f"  - Pipeline Stage:      BM25 + BGE Dense -> RRF (k=60) -> BGE Cross-Encoder")
    print("=" * 75)


if __name__ == "__main__":
    main()

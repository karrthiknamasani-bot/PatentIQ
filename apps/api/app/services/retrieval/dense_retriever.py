from typing import List, Optional
from app.schemas.patent import PatentChunkCreate
from app.services.retrieval.types import RetrievalResult, RetrievalFilters
from app.services.retrieval.embedding_provider import EmbeddingProviderBase, BGEEmbeddingProvider
from app.services.retrieval.qdrant_store import QdrantVectorStore
from app.services.retrieval.metadata_filter import MetadataFilterMatcher


class DenseRetriever:
    """Dense semantic retriever encoding queries into BGE embeddings

    and performing approximate nearest neighbor search in Qdrant.
    """

    def __init__(
        self,
        embedding_provider: Optional[EmbeddingProviderBase] = None,
        vector_store: Optional[QdrantVectorStore] = None,
    ):
        self.embedding_provider = embedding_provider or BGEEmbeddingProvider()
        self.vector_store = vector_store or QdrantVectorStore()

    def index_chunks(self, chunks: List[PatentChunkCreate], batch_size: int = 32) -> int:
        """Embeds and indexes chunks into the Qdrant vector store."""
        if not chunks:
            return 0

        dim = self.embedding_provider.dimension
        self.vector_store.ensure_collection(dimension=dim)

        texts = [c.text for c in chunks]
        vectors = self.embedding_provider.embed_texts(texts, batch_size=batch_size)

        return self.vector_store.upsert_chunks(chunks, vectors)

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[RetrievalFilters] = None,
    ) -> List[RetrievalResult]:
        """Encodes query and executes vector similarity search with optional Qdrant filtering."""
        if not query or not query.strip():
            return []

        query_vector = self.embedding_provider.embed_text(query.strip())
        qdrant_filter = MetadataFilterMatcher.build_qdrant_filter(filters)

        points = self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
            query_filter=qdrant_filter,
        )

        results: List[RetrievalResult] = []
        for rank, pt in enumerate(points, start=1):
            payload = pt.payload or {}
            results.append(
                RetrievalResult(
                    patent_number=payload.get("patent_number", "UNKNOWN"),
                    patent_id=payload.get("patent_id"),
                    chunk_id=str(pt.id),
                    chunk_index=payload.get("chunk_index", 0),
                    text=payload.get("text", ""),
                    section=payload.get("section", "description"),
                    claim_number=payload.get("claim_number"),
                    page_number=payload.get("page_number"),
                    paragraph_id=payload.get("paragraph_id"),
                    retrieval_method="dense",
                    retrieval_score=round(float(pt.score), 4),
                    rank=rank,
                    metadata=payload,
                )
            )

        return results

import logging
import threading
import uuid
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.schemas.patent import PatentChunkCreate

logger = logging.getLogger("patentiq.qdrant")

# Deterministic namespace UUID for generating Qdrant point IDs
PATENTIQ_NAMESPACE = uuid.UUID("a7b3c2d1-e4f5-4a6b-8c9d-0e1f2a3b4c5d")


def generate_point_id(patent_number: str, chunk_index: int) -> str:
    """Generates a stable, reproducible UUIDv5 for a patent chunk in Qdrant.

    Derived deterministically from patent_number + chunk_index.
    """
    key = f"{patent_number.strip().upper()}:{chunk_index}"
    return str(uuid.uuid5(PATENTIQ_NAMESPACE, key))


class QdrantVectorStore:
    """Manages collection provisioning, vector indexing, and similarity searches

    in Qdrant (supporting both local in-memory and networked server instances).
    """

    _shared_in_memory_client: Optional[Any] = None
    _client_lock: threading.Lock = threading.Lock()

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: Optional[str] = None,
        client: Optional[Any] = None,
    ):
        self.url = url or settings.QDRANT_URL
        self.api_key = api_key or settings.QDRANT_API_KEY
        self.collection_name = collection_name or settings.QDRANT_COLLECTION
        self._client = client
        self._collection_ensured: bool = False

    def get_client(self) -> Any:
        """Retrieves or lazily initializes the QdrantClient instance."""
        if self._client is not None:
            return self._client

        import os
        from qdrant_client import QdrantClient

        # Check if on-disk embedded storage path is configured and exists
        storage_path = getattr(settings, "QDRANT_STORAGE_PATH", None)
        if storage_path:
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
            abs_storage_path = os.path.abspath(os.path.join(repo_root, storage_path) if not os.path.isabs(storage_path) else storage_path)
            if os.path.exists(abs_storage_path):
                with QdrantVectorStore._client_lock:
                    if QdrantVectorStore._shared_in_memory_client is None:
                        QdrantVectorStore._shared_in_memory_client = QdrantClient(path=abs_storage_path)
                    self._client = QdrantVectorStore._shared_in_memory_client
                    return self._client

        if not self.url or self.url == ":memory:":
            with QdrantVectorStore._client_lock:
                if QdrantVectorStore._shared_in_memory_client is None:
                    QdrantVectorStore._shared_in_memory_client = QdrantClient(location=":memory:")
                self._client = QdrantVectorStore._shared_in_memory_client
        else:
            try:
                # Test connection with short timeout or fallback to in-memory if server unavailable in dev
                candidate = QdrantClient(url=self.url, api_key=self.api_key, timeout=1.0)
                candidate.get_collections()
                self._client = candidate
            except Exception:
                with QdrantVectorStore._client_lock:
                    if QdrantVectorStore._shared_in_memory_client is None:
                        QdrantVectorStore._shared_in_memory_client = QdrantClient(location=":memory:")
                    self._client = QdrantVectorStore._shared_in_memory_client

        return self._client

    def ensure_collection(self, dimension: int) -> bool:
        """Creates the Qdrant collection configured with COSINE distance and the exact vector dimension

        if it does not already exist.
        """
        if getattr(self, "_collection_ensured", False):
            return False

        client = self.get_client()
        from qdrant_client.http import models

        try:
            collections = client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
        except Exception:
            exists = False

        if not exists:
            try:
                client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=dimension,
                        distance=models.Distance.COSINE,
                    ),
                )
                self._collection_ensured = True
                return True
            except Exception as exc:
                logger.warning("Failed to create collection %s: %s", self.collection_name, exc)
                return False
        self._collection_ensured = True
        return False

    def upsert_chunks(
        self,
        chunks: List[PatentChunkCreate],
        vectors: List[List[float]],
    ) -> int:
        """Idempotently upserts chunk vectors and traceability payloads into Qdrant.

        Uses deterministic UUIDs derived from patent_number + chunk_index.
        """
        if not chunks or not vectors or len(chunks) != len(vectors):
            return 0

        client = self.get_client()
        from qdrant_client.http import models

        points = []
        for chunk, vector in zip(chunks, vectors):
            point_id = generate_point_id(chunk.patent_number, chunk.chunk_index)
            meta = chunk.metadata or {}

            # Construct comprehensive traceability payload
            payload: Dict[str, Any] = {
                "patent_number": chunk.patent_number,
                "patent_id": chunk.patent_id,
                "chunk_index": chunk.chunk_index,
                "section": chunk.section,
                "claim_number": chunk.claim_number,
                "page_number": chunk.page_number,
                "paragraph_id": chunk.paragraph_id,
                "text": chunk.text,
                "title": meta.get("title", ""),
                "assignee": meta.get("assignee", ""),
                "publication_date": meta.get("publication_date"),
                "country_code": meta.get("country_code", "US"),
                "language": meta.get("language", "en"),
                "ipc_classes": meta.get("ipc_classes", []),
                "cpc_classes": meta.get("cpc_classes", []),
                "source": meta.get("source", "custom"),
            }

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            )

        # Batch upsert
        client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )
        return len(points)

    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        query_filter: Optional[Any] = None,
    ) -> List[Any]:
        """Executes vector search against the Qdrant collection."""
        if not query_vector:
            return []
        self.ensure_collection(dimension=len(query_vector))
        client = self.get_client()
        try:
            if hasattr(client, "query_points"):
                res = client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    query_filter=query_filter,
                    limit=top_k,
                    with_payload=True,
                )
                return res.points
            return client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
            )
        except Exception as exc:
            logger.warning("Qdrant search failed gracefully: %s", exc)
            return []

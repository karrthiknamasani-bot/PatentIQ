import threading
from abc import ABC, abstractmethod
from typing import List, Optional
from app.core.config import settings


class EmbeddingProviderBase(ABC):
    """Abstract interface for dense representation encoders."""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Encodes a single text string into a dense vector."""
        pass

    @abstractmethod
    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Encodes a batch of texts into dense vectors."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Returns the dimensionality of the generated vector embeddings."""
        pass


class BGEEmbeddingProvider(EmbeddingProviderBase):
    """Dense embedding encoder using BAAI's BGE (Beijing Academy of Artificial Intelligence) models.

    Models:
        - BAAI/bge-base-en-v1.5 (dim=768) [Default]
        - BAAI/bge-large-en-v1.5 (dim=1024)

    Features:
        - Thread-safe lazy loading on first inference request.
        - Process-level singleton reuse to avoid repeated memory allocations.
        - Strict L2-normalization for cosine distance metrics in Qdrant.
    """

    _lock = threading.Lock()
    _shared_model = None
    _shared_model_name = None

    # Known dimensions for standard BGE models to avoid premature model loading
    _KNOWN_DIMENSIONS = {
        "BAAI/bge-base-en-v1.5": 768,
        "BAAI/bge-large-en-v1.5": 1024,
        "bge-base-en-v1.5": 768,
        "bge-large-en-v1.5": 1024,
    }

    def __init__(
        self,
        model_name: Optional[str] = None,
        normalize_embeddings: Optional[bool] = None,
    ):
        self.model_name = model_name or settings.BGE_MODEL_NAME
        self.normalize_embeddings = (
            normalize_embeddings if normalize_embeddings is not None else settings.BGE_NORMALIZE_EMBEDDINGS
        )
        self._dimension: Optional[int] = self._KNOWN_DIMENSIONS.get(self.model_name)

    def _ensure_model_loaded(self):
        """Loads SentenceTransformer model lazily if not already in memory."""
        if BGEEmbeddingProvider._shared_model is not None and BGEEmbeddingProvider._shared_model_name == self.model_name:
            return BGEEmbeddingProvider._shared_model

        with BGEEmbeddingProvider._lock:
            if BGEEmbeddingProvider._shared_model is not None and BGEEmbeddingProvider._shared_model_name == self.model_name:
                return BGEEmbeddingProvider._shared_model

            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(self.model_name)
            BGEEmbeddingProvider._shared_model = model
            BGEEmbeddingProvider._shared_model_name = self.model_name
            get_dim_fn = getattr(model, "get_embedding_dimension", getattr(model, "get_sentence_embedding_dimension", None))
            self._dimension = get_dim_fn() if get_dim_fn else 768
            return model

    @property
    def dimension(self) -> int:
        """Returns embedding vector dimension."""
        if self._dimension is not None:
            return self._dimension
        model = self._ensure_model_loaded()
        get_dim_fn = getattr(model, "get_embedding_dimension", getattr(model, "get_sentence_embedding_dimension", None))
        self._dimension = get_dim_fn() if get_dim_fn else 768
        return self._dimension

    def embed_text(self, text: str) -> List[float]:
        """Encodes single text into normalized dense vector."""
        model = self._ensure_model_loaded()
        vec = model.encode(
            text,
            normalize_embeddings=self.normalize_embeddings,
            show_progress_bar=False,
        )
        return vec.tolist()

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Encodes multiple texts in batches."""
        if not texts:
            return []
        model = self._ensure_model_loaded()
        vecs = model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=self.normalize_embeddings,
            show_progress_bar=False,
        )
        return vecs.tolist()


class MockEmbeddingProvider(EmbeddingProviderBase):
    """Deterministic, zero-dependency mock embedding provider for tests and offline CI."""

    def __init__(self, dimension: int = 768):
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> List[float]:
        # Generates deterministic vector derived from hash of text
        import hashlib
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vec = [float(h[i % len(h)]) / 255.0 for i in range(self._dimension)]
        # Normalize
        norm = sum(x * x for x in vec) ** 0.5 or 1.0
        return [x / norm for x in vec]

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]

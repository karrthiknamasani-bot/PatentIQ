import logging
import threading
from typing import List, Tuple, Optional, Any
from app.core.config import settings
from app.services.reranking.types import BaseReranker

logger = logging.getLogger("patentiq.reranking")


class BGEReranker(BaseReranker):
    """BGE Cross-Encoder reranker utilizing sentence-transformers CrossEncoder.

    Features:
    - Thread-safe lazy model loading
    - Process-level model caching
    - Batched pairwise inference (query, candidate_text)
    - Raw un-normalized relevance scores preservation
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        batch_size: Optional[int] = None,
    ):
        self._model_name = model_name or settings.RERANKER_MODEL_NAME
        self._batch_size = batch_size or settings.RERANKER_BATCH_SIZE
        self._model: Optional[Any] = None
        self._lock = threading.Lock()

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def batch_size(self) -> int:
        return self._batch_size

    def _get_model(self) -> Any:
        """Lazily initializes the CrossEncoder instance in a thread-safe manner."""
        if self._model is None:
            with self._lock:
                if self._model is None:
                    logger.info("Lazy-loading CrossEncoder reranker model: %s", self._model_name)
                    from sentence_transformers import CrossEncoder
                    self._model = CrossEncoder(
                        self._model_name,
                        activation_fn=None,  # Keep raw logits/relevance score
                    )
                    logger.info("CrossEncoder model %s loaded successfully.", self._model_name)
        return self._model

    def score(
        self,
        pairs: List[Tuple[str, str]],
        batch_size: Optional[int] = None,
    ) -> List[float]:
        """Calculates pairwise relevance scores for (query, passage) tuples.

        Args:
            pairs: List of (query, candidate_text) tuples.
            batch_size: Batch size for model inference.

        Returns:
            List of raw float relevance scores.
        """
        if not pairs:
            return []

        effective_batch_size = batch_size or self._batch_size
        model = self._get_model()

        logger.debug(
            "Scoring %d pairs with %s (batch_size=%d)",
            len(pairs),
            self._model_name,
            effective_batch_size,
        )

        predictions = model.predict(
            pairs,
            batch_size=effective_batch_size,
            show_progress_bar=False,
        )

        # Convert numpy floats / arrays to standard python float list
        if hasattr(predictions, "tolist"):
            return [float(x) for x in predictions.tolist()]
        return [float(x) for x in predictions]

import re
import math
import logging
from abc import ABC, abstractmethod
from typing import List, Tuple, Set, Optional, Dict

from app.core.config import settings
from app.services.features.feature_schema import TechnicalFeature
from app.services.reranking.types import RerankedResult
from app.services.retrieval.embedding_provider import EmbeddingProviderBase, BGEEmbeddingProvider

logger = logging.getLogger("patentiq.mapping")

# Standard conservative stop-words to exclude from lexical comparison
STOP_WORDS: Set[str] = {
    "a", "an", "the", "and", "or", "of", "to", "in", "for", "with", "on", "at",
    "by", "from", "up", "about", "into", "over", "after", "is", "are", "was",
    "were", "be", "been", "being", "have", "has", "had", "having", "do", "does",
    "did", "doing", "that", "this", "these", "those", "it", "its", "as", "such",
}


class MatchResult:
    """Individual similarity metrics between a feature and an evidence passage."""
    __slots__ = ("lexical_similarity", "semantic_similarity", "matching_score")

    def __init__(self, lexical_similarity: float, semantic_similarity: float, matching_score: float):
        self.lexical_similarity = lexical_similarity
        self.semantic_similarity = semantic_similarity
        self.matching_score = matching_score


class BaseFeatureEvidenceMatcher(ABC):
    """Abstract interface for measuring technical similarity between features and evidence."""

    @abstractmethod
    def match(
        self,
        feature: TechnicalFeature,
        evidence: RerankedResult,
        lexical_weight: float = 0.4,
        semantic_weight: float = 0.6,
    ) -> MatchResult:
        """Computes lexical, semantic, and combined matching score."""
        ...


class FeatureEvidenceMatcher(BaseFeatureEvidenceMatcher):
    """Deterministic feature-to-evidence matcher combining token Jaccard and BGE dense similarity.

    Features:
    - Conservative tokenization preserving numbers, technical hyphenations, and units.
    - Token-level Jaccard similarity.
    - Dense cosine semantic similarity via BGE embedding provider.
    - Embedding vector caching per mapping session to avoid repeated neural inference.
    - Strict validation of alpha/beta weights (alpha + beta == 1.0).
    """

    _TOKEN_RE = re.compile(r"[a-zA-Z0-9]+(?:[\.\-_][a-zA-Z0-9]+)*")

    def __init__(self, embedding_provider: Optional[EmbeddingProviderBase] = None):
        self._embedding_provider = embedding_provider
        self._vector_cache: Dict[str, List[float]] = {}

    def get_embedding_provider(self) -> Optional[EmbeddingProviderBase]:
        """Lazily provisions BGEEmbeddingProvider if not supplied."""
        if self._embedding_provider is None:
            try:
                self._embedding_provider = BGEEmbeddingProvider()
            except Exception as exc:
                logger.warning("Could not initialize BGEEmbeddingProvider for mapping: %s", exc)
                self._embedding_provider = None
        return self._embedding_provider

    @classmethod
    def tokenize(cls, text: str) -> Set[str]:
        """Extracts technical tokens (length >= 2, non-stopwords)."""
        if not text:
            return set()
        tokens = cls._TOKEN_RE.findall(text.lower())
        return {t for t in tokens if len(t) >= 2 and t not in STOP_WORDS}

    @classmethod
    def compute_lexical_similarity(cls, feature_text: str, evidence_text: str) -> float:
        """Computes token Jaccard similarity: |T(F) ∩ T(E)| / |T(F) ∪ T(E)|.

        Returns float in [0.0, 1.0].
        """
        tokens_f = cls.tokenize(feature_text)
        tokens_e = cls.tokenize(evidence_text)

        if not tokens_f or not tokens_e:
            return 0.0

        intersection = tokens_f.intersection(tokens_e)
        union = tokens_f.union(tokens_e)

        if not union:
            return 0.0

        return round(len(intersection) / len(union), 4)

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Retrieves cached vector or encodes text via embedding provider."""
        if text in self._vector_cache:
            return self._vector_cache[text]

        provider = self.get_embedding_provider()
        if provider is None:
            return None

        try:
            vec = provider.embed_text(text)
            self._vector_cache[text] = vec
            return vec
        except Exception as exc:
            logger.warning("Embedding generation failed for text snippet: %s", exc)
            return None

    def compute_semantic_similarity(self, feature_text: str, evidence_text: str) -> float:
        """Computes cosine similarity between feature text and evidence passage.

        Since BGE embeddings are strictly L2-normalized, cosine similarity is the dot product.
        Clamped to [0.0, 1.0].
        """
        vec_f = self._get_embedding(feature_text)
        vec_e = self._get_embedding(evidence_text)

        if vec_f is None or vec_e is None:
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec_f, vec_e))
        # Clamp to [0.0, 1.0] (negative cosine indicates antithetical/orthogonal semantics)
        clamped = max(0.0, min(1.0, dot_product))
        return round(clamped, 4)

    def match(
        self,
        feature: TechnicalFeature,
        evidence: RerankedResult,
        lexical_weight: float = 0.4,
        semantic_weight: float = 0.6,
    ) -> MatchResult:
        """Calculates combined matching score from lexical and semantic signals.

        Formula:
            matching_score = alpha * lexical_similarity + beta * semantic_similarity
        """
        if not math.isclose(lexical_weight + semantic_weight, 1.0, rel_tol=1e-3):
            raise ValueError(
                f"lexical_weight ({lexical_weight}) + semantic_weight ({semantic_weight}) must sum to 1.0"
            )

        f_text = feature.normalized_text or feature.feature_text
        e_text = evidence.text

        lex_sim = self.compute_lexical_similarity(f_text, e_text)
        sem_sim = self.compute_semantic_similarity(f_text, e_text)

        combined = (lexical_weight * lex_sim) + (semantic_weight * sem_sim)
        combined_clamped = round(max(0.0, min(1.0, combined)), 4)

        return MatchResult(
            lexical_similarity=lex_sim,
            semantic_similarity=sem_sim,
            matching_score=combined_clamped,
        )

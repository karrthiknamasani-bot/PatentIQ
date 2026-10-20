from typing import Dict, Optional
from app.core.config import settings
from app.services.mapping.types import EvidenceRelationship


class RelationshipClassifier:
    """Deterministic, transparent rule-based classifier for technical evidence relationships.

    Threshold semantics:
    - direct_match: Evidence closely discloses the technical feature (default >= 0.75).
    - partial_match: Meaningful elements of the feature are represented (default >= 0.50).
    - contextual_match: Provides technically relevant context/background (default >= 0.30).
    - weak_match: Limited technical correspondence (default >= 0.15).
    - no_material_match: Insufficient correspondence (< 0.15).

    IMPORTANT: A direct_match indicates high technical correspondence; it is NOT
    a legal finding of lack of novelty or unpatentability.
    """

    def __init__(
        self,
        direct_threshold: Optional[float] = None,
        partial_threshold: Optional[float] = None,
        contextual_threshold: Optional[float] = None,
        weak_threshold: Optional[float] = None,
    ):
        self.direct_threshold = direct_threshold if direct_threshold is not None else settings.DIRECT_MATCH_THRESHOLD
        self.partial_threshold = partial_threshold if partial_threshold is not None else settings.PARTIAL_MATCH_THRESHOLD
        self.contextual_threshold = contextual_threshold if contextual_threshold is not None else settings.CONTEXTUAL_MATCH_THRESHOLD
        self.weak_threshold = weak_threshold if weak_threshold is not None else settings.WEAK_MATCH_THRESHOLD

        # Validate monotonic threshold ordering
        if not (self.direct_threshold > self.partial_threshold > self.contextual_threshold > self.weak_threshold >= 0.0):
            raise ValueError(
                f"Thresholds must be strictly descending: direct ({self.direct_threshold}) > "
                f"partial ({self.partial_threshold}) > contextual ({self.contextual_threshold}) > "
                f"weak ({self.weak_threshold}) >= 0.0"
            )

    def get_threshold_config(self) -> Dict[str, float]:
        """Returns the active threshold configuration dictionary."""
        return {
            "direct_match_threshold": self.direct_threshold,
            "partial_match_threshold": self.partial_threshold,
            "contextual_match_threshold": self.contextual_threshold,
            "weak_match_threshold": self.weak_threshold,
        }

    def classify(
        self,
        matching_score: float,
        lexical_similarity: float = 0.0,
        semantic_similarity: float = 0.0,
    ) -> EvidenceRelationship:
        """Classifies the technical relationship between an invention feature and evidence passage.

        Rules are evaluated in order of strictness:
        1. direct_match: matching_score >= direct_threshold OR (semantic >= 0.85 and lexical >= 0.40)
        2. partial_match: matching_score >= partial_threshold OR lexical >= 0.50
        3. contextual_match: matching_score >= contextual_threshold
        4. weak_match: matching_score >= weak_threshold
        5. no_material_match: otherwise
        """
        # 1. Direct match check
        if matching_score >= self.direct_threshold or (semantic_similarity >= 0.85 and lexical_similarity >= 0.40):
            return EvidenceRelationship.DIRECT_MATCH

        # 2. Partial match check
        if matching_score >= self.partial_threshold or lexical_similarity >= 0.50:
            return EvidenceRelationship.PARTIAL_MATCH

        # 3. Contextual match check
        if matching_score >= self.contextual_threshold:
            return EvidenceRelationship.CONTEXTUAL_MATCH

        # 4. Weak match check
        if matching_score >= self.weak_threshold:
            return EvidenceRelationship.WEAK_MATCH

        # 5. No material match
        return EvidenceRelationship.NO_MATERIAL_MATCH

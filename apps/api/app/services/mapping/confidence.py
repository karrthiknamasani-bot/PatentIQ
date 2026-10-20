from typing import Optional
from app.services.mapping.types import EvidenceRelationship


def calculate_mapping_confidence(
    matching_score: float,
    relationship: EvidenceRelationship,
    lexical_similarity: float,
    semantic_similarity: float,
    reranker_rank: Optional[int] = None,
    feature_confidence: float = 1.0,
) -> float:
    """Calculates a deterministic mapping confidence score in [0.0, 1.0].

    SEMANTICS:
    Represents certainty in the correspondence quality between feature and evidence.
    It is NOT:
    - Patentability confidence
    - Novelty score
    - Legal validity
    - Infringement probability

    FORMULA:
    Base = (0.60 * matching_score) + (0.20 * feature_confidence)
    Relationship weight:
      - direct_match:      +0.15
      - partial_match:     +0.10
      - contextual_match:  +0.05
      - weak_match:        +0.00
      - no_material_match: -0.10
    Signal agreement:
      - |semantic - lexical| <= 0.20: +0.05
      - |semantic - lexical| >= 0.50: -0.05
    Reranker top alignment:
      - reranker_rank <= 3: +0.05
    Clamped strictly to [0.0, 1.0].
    """
    base = (0.60 * matching_score) + (0.20 * feature_confidence)

    # Relationship contribution
    if relationship == EvidenceRelationship.DIRECT_MATCH:
        rel_boost = 0.15
    elif relationship == EvidenceRelationship.PARTIAL_MATCH:
        rel_boost = 0.10
    elif relationship == EvidenceRelationship.CONTEXTUAL_MATCH:
        rel_boost = 0.05
    elif relationship == EvidenceRelationship.WEAK_MATCH:
        rel_boost = 0.00
    else:
        rel_boost = -0.10

    # Cross-signal agreement contribution
    diff = abs(semantic_similarity - lexical_similarity)
    if diff <= 0.20 and (semantic_similarity > 0.0 or lexical_similarity > 0.0):
        agreement_boost = 0.05
    elif diff >= 0.50:
        agreement_boost = -0.05
    else:
        agreement_boost = 0.00

    # Upstream reranker top tier contribution
    reranker_boost = 0.05 if (reranker_rank is not None and reranker_rank <= 3) else 0.00

    raw_confidence = base + rel_boost + agreement_boost + reranker_boost
    return round(max(0.0, min(1.0, raw_confidence)), 4)

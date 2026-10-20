import hashlib
import logging
from collections import Counter
from typing import List, Optional, Dict, Set

from app.core.config import settings
from app.services.features.feature_schema import TechnicalFeature
from app.services.reranking.types import RerankedResult
from app.services.mapping.types import (
    EvidenceRelationship,
    FeatureEvidenceMapping,
    MappingMetadata,
    FeatureEvidenceMappingResponse,
)
from app.services.mapping.feature_evidence_matcher import (
    BaseFeatureEvidenceMatcher,
    FeatureEvidenceMatcher,
)
from app.services.mapping.relationship_classifier import RelationshipClassifier
from app.services.mapping.confidence import calculate_mapping_confidence

logger = logging.getLogger("patentiq.mapping")


class PatentMappingService:
    """Orchestrator for connecting extracted technical features to prior-art evidence.

    Responsibilities:
    - Pairwise similarity evaluation (token Jaccard + BGE dense cosine).
    - Deterministic relationship classification (direct, partial, contextual, weak, no_material).
    - Deterministic confidence computation.
    - Top-k candidate filtering per technical feature.
    - Duplicate prevention per (feature, evidence) pair.
    - Content-addressed mapping ID generation and full upstream signal preservation.
    """

    def __init__(
        self,
        matcher: Optional[BaseFeatureEvidenceMatcher] = None,
        classifier: Optional[RelationshipClassifier] = None,
    ):
        self.matcher = matcher or FeatureEvidenceMatcher()
        self.classifier = classifier or RelationshipClassifier()

    @classmethod
    def generate_mapping_id(
        cls,
        project_id: str,
        feature_id: str,
        patent_number: str,
        chunk_index: int,
    ) -> str:
        """Generates a stable, content-addressed mapping ID.

        Format: map_{sha256[:14]}
        Guarantees: Same project + same feature + same evidence chunk -> exact same ID.
        """
        raw_key = f"{project_id.strip()}::{feature_id.strip()}::{patent_number.strip()}#{chunk_index}"
        digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:14]
        return f"map_{digest}"

    def map_features_to_evidence(
        self,
        project_id: str,
        features: List[TechnicalFeature],
        evidence: List[RerankedResult],
        top_k: Optional[int] = None,
        lexical_weight: Optional[float] = None,
        semantic_weight: Optional[float] = None,
    ) -> FeatureEvidenceMappingResponse:
        """Executes feature-to-evidence matching across all features and evidence passages."""
        if not project_id or not project_id.strip():
            raise ValueError("project_id must be a non-empty string.")

        if not features:
            raise ValueError("At least one TechnicalFeature must be provided for mapping.")

        if not evidence:
            raise ValueError("At least one RerankedResult evidence candidate must be provided for mapping.")

        effective_top_k = top_k if top_k is not None else settings.MAPPING_TOP_K
        lw = lexical_weight if lexical_weight is not None else settings.MAPPING_LEXICAL_WEIGHT
        sw = semantic_weight if semantic_weight is not None else settings.MAPPING_SEMANTIC_WEIGHT

        selected_mappings: List[FeatureEvidenceMapping] = []
        relationship_counts = Counter()

        for feat in features:
            feature_candidates: List[FeatureEvidenceMapping] = []
            seen_evidence_keys: Set[str] = set()

            for ev in evidence:
                evidence_key = f"{ev.patent_number}#{ev.chunk_index}"
                if evidence_key in seen_evidence_keys:
                    continue
                seen_evidence_keys.add(evidence_key)

                # 1. Similarity computation
                match_res = self.matcher.match(
                    feature=feat,
                    evidence=ev,
                    lexical_weight=lw,
                    semantic_weight=sw,
                )

                # 2. Relationship classification
                rel = self.classifier.classify(
                    matching_score=match_res.matching_score,
                    lexical_similarity=match_res.lexical_similarity,
                    semantic_similarity=match_res.semantic_similarity,
                )

                # 3. Confidence calculation
                conf = calculate_mapping_confidence(
                    matching_score=match_res.matching_score,
                    relationship=rel,
                    lexical_similarity=match_res.lexical_similarity,
                    semantic_similarity=match_res.semantic_similarity,
                    reranker_rank=ev.reranker_rank,
                    feature_confidence=feat.confidence,
                )

                # 4. Deterministic mapping ID
                map_id = self.generate_mapping_id(
                    project_id=project_id,
                    feature_id=feat.feature_id,
                    patent_number=ev.patent_number,
                    chunk_index=ev.chunk_index,
                )

                mapping_obj = FeatureEvidenceMapping(
                    mapping_id=map_id,
                    project_id=project_id,
                    feature_id=feat.feature_id,
                    feature_type=feat.feature_type.value if hasattr(feat.feature_type, "value") else str(feat.feature_type),
                    feature_text=feat.feature_text,
                    normalized_text=feat.normalized_text,
                    patent_number=ev.patent_number,
                    patent_id=ev.patent_id,
                    chunk_id=ev.chunk_id,
                    chunk_index=ev.chunk_index,
                    evidence_text=ev.text,
                    section=ev.section,
                    claim_number=ev.claim_number,
                    page_number=ev.page_number,
                    paragraph_id=ev.paragraph_id,
                    title=ev.metadata.get("title") if ev.metadata else None,
                    country_code=ev.metadata.get("country_code", "US") if ev.metadata else "US",
                    publication_date=ev.metadata.get("publication_date") if ev.metadata else None,
                    ipc_classes=ev.metadata.get("ipc_classes", []) if ev.metadata else [],
                    cpc_classes=ev.metadata.get("cpc_classes", []) if ev.metadata else [],
                    source=ev.source,
                    retrieval_method=ev.retrieval_method,
                    sparse_rank=ev.sparse_rank,
                    dense_rank=ev.dense_rank,
                    sparse_score=ev.sparse_score,
                    dense_score=ev.dense_score,
                    rrf_score=ev.rrf_score,
                    reranker_score=ev.reranker_score,
                    reranker_rank=ev.reranker_rank,
                    fusion_methods=ev.fusion_methods,
                    lexical_similarity=match_res.lexical_similarity,
                    semantic_similarity=match_res.semantic_similarity,
                    matching_score=match_res.matching_score,
                    evidence_relationship=rel,
                    mapping_confidence=conf,
                )
                feature_candidates.append(mapping_obj)

            # Sort candidate mappings for this feature:
            # 1. matching_score descending
            # 2. mapping_confidence descending
            # 3. patent_number ascending
            # 4. chunk_index ascending
            feature_candidates.sort(
                key=lambda m: (
                    -m.matching_score,
                    -m.mapping_confidence,
                    m.patent_number,
                    m.chunk_index,
                )
            )

            # Retain top-k evidence mappings for this feature
            top_for_feature = feature_candidates[:effective_top_k]
            selected_mappings.extend(top_for_feature)

            for m in top_for_feature:
                relationship_counts[m.evidence_relationship.value] += 1

        # Summary averages
        avg_score = (
            round(sum(m.matching_score for m in selected_mappings) / len(selected_mappings), 4)
            if selected_mappings else 0.0
        )
        avg_conf = (
            round(sum(m.mapping_confidence for m in selected_mappings) / len(selected_mappings), 4)
            if selected_mappings else 0.0
        )

        metadata = MappingMetadata(
            number_of_features=len(features),
            number_of_evidence_candidates=len(evidence),
            number_of_mappings=len(selected_mappings),
            relationship_distribution=dict(relationship_counts),
            average_matching_score=avg_score,
            average_mapping_confidence=avg_conf,
            mapping_top_k=effective_top_k,
            lexical_weight=lw,
            semantic_weight=sw,
            threshold_configuration=self.classifier.get_threshold_config(),
            mapping_method="hybrid_lexical_semantic",
        )

        return FeatureEvidenceMappingResponse(
            project_id=project_id,
            mappings=selected_mappings,
            total_mappings=len(selected_mappings),
            mapping_metadata=metadata,
        )


# Global singleton instance for FastAPI dependency injection
patent_mapping_service = PatentMappingService()

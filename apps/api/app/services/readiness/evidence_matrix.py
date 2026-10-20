from typing import List, Dict, Set
from app.services.features.feature_schema import TechnicalFeature
from app.services.mapping.types import FeatureEvidenceMapping
from app.services.readiness.types import EvidenceMatrix, EvidenceMatrixCell


def build_evidence_matrix(
    project_id: str,
    features: List[TechnicalFeature],
    mappings: List[FeatureEvidenceMapping],
) -> EvidenceMatrix:
    """Construct a structured Evidence Matrix from features and evidence mappings.
    
    Preserves all feature-evidence correspondences, upstream retrieval signals,
    and calculates matrix-level distribution metrics.
    """
    cells: List[EvidenceMatrixCell] = []
    distinct_patents: Set[str] = set()
    relationship_dist: Dict[str, int] = {
        "direct_match": 0,
        "partial_match": 0,
        "contextual_match": 0,
        "weak_match": 0,
        "no_material_match": 0,
    }

    # Build matrix cells from mapping entries
    for mapping in mappings:
        rel_val = mapping.evidence_relationship.value if hasattr(mapping.evidence_relationship, "value") else str(mapping.evidence_relationship)
        relationship_dist[rel_val] = relationship_dist.get(rel_val, 0) + 1
        distinct_patents.add(mapping.patent_number)

        cell = EvidenceMatrixCell(
            cell_id=f"cell_{mapping.mapping_id}",
            mapping_id=mapping.mapping_id,
            feature_id=mapping.feature_id,
            feature_type=mapping.feature_type,
            feature_text=mapping.feature_text,
            patent_number=mapping.patent_number,
            patent_id=mapping.patent_id,
            chunk_id=mapping.chunk_id,
            chunk_index=mapping.chunk_index,
            evidence_text=mapping.evidence_text,
            relationship=mapping.evidence_relationship,
            matching_score=round(float(mapping.matching_score), 4),
            mapping_confidence=round(float(mapping.mapping_confidence), 4),
            reranker_score=round(float(mapping.reranker_score), 4) if mapping.reranker_score is not None else None,
            reranker_rank=mapping.reranker_rank,
            section=mapping.section,
            claim_number=mapping.claim_number,
            page_number=mapping.page_number,
            source=mapping.source,
        )
        cells.append(cell)

    return EvidenceMatrix(
        project_id=project_id,
        cells=cells,
        feature_count=len(features),
        patent_count=len(distinct_patents),
        evidence_count=len(cells),
        relationship_distribution=relationship_dist,
    )

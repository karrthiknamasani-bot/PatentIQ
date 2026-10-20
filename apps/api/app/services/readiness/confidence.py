from typing import List, Dict, Set, Tuple
from app.services.features.feature_schema import TechnicalFeature
from app.services.mapping.types import FeatureEvidenceMapping
from app.services.readiness.types import DimensionScore


def evaluate_assessment_confidence(
    features: List[TechnicalFeature],
    mappings: List[FeatureEvidenceMapping],
    dimension_scores: Dict[str, DimensionScore],
) -> Tuple[float, List[str]]:
    """Compute overall assessment confidence and aggregate uncertainty flags.
    
    Assessment confidence measures evidence adequacy, documentation integrity,
    and signal stability. It is strictly NOT a probability of patent grant.
    """
    flags: Set[str] = set()

    # Collect flags already raised by individual dimensions
    for ds in dimension_scores.values():
        flags.update(ds.uncertainty_flags)

    # 1. Feature Volume & Documentation Quality Checks
    num_features = len(features)
    if num_features < 3:
        flags.add("limited_documentation")

    # Provenance completeness check
    features_with_prov = sum(
        1 for f in features if getattr(f, "supporting_sources", None) and len(f.supporting_sources) > 0
    )
    prov_ratio = (features_with_prov / num_features) if num_features > 0 else 0.0
    if prov_ratio < 0.60:
        flags.add("incomplete_feature_provenance")

    # 2. Prior Art Coverage Checks
    mapped_feature_ids = {m.feature_id for m in mappings}
    coverage_ratio = (len(mapped_feature_ids.intersection(f.feature_id for f in features)) / num_features) if num_features > 0 else 0.0

    if coverage_ratio < 0.50:
        flags.add("insufficient_prior_art_coverage")

    # 3. Evidence Quality & Mapping Confidence
    if mappings:
        avg_map_conf = sum(m.mapping_confidence for m in mappings) / len(mappings)
        if avg_map_conf < 0.35:
            flags.add("weak_evidence_support")
    else:
        avg_map_conf = 0.0
        flags.add("insufficient_prior_art_coverage")
        flags.add("weak_evidence_support")

    # 4. Composite Confidence Calculation
    # Factors:
    # - Coverage ratio: 0.35
    # - Average mapping confidence: 0.30
    # - Provenance ratio: 0.20
    # - Documentation breadth: 0.15
    doc_breadth = min(1.0, num_features / 5.0)

    raw_conf = (
        (coverage_ratio * 0.35)
        + (avg_map_conf * 0.30)
        + (prov_ratio * 0.20)
        + (doc_breadth * 0.15)
    )

    # Penalty per major uncertainty flag
    penalty = len(flags) * 0.05
    final_conf = max(0.15, min(0.95, raw_conf - penalty))

    sorted_flags = sorted(list(flags))
    return round(final_conf, 4), sorted_flags

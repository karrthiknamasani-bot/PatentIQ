from typing import List, Dict, Tuple, Set
from collections import defaultdict
from app.services.features.feature_schema import TechnicalFeature, FeatureType
from app.services.mapping.types import FeatureEvidenceMapping, EvidenceRelationship
from app.services.readiness.types import DimensionScore


RELATIONSHIP_SEVERITY = {
    EvidenceRelationship.DIRECT_MATCH: 4,
    EvidenceRelationship.PARTIAL_MATCH: 3,
    EvidenceRelationship.CONTEXTUAL_MATCH: 2,
    EvidenceRelationship.WEAK_MATCH: 1,
    EvidenceRelationship.NO_MATERIAL_MATCH: 0,
}


def score_novelty_dimension(
    features: List[TechnicalFeature],
    mappings: List[FeatureEvidenceMapping],
) -> DimensionScore:
    """Calculate evidence-derived novelty indication heuristic.
    
    Novelty decreases when strong direct/partial prior-art evidence covers invention features.
    Absence of retrieved prior art is NOT treated as proof of novelty; it triggers uncertainty.
    """
    if not features:
        return DimensionScore(
            dimension_name="novelty",
            score=0.50,
            supporting_feature_ids=[],
            supporting_mapping_ids=[],
            rationale="No features provided to evaluate novelty indication.",
            confidence=0.10,
            uncertainty_flags=["insufficient_prior_art_coverage"],
        )

    # Group mappings by feature
    feature_mappings = defaultdict(list)
    for m in mappings:
        feature_mappings[m.feature_id].append(m)

    feature_novelty_scores: List[float] = []
    direct_count = 0
    partial_count = 0
    contextual_count = 0
    unevidenced_count = 0
    supporting_feature_ids = [f.feature_id for f in features]
    supporting_mapping_ids: List[str] = []
    uncertainty_flags: List[str] = []

    for f in features:
        f_maps = feature_mappings.get(f.feature_id, [])
        if not f_maps:
            # Feature has no prior art candidates in candidate pool
            # Do NOT award 1.0; anchor conservatively to reflect unsearched prior art space
            unevidenced_count += 1
            feature_novelty_scores.append(0.60)
            continue

        # Sort by relationship severity (highest first), then confidence descending
        sorted_maps = sorted(
            f_maps,
            key=lambda m: (RELATIONSHIP_SEVERITY.get(m.evidence_relationship, 0), m.mapping_confidence),
            reverse=True,
        )
        strongest = sorted_maps[0]
        supporting_mapping_ids.append(strongest.mapping_id)

        rel = strongest.evidence_relationship
        conf = strongest.mapping_confidence

        if rel == EvidenceRelationship.DIRECT_MATCH:
            direct_count += 1
            # Severe novelty reduction: range [0.05, 0.25]
            f_score = max(0.05, 1.0 - (0.75 * conf + 0.20))
        elif rel == EvidenceRelationship.PARTIAL_MATCH:
            partial_count += 1
            # Moderate novelty reduction: range [0.35, 0.65]
            f_score = max(0.20, 1.0 - (0.60 * conf))
        elif rel == EvidenceRelationship.CONTEXTUAL_MATCH:
            contextual_count += 1
            # Minor novelty reduction: range [0.65, 0.85]
            f_score = max(0.50, 1.0 - (0.35 * conf))
        elif rel == EvidenceRelationship.WEAK_MATCH:
            # Minimal reduction
            f_score = max(0.80, 1.0 - (0.15 * conf))
        else:
            f_score = 0.90

        feature_novelty_scores.append(f_score)

    avg_score = sum(feature_novelty_scores) / len(feature_novelty_scores)
    
    # Confidence derivation
    eval_coverage = (len(features) - unevidenced_count) / len(features)
    if unevidenced_count > 0:
        uncertainty_flags.append("insufficient_prior_art_coverage")
    if direct_count > 0:
        uncertainty_flags.append("direct_prior_art_overlap")

    confidence = round(max(0.20, min(0.95, eval_coverage * 0.85 + (0.10 if direct_count > 0 else 0.0))), 4)
    
    rationale = (
        f"Novelty indication computed across {len(features)} features: "
        f"{direct_count} direct matches, {partial_count} partial matches, "
        f"{contextual_count} contextual matches, and {unevidenced_count} unevidenced in candidate pool. "
        "Score reflects evidence-derived technical divergence (NOT a legal patentability finding)."
    )

    return DimensionScore(
        dimension_name="novelty",
        score=round(avg_score, 4),
        supporting_feature_ids=supporting_feature_ids,
        supporting_mapping_ids=supporting_mapping_ids,
        rationale=rationale,
        confidence=confidence,
        uncertainty_flags=uncertainty_flags,
    )


def score_prior_art_overlap_dimension(
    features: List[TechnicalFeature],
    mappings: List[FeatureEvidenceMapping],
) -> DimensionScore:
    """Calculate prior-art overlap dimension.
    
    Measures the degree to which invention features are directly or partially
    anticipated by the retrieved prior-art evidence. Higher score = higher overlap.
    """
    if not features:
        return DimensionScore(
            dimension_name="prior_art_overlap",
            score=0.0,
            supporting_feature_ids=[],
            supporting_mapping_ids=[],
            rationale="No features available to evaluate prior art overlap.",
            confidence=0.10,
            uncertainty_flags=["insufficient_prior_art_coverage"],
        )

    feature_mappings = defaultdict(list)
    for m in mappings:
        feature_mappings[m.feature_id].append(m)

    overlap_scores: List[float] = []
    supporting_mapping_ids: List[str] = []
    supporting_feature_ids = [f.feature_id for f in features]
    uncertainty_flags: List[str] = []

    direct_count = 0
    partial_count = 0
    contextual_count = 0
    weak_count = 0

    for f in features:
        f_maps = feature_mappings.get(f.feature_id, [])
        if not f_maps:
            overlap_scores.append(0.0)
            continue

        sorted_maps = sorted(
            f_maps,
            key=lambda m: (RELATIONSHIP_SEVERITY.get(m.evidence_relationship, 0), m.mapping_confidence),
            reverse=True,
        )
        strongest = sorted_maps[0]

        rel = strongest.evidence_relationship
        conf = strongest.mapping_confidence

        if rel == EvidenceRelationship.DIRECT_MATCH:
            f_overlap = 0.80 + (0.20 * conf)
            direct_count += 1
            supporting_mapping_ids.append(strongest.mapping_id)
        elif rel == EvidenceRelationship.PARTIAL_MATCH:
            f_overlap = 0.50 + (0.30 * conf)
            partial_count += 1
            supporting_mapping_ids.append(strongest.mapping_id)
        elif rel == EvidenceRelationship.CONTEXTUAL_MATCH:
            # Contextual match provides background technical relevance, NOT material overlap
            f_overlap = 0.0
            contextual_count += 1
        elif rel == EvidenceRelationship.WEAK_MATCH:
            # Weak match: limited technical correspondence, NOT material overlap
            f_overlap = 0.0
            weak_count += 1
        else:
            f_overlap = 0.0

        overlap_scores.append(min(1.0, f_overlap))

    avg_overlap = sum(overlap_scores) / len(overlap_scores)
    if not mappings:
        uncertainty_flags.append("insufficient_prior_art_coverage")

    confidence = round(0.85 if mappings else 0.20, 4)
    rationale = (
        f"Prior-art overlap computed across {len(features)} features against {len(mappings)} candidate mappings: "
        f"{direct_count} direct overlap, {partial_count} partial overlap. "
        f"{contextual_count} contextual and {weak_count} weak matches retained in Evidence Matrix for background traceability only."
    )

    return DimensionScore(
        dimension_name="prior_art_overlap",
        score=round(avg_overlap, 4),
        supporting_feature_ids=supporting_feature_ids,
        supporting_mapping_ids=supporting_mapping_ids,
        rationale=rationale,
        confidence=confidence,
        uncertainty_flags=uncertainty_flags,
    )


def score_technical_differentiation_dimension(
    features: List[TechnicalFeature],
    mappings: List[FeatureEvidenceMapping],
) -> DimensionScore:
    """Calculate technical differentiation dimension.
    
    Evaluates the proportion and technical significance of features that remain
    distinct, weakly represented, or unaddressed by retrieved prior-art evidence.
    """
    if not features:
        return DimensionScore(
            dimension_name="technical_differentiation",
            score=0.50,
            supporting_feature_ids=[],
            supporting_mapping_ids=[],
            rationale="No features available to evaluate technical differentiation.",
            confidence=0.10,
            uncertainty_flags=["insufficient_prior_art_coverage"],
        )

    feature_mappings = defaultdict(list)
    for m in mappings:
        feature_mappings[m.feature_id].append(m)

    diff_scores: List[float] = []
    differentiated_feature_ids: List[str] = []
    supporting_mapping_ids: List[str] = []
    uncertainty_flags: List[str] = []

    # High-value inventive feature types
    inventive_types = {"mechanism", "constraint", "function", "claimed_aspect"}

    for f in features:
        f_maps = feature_mappings.get(f.feature_id, [])
        type_str = f.feature_type.value if hasattr(f.feature_type, "value") else str(f.feature_type)
        is_inventive = type_str in inventive_types

        if not f_maps:
            # Unrepresented feature
            diff_scores.append(0.80 if is_inventive else 0.70)
            differentiated_feature_ids.append(f.feature_id)
            continue

        sorted_maps = sorted(
            f_maps,
            key=lambda m: (RELATIONSHIP_SEVERITY.get(m.evidence_relationship, 0), m.mapping_confidence),
            reverse=True,
        )
        strongest = sorted_maps[0]
        supporting_mapping_ids.append(strongest.mapping_id)

        rel = strongest.evidence_relationship
        conf = strongest.mapping_confidence

        if rel == EvidenceRelationship.DIRECT_MATCH:
            f_diff = max(0.05, 0.20 * (1.0 - conf))
        elif rel == EvidenceRelationship.PARTIAL_MATCH:
            f_diff = 0.35 + (0.25 * (1.0 - conf))
        elif rel == EvidenceRelationship.CONTEXTUAL_MATCH:
            f_diff = 0.65 + (0.15 * (1.0 - conf))
            differentiated_feature_ids.append(f.feature_id)
        elif rel == EvidenceRelationship.WEAK_MATCH:
            f_diff = 0.85
            differentiated_feature_ids.append(f.feature_id)
        else:
            f_diff = 0.95
            differentiated_feature_ids.append(f.feature_id)

        if is_inventive and f_diff >= 0.60:
            f_diff = min(1.0, f_diff * 1.05)

        diff_scores.append(min(1.0, f_diff))

    avg_diff = sum(diff_scores) / len(diff_scores)
    confidence = round(0.80 if mappings else 0.30, 4)
    if not mappings:
        uncertainty_flags.append("insufficient_prior_art_coverage")

    rationale = (
        f"Technical differentiation assessed across {len(features)} features: "
        f"{len(differentiated_feature_ids)} features exhibit distinct or weakly matched profiles against retrieved prior art."
    )

    return DimensionScore(
        dimension_name="technical_differentiation",
        score=round(avg_diff, 4),
        supporting_feature_ids=[f.feature_id for f in features],
        supporting_mapping_ids=supporting_mapping_ids,
        rationale=rationale,
        confidence=confidence,
        uncertainty_flags=uncertainty_flags,
    )


def score_innovation_characteristics_dimension(
    features: List[TechnicalFeature],
) -> DimensionScore:
    """Assess structural and architectural completeness of the invention feature set.
    
    Evaluates diversity across components, functions, mechanisms, relationships,
    technical effects, and constraints. (Engineering heuristic, not complexity bias).
    """
    if not features:
        return DimensionScore(
            dimension_name="innovation_characteristics",
            score=0.10,
            supporting_feature_ids=[],
            supporting_mapping_ids=[],
            rationale="No features extracted to evaluate innovation characteristics.",
            confidence=0.10,
            uncertainty_flags=["limited_documentation"],
        )

    categories_present: Set[str] = set()
    has_mechanism = False
    has_constraint = False
    has_technical_effect = False
    has_relationship = False

    for f in features:
        type_str = f.feature_type.value if hasattr(f.feature_type, "value") else str(f.feature_type)
        categories_present.add(type_str)
        if type_str == "mechanism":
            has_mechanism = True
        elif type_str == "constraint":
            has_constraint = True
        elif type_str == "technical_effect":
            has_technical_effect = True
        elif type_str == "relationship":
            has_relationship = True

    # 1. Category Diversity (max 6 categories -> up to 0.40)
    cat_score = min(0.40, (len(categories_present) / 6.0) * 0.40)

    # 2. Structural Depth / Volume (up to 0.30)
    vol_score = min(0.30, (len(features) / 5.0) * 0.30)

    # 3. Inventive Mechanism & Integration Elements (up to 0.30)
    elem_points = 0.0
    if has_mechanism:
        elem_points += 0.10
    if has_constraint:
        elem_points += 0.08
    if has_technical_effect:
        elem_points += 0.07
    if has_relationship:
        elem_points += 0.05
    elem_score = min(0.30, elem_points)

    total_score = min(1.0, cat_score + vol_score + elem_score)
    uncertainty_flags: List[str] = []
    if len(features) < 3:
        uncertainty_flags.append("limited_documentation")

    rationale = (
        f"Innovation characteristics evaluated across {len(features)} features spanning {len(categories_present)} categories: "
        f"diversity score={cat_score:.2f}, volume score={vol_score:.2f}, integration elements score={elem_score:.2f}."
    )

    return DimensionScore(
        dimension_name="innovation_characteristics",
        score=round(total_score, 4),
        supporting_feature_ids=[f.feature_id for f in features],
        supporting_mapping_ids=[],
        rationale=rationale,
        confidence=0.85,
        uncertainty_flags=uncertainty_flags,
    )


def score_documentation_quality_dimension(
    features: List[TechnicalFeature],
) -> DimensionScore:
    """Measure whether the invention input contains sufficiently structured technical disclosure.
    
    Evaluates provenance completeness, traceable character spans, and technical detail.
    """
    if not features:
        return DimensionScore(
            dimension_name="documentation_quality",
            score=0.10,
            supporting_feature_ids=[],
            supporting_mapping_ids=[],
            rationale="No features extracted to evaluate documentation quality.",
            confidence=0.10,
            uncertainty_flags=["limited_documentation"],
        )

    # 1. Feature Volume Sufficiency (up to 0.25)
    vol_score = min(0.25, (len(features) / 4.0) * 0.25)

    # 2. Provenance Completeness (up to 0.40)
    provenance_count = 0
    span_count = 0
    for f in features:
        sources = getattr(f, "supporting_sources", [])
        if sources:
            provenance_count += 1
            if any(getattr(s, "evidence_span_start", None) is not None for s in sources):
                span_count += 1

    prov_ratio = provenance_count / len(features)
    span_ratio = span_count / len(features)
    prov_score = min(0.40, (prov_ratio * 0.20) + (span_ratio * 0.20))

    # 3. Precision & Constraints Presence (up to 0.35)
    has_constraints = any(
        (f.feature_type.value if hasattr(f.feature_type, "value") else str(f.feature_type)) in {"constraint", "technical_effect"}
        for f in features
    )
    precision_score = 0.35 if has_constraints else 0.15

    total_score = min(1.0, vol_score + prov_score + precision_score)
    uncertainty_flags: List[str] = []
    if prov_ratio < 0.5:
        uncertainty_flags.append("incomplete_feature_provenance")
    if len(features) < 3:
        uncertainty_flags.append("limited_documentation")

    rationale = (
        f"Documentation quality score derived from {len(features)} features: "
        f"provenance completeness={prov_ratio*100:.1f}%, traceable span coverage={span_ratio*100:.1f}%."
    )

    return DimensionScore(
        dimension_name="documentation_quality",
        score=round(total_score, 4),
        supporting_feature_ids=[f.feature_id for f in features],
        supporting_mapping_ids=[],
        rationale=rationale,
        confidence=0.90,
        uncertainty_flags=uncertainty_flags,
    )


def score_commercial_potential_dimension(
    features: List[TechnicalFeature],
) -> DimensionScore:
    """Conservative engineering heuristic assessing explicit technical utility characteristics.
    
    Evaluates problem-solution framing, concrete outputs, and practical constraints.
    (Explicitly disclaims market or financial prediction).
    """
    if not features:
        return DimensionScore(
            dimension_name="commercial_potential",
            score=0.20,
            supporting_feature_ids=[],
            supporting_mapping_ids=[],
            rationale="No features provided; technical utility signals absent.",
            confidence=0.10,
            uncertainty_flags=["commercial_information_missing"],
        )

    categories = set(
        f.feature_type.value if hasattr(f.feature_type, "value") else str(f.feature_type)
        for f in features
    )

    score_acc = 0.0
    has_problem = "problem" in categories
    has_effect_or_output = bool(categories.intersection({"technical_effect", "output"}))
    has_constraint = "constraint" in categories
    has_function_or_process = bool(categories.intersection({"function", "process"}))

    if has_problem:
        score_acc += 0.25
    if has_effect_or_output:
        score_acc += 0.35
    if has_constraint:
        score_acc += 0.25
    if has_function_or_process:
        score_acc += 0.15

    uncertainty_flags: List[str] = []
    if score_acc < 0.30:
        uncertainty_flags.append("commercial_information_missing")

    confidence = round(0.70 if score_acc >= 0.40 else 0.40, 4)
    rationale = (
        f"Technical commercial utility indicators: problem framing={has_problem}, "
        f"technical effect/output={has_effect_or_output}, practical constraints={has_constraint}, "
        f"functional execution={has_function_or_process}. (Engineering heuristic, not market prediction)."
    )

    return DimensionScore(
        dimension_name="commercial_potential",
        score=round(min(1.0, score_acc), 4),
        supporting_feature_ids=[f.feature_id for f in features],
        supporting_mapping_ids=[],
        rationale=rationale,
        confidence=confidence,
        uncertainty_flags=uncertainty_flags,
    )


def score_all_dimensions(
    features: List[TechnicalFeature],
    mappings: List[FeatureEvidenceMapping],
) -> Dict[str, DimensionScore]:
    """Execute scoring across all six EB-PRE dimensions."""
    return {
        "novelty": score_novelty_dimension(features, mappings),
        "prior_art_overlap": score_prior_art_overlap_dimension(features, mappings),
        "technical_differentiation": score_technical_differentiation_dimension(features, mappings),
        "innovation_characteristics": score_innovation_characteristics_dimension(features),
        "documentation_quality": score_documentation_quality_dimension(features),
        "commercial_potential": score_commercial_potential_dimension(features),
    }

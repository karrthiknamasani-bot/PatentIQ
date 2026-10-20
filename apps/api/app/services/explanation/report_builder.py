from typing import List, Dict, Any
from app.services.explanation.types import (
    GroundedContext,
    GroundedExplanation,
    EvidenceBasedReport,
    PriorArtFinding,
    DimensionExplanation,
    EvidenceHighlight,
)

LEGAL_DISCLAIMER = (
    "PatentIQ provides an early-stage evidence-based technical readiness indication. "
    "It does not constitute legal advice or a legal determination of patentability, novelty, "
    "validity, infringement, or freedom to operate. A professional patent search and legal "
    "examination are required for final decisions."
)


def build_fallback_explanation(
    context: GroundedContext,
    reason: str = "LLM provider unconfigured or failed",
) -> GroundedExplanation:
    """Generate a fully deterministic fallback explanation derived strictly from EB-PRE."""
    evidence_ids = [item.evidence_id for item in context.evidence_items]
    primary_eids = evidence_ids[:2] if evidence_ids else []

    prior_art_findings: List[PriorArtFinding] = []
    evidence_highlights: List[EvidenceHighlight] = []

    for item in context.evidence_items[:5]:
        prior_art_findings.append(
            PriorArtFinding(
                statement=f"Prior-art reference {item.patent_number} ({item.section}) discloses technical subject matter with {item.relationship} correspondence.",
                evidence_ids=[item.evidence_id],
            )
        )
        evidence_highlights.append(
            EvidenceHighlight(
                feature_id=item.feature_id,
                patent_number=item.patent_number,
                relationship=item.relationship,
                mapping_confidence=item.mapping_confidence,
                evidence_id=item.evidence_id,
                relevance_explanation=f"Demonstrates {item.relationship} with mapping confidence {item.mapping_confidence:.2f}.",
            )
        )

    dimension_explanations: List[DimensionExplanation] = []
    for dim_name, ds in context.dimension_scores.items():
        dim_eids = primary_eids if dim_name in {"novelty", "prior_art_overlap", "technical_differentiation"} else []
        dimension_explanations.append(
            DimensionExplanation(
                dimension=dim_name,
                score=ds.score,
                explanation=f"Deterministic EB-PRE score: {ds.score:.4f}. Rationale: {ds.rationale}",
                evidence_ids=dim_eids,
            )
        )

    exec_summary = (
        "Grounded explanation is temporarily unavailable. The deterministic EB-PRE assessment and evidence mappings remain available. "
        f"Early-stage patent readiness is evaluated as {context.category_display.upper()} "
        f"with a composite score of {context.readiness_score:.4f} ({context.readiness_percentage:.1f}%) "
        f"and assessment confidence of {context.confidence_score:.4f}."
    )

    diff_text = (
        "Technical differentiation assessed from feature mapping distribution: "
        f"{len(context.features)} features evaluated against {len(context.evidence_items)} prior-art excerpts."
    )

    uncertainty_text = (
        f"Active uncertainty indicators: {', '.join(context.uncertainty_flags) if context.uncertainty_flags else 'None'}. "
        "Score reflects evidence available in candidate corpus only."
    )

    return GroundedExplanation(
        executive_summary=exec_summary,
        invention_summary=f"Invention disclosure in project '{context.project_id}' contains {len(context.features)} extracted technical features.",
        key_technical_features=[f.feature_text for f in context.features],
        prior_art_findings=prior_art_findings,
        dimension_explanations=dimension_explanations,
        differentiation_analysis=diff_text,
        evidence_highlights=evidence_highlights,
        uncertainty_explanation=uncertainty_text,
        limitations=[
            "Deterministic fallback generated without LLM narrative synthesis.",
            "Assessment limited strictly to active development candidate corpus (15 reference patents / 78 chunks).",
            "Absence of direct prior-art overlap within development corpus is not a legal finding of worldwide novelty.",
            "Not a legal patentability, validity, or FTO determination.",
        ],
        conclusion=f"Overall assessment indicates {context.category_display}.",
        evidence_references=evidence_ids,
        readiness_score=context.readiness_score,
        readiness_percentage=context.readiness_percentage,
        readiness_category=context.readiness_category,
        confidence_score=context.confidence_score,
    )


def build_evidence_based_report(
    context: GroundedContext,
    explanation: GroundedExplanation,
    fallback_used: bool = False,
) -> EvidenceBasedReport:
    """Synthesize the final 10-section EvidenceBasedReport."""
    # 1. Technical Feature Analysis
    feat_analysis = []
    for f in context.features:
        type_str = f.feature_type.value if hasattr(f.feature_type, "value") else str(f.feature_type)
        sources = [
            {"chunk_index": s.chunk_index, "section": s.section, "claim": s.claim_number, "page": s.page_number}
            for s in getattr(f, "supporting_sources", [])
        ]
        feat_analysis.append({
            "feature_id": f.feature_id,
            "feature_type": type_str,
            "feature_text": f.feature_text,
            "provenance": sources,
        })

    # 2. Prior-Art Evidence
    prior_art_list = []
    for item in context.evidence_items:
        prior_art_list.append({
            "evidence_id": item.evidence_id,
            "patent_number": item.patent_number,
            "section": item.section,
            "claim_number": item.claim_number,
            "relationship": item.relationship,
            "mapping_confidence": item.mapping_confidence,
            "reranker_rank": item.reranker_rank,
            "text": item.text,
        })

    # 3. Evidence Matrix Summary
    matrix_summary = {
        "total_features": len(context.features),
        "total_evidence_chunks": len(context.evidence_items),
        "distinct_patents": len({item.patent_number for item in context.evidence_items}),
        "relationship_breakdown": {
            rel: sum(1 for item in context.evidence_items if item.relationship == rel)
            for rel in {"direct_match", "partial_match", "contextual_match", "weak_match", "no_material_match"}
        },
    }

    # 4. Dimension Assessments
    dim_assessments = []
    for de in explanation.dimension_explanations:
        orig_ds = context.dimension_scores.get(de.dimension)
        dim_assessments.append({
            "dimension": de.dimension,
            "score": de.score,
            "confidence": orig_ds.confidence if orig_ds else 0.80,
            "explanation": de.explanation,
            "evidence_ids": de.evidence_ids,
        })

    # 5. Uncertainty & Limitations
    uncertainty_dict = {
        "active_flags": context.uncertainty_flags,
        "explanation": explanation.uncertainty_explanation,
        "limitations": explanation.limitations,
    }

    # 6. Overall Readiness
    overall_readiness = {
        "readiness_score": context.readiness_score,
        "readiness_percentage": context.readiness_percentage,
        "readiness_category": context.readiness_category,
        "category_display": context.category_display,
        "confidence_score": context.confidence_score,
        "conclusion": explanation.conclusion,
        "fallback_used": fallback_used,
    }

    return EvidenceBasedReport(
        project_id=context.project_id,
        executive_summary=explanation.executive_summary,
        invention_overview=explanation.invention_summary,
        technical_feature_analysis=feat_analysis,
        prior_art_evidence=prior_art_list,
        evidence_matrix_summary=matrix_summary,
        eb_pre_dimension_assessment=dim_assessments,
        technical_differentiation=explanation.differentiation_analysis,
        uncertainty_and_limitations=uncertainty_dict,
        overall_early_stage_readiness=overall_readiness,
        legal_disclaimer=LEGAL_DISCLAIMER,
    )

import re
from typing import List, Set, Dict, Any
from pydantic import BaseModel, Field
from app.services.explanation.types import GroundedContext, GroundedExplanation


PROHIBITED_LEGAL_TERMS = [
    r"\bguaranteed\s+patentab(le|ility)\b",
    r"\bguaranteed\s+novelty\b",
    r"\blegally\s+novel\b",
    r"\bguaranteed\s+patent\s+grant\b",
    r"\bdefinitely\s+infring(es|ing)\b",
    r"\bguaranteed\s+freedom\s+to\s+operate\b",
    r"\bproves?\s+legal\s+invalidity\b",
    r"\blegally\s+binding\s+patentability\b",
]


class GroundingValidationResult(BaseModel):
    """Telemetry and outcome of the grounding validation inspection."""
    is_valid: bool = Field(..., description="Whether the explanation satisfies all grounding rules")
    errors: List[str] = Field(default_factory=list, description="Specific grounding or integrity failures")
    checked_evidence_ids: List[str] = Field(default_factory=list)
    checked_patent_numbers: List[str] = Field(default_factory=list)


def validate_grounding(
    explanation: GroundedExplanation,
    context: GroundedContext,
) -> GroundingValidationResult:
    """Rigorous verification of evidence grounding, numerical integrity, and legal boundaries."""
    errors: List[str] = []

    valid_evidence_ids: Set[str] = {item.evidence_id for item in context.evidence_items}
    valid_patents: Set[str] = {item.patent_number for item in context.evidence_items}
    patent_to_claims: Dict[str, Set[int]] = {}
    for item in context.evidence_items:
        if item.claim_number is not None:
            patent_to_claims.setdefault(item.patent_number, set()).add(item.claim_number)

    all_cited_eids: Set[str] = set()

    # 1. Validate Evidence References in Prior Art Findings
    for paf in explanation.prior_art_findings:
        for eid in paf.evidence_ids:
            all_cited_eids.add(eid)
            if eid not in valid_evidence_ids:
                errors.append(f"Prior-art finding references unknown evidence ID '{eid}'")

    # 2. Validate Evidence References in Dimension Explanations
    for de in explanation.dimension_explanations:
        for eid in de.evidence_ids:
            all_cited_eids.add(eid)
            if eid not in valid_evidence_ids:
                errors.append(f"Dimension '{de.dimension}' explanation references unknown evidence ID '{eid}'")

    # 3. Validate Evidence Highlights
    checked_patents: Set[str] = set()
    for hl in explanation.evidence_highlights:
        all_cited_eids.add(hl.evidence_id)
        checked_patents.add(hl.patent_number)
        if hl.evidence_id not in valid_evidence_ids:
            errors.append(f"Evidence highlight references unknown evidence ID '{hl.evidence_id}'")
        if hl.patent_number not in valid_patents:
            errors.append(f"Evidence highlight references unknown patent number '{hl.patent_number}'")

    # 4. Validate Top-Level Evidence References
    for eid in explanation.evidence_references:
        all_cited_eids.add(eid)
        if eid not in valid_evidence_ids:
            errors.append(f"Top-level evidence reference contains unknown ID '{eid}'")

    # 5. Validate Numerical Integrity (Strict EB-PRE Match)
    if abs(explanation.readiness_score - context.readiness_score) > 1e-4:
        errors.append(
            f"Readiness score mismatch: explanation={explanation.readiness_score}, EB-PRE={context.readiness_score}"
        )

    if abs(explanation.readiness_percentage - context.readiness_percentage) > 0.05:
        errors.append(
            f"Readiness percentage mismatch: explanation={explanation.readiness_percentage}, EB-PRE={context.readiness_percentage}"
        )

    if explanation.readiness_category.lower() != context.readiness_category.lower():
        errors.append(
            f"Readiness category mismatch: explanation='{explanation.readiness_category}', EB-PRE='{context.readiness_category}'"
        )

    if abs(explanation.confidence_score - context.confidence_score) > 1e-4:
        errors.append(
            f"Assessment confidence mismatch: explanation={explanation.confidence_score}, EB-PRE={context.confidence_score}"
        )

    # 6. Validate Dimension Scores
    exp_dims = {de.dimension: de for de in explanation.dimension_explanations}
    for dim_name, ds in context.dimension_scores.items():
        if dim_name not in exp_dims:
            errors.append(f"Missing explanation for EB-PRE dimension '{dim_name}'")
        else:
            de = exp_dims[dim_name]
            if abs(de.score - ds.score) > 1e-4:
                errors.append(
                    f"Dimension '{dim_name}' score mismatch: explanation={de.score}, EB-PRE={ds.score}"
                )

    # 7. Check for Prohibited Legal Assertions in all text fields
    full_text_corpus = " ".join([
        explanation.executive_summary,
        explanation.invention_summary,
        explanation.differentiation_analysis,
        explanation.uncertainty_explanation,
        explanation.conclusion,
        " ".join(paf.statement for paf in explanation.prior_art_findings),
        " ".join(de.explanation for de in explanation.dimension_explanations),
    ])

    for pat in PROHIBITED_LEGAL_TERMS:
        if re.search(pat, full_text_corpus, re.IGNORECASE):
            errors.append(f"Explanation contains prohibited legal conclusion matching pattern: '{pat}'")

    is_valid = (len(errors) == 0)
    return GroundingValidationResult(
        is_valid=is_valid,
        errors=errors,
        checked_evidence_ids=sorted(list(all_cited_eids)),
        checked_patent_numbers=sorted(list(checked_patents)),
    )

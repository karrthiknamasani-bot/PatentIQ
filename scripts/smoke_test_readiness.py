import sys
import os
from pathlib import Path

# Add apps/api to path so imports work cleanly
API_DIR = Path(__file__).resolve().parent.parent / "apps" / "api"
sys.path.insert(0, str(API_DIR))

from app.services.features.types import FeatureType, SourceProvenance
from app.services.features.feature_schema import TechnicalFeature
from app.services.mapping.types import EvidenceRelationship, FeatureEvidenceMapping
from app.services.readiness.readiness_engine import readiness_engine
from app.services.readiness.types import ReadinessAssessmentResponse


def run_scenario_a():
    """Scenario A: High prior-art overlap (features directly matched by prior art)."""
    print("=" * 80)
    print("SCENARIO A: HIGH PRIOR-ART OVERLAP (STRONG ANTICIPATION / CORRESPONDENCE)")
    print("=" * 80)

    features = [
        TechnicalFeature(
            feature_id="feat_a_sensor",
            project_id="proj_scenario_a",
            feature_type=FeatureType.COMPONENT,
            feature_text="Integrated sensor array monitoring tissue impedance during RF ablation",
            normalized_text="integrated sensor array monitoring tissue impedance during rf ablation",
            supporting_sources=[
                SourceProvenance(chunk_id="chk_a_0", chunk_index=0, section="description", page_number=2, evidence_span_start=10, evidence_span_end=80)
            ],
            confidence=0.95,
        ),
        TechnicalFeature(
            feature_id="feat_a_modulation",
            project_id="proj_scenario_a",
            feature_type=FeatureType.FUNCTION,
            feature_text="Adaptive RF modulation circuit dynamically varying frequency based on tissue feedback",
            normalized_text="adaptive rf modulation circuit dynamically varying frequency based on tissue feedback",
            supporting_sources=[
                SourceProvenance(chunk_id="chk_a_1", chunk_index=1, section="claims", claim_number=1, page_number=4, evidence_span_start=5, evidence_span_end=95)
            ],
            confidence=0.92,
        ),
    ]

    # Strong direct prior art mappings
    mappings = [
        FeatureEvidenceMapping(
            mapping_id="map_a_001",
            project_id="proj_scenario_a",
            feature_id="feat_a_sensor",
            feature_type="component",
            feature_text="Integrated sensor array monitoring tissue impedance during RF ablation",
            patent_number="US-10492811-B2",
            chunk_id="chk_prior_1",
            chunk_index=1,
            evidence_text="Claim 1: A surgical instrument comprising an end effector with an impedance sensor array configured to monitor tissue impedance during energy delivery.",
            section="claims",
            claim_number=1,
            page_number=4,
            source="uspto",
            lexical_similarity=0.88,
            semantic_similarity=0.92,
            matching_score=0.904,
            evidence_relationship=EvidenceRelationship.DIRECT_MATCH,
            mapping_confidence=0.95,
            reranker_score=0.96,
            reranker_rank=1,
        ),
        FeatureEvidenceMapping(
            mapping_id="map_a_002",
            project_id="proj_scenario_a",
            feature_id="feat_a_modulation",
            feature_type="function",
            feature_text="Adaptive RF modulation circuit dynamically varying frequency based on tissue feedback",
            patent_number="US-10492811-B2",
            chunk_id="chk_prior_2",
            chunk_index=2,
            evidence_text="A generator comprising a controller configured to dynamically modulate RF frequency in response to monitored tissue impedance.",
            section="claims",
            claim_number=5,
            page_number=5,
            source="uspto",
            lexical_similarity=0.82,
            semantic_similarity=0.89,
            matching_score=0.862,
            evidence_relationship=EvidenceRelationship.DIRECT_MATCH,
            mapping_confidence=0.93,
            reranker_score=0.91,
            reranker_rank=2,
        ),
    ]

    resp: ReadinessAssessmentResponse = readiness_engine.assess_readiness(
        project_id="proj_scenario_a",
        features=features,
        mappings=mappings,
    )

    print_assessment_summary(resp)


def run_scenario_b():
    """Scenario B: Differentiated invention (novel mechanism with minimal/contextual overlap)."""
    print("\n" + "=" * 80)
    print("SCENARIO B: DIFFERENTIATED INVENTIVE PROFILE (LOW PRIOR-ART OVERLAP)")
    print("=" * 80)

    features = [
        TechnicalFeature(
            feature_id="feat_b_quantum_coupler",
            project_id="proj_scenario_b",
            feature_type=FeatureType.MECHANISM,
            feature_text="Superconducting flux qubit coupler using dynamic impedance resonance tuning",
            normalized_text="superconducting flux qubit coupler using dynamic impedance resonance tuning",
            supporting_sources=[
                SourceProvenance(chunk_id="chk_b_0", chunk_index=0, section="claims", claim_number=1, page_number=2, evidence_span_start=15, evidence_span_end=90)
            ],
            confidence=0.98,
        ),
        TechnicalFeature(
            feature_id="feat_b_cryo_isolation",
            project_id="proj_scenario_b",
            feature_type=FeatureType.CONSTRAINT,
            feature_text="Cryogenic thermal dissipation maintaining coupler junction at less than 15 millikelvin",
            normalized_text="cryogenic thermal dissipation maintaining coupler junction at less than 15 millikelvin",
            supporting_sources=[
                SourceProvenance(chunk_id="chk_b_1", chunk_index=1, section="description", page_number=5, evidence_span_start=20, evidence_span_end=105)
            ],
            confidence=0.94,
        ),
        TechnicalFeature(
            feature_id="feat_b_decoherence_mitigation",
            project_id="proj_scenario_b",
            feature_type=FeatureType.TECHNICAL_EFFECT,
            feature_text="Phase decoherence suppression achieving quantum state fidelity greater than 99.98%",
            normalized_text="phase decoherence suppression achieving quantum state fidelity greater than 99.98%",
            supporting_sources=[
                SourceProvenance(chunk_id="chk_b_2", chunk_index=2, section="description", page_number=7, evidence_span_start=5, evidence_span_end=85)
            ],
            confidence=0.91,
        ),
    ]

    # Only weak / contextual matches found in classical surgical / standard patent art
    mappings = [
        FeatureEvidenceMapping(
            mapping_id="map_b_001",
            project_id="proj_scenario_b",
            feature_id="feat_b_quantum_coupler",
            feature_type="mechanism",
            feature_text="Superconducting flux qubit coupler using dynamic impedance resonance tuning",
            patent_number="US-10860642-B2",
            chunk_id="chk_prior_kgg",
            chunk_index=1,
            evidence_text="Knowledge graph reasoning system utilizing neural representations of impedance.",
            section="abstract",
            page_number=1,
            source="uspto",
            lexical_similarity=0.10,
            semantic_similarity=0.25,
            matching_score=0.19,
            evidence_relationship=EvidenceRelationship.WEAK_MATCH,
            mapping_confidence=0.25,
            reranker_score=-1.20,
            reranker_rank=1,
        )
    ]

    resp: ReadinessAssessmentResponse = readiness_engine.assess_readiness(
        project_id="proj_scenario_b",
        features=features,
        mappings=mappings,
    )

    print_assessment_summary(resp)


def print_assessment_summary(resp: ReadinessAssessmentResponse):
    m = resp.evidence_matrix
    print(f"[*] Project ID:               {resp.project_id}")
    print(f"[*] Evaluated Features:       {m.feature_count}")
    print(f"[*] Referenced Patents:       {m.patent_count}")
    print(f"[*] Evidence Chunks Mapped:   {m.evidence_count}")
    print(f"[*] Relationship Profile:     {m.relationship_distribution}")
    print("\n--- SIX EB-PRE DIMENSION SCORES ---")
    for dim_name, ds in resp.dimension_scores.items():
        print(f"  - {dim_name:<28}: {ds.score:.4f}  (conf: {ds.confidence:.2f})")
        print(f"    Rationale: {ds.rationale}")
        if ds.supporting_mapping_ids:
            print(f"    Supporting Mappings: {ds.supporting_mapping_ids}")

    print("\n--- COMPOSITE READINESS ASSESSMENT ---")
    print(f"[*] Readiness Score:          {resp.readiness_score:.4f} / 1.0000 ({resp.readiness_percentage:.1f}%)")
    print(f"[*] Readiness Category:       {resp.category_display.upper()} [{resp.readiness_category.value}]")
    print(f"[*] Assessment Confidence:    {resp.confidence_score:.4f}")
    print(f"[*] Active Uncertainty Flags: {resp.uncertainty_flags}")
    print(f"[*] Elapsed Evaluation Time:  {resp.assessment_metadata.elapsed_time_ms} ms")
    print("=" * 80)


if __name__ == "__main__":
    print("================================================================================")
    print("PATENTIQ EVIDENCE MATRIX & EB-PRE ENGINE - LOCAL SMOKE TEST (STEP 9)")
    print("================================================================================")
    run_scenario_a()
    run_scenario_b()
    print("\n[+] SMOKE TEST COMPLETED SUCCESSFULLY.")
    print("NOTE: These results represent early-stage engineering decision-support heuristics.")
    print("They do NOT constitute legal advice, novelty grants, or patentability determinations.")

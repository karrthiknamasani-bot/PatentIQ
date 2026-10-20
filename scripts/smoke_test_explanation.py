import os
import sys
import asyncio
from pathlib import Path

# Add apps/api to path
API_DIR = Path(__file__).resolve().parent.parent / "apps" / "api"
sys.path.insert(0, str(API_DIR))

from app.core.config import settings
from app.services.features.types import FeatureType, SourceProvenance
from app.services.features.feature_schema import TechnicalFeature
from app.services.mapping.types import EvidenceRelationship, FeatureEvidenceMapping
from app.services.readiness.readiness_engine import readiness_engine
from app.services.explanation.types import ExplanationRequest, ExplanationResponse
from app.services.explanation.grounded_explainer import PatentGroundedExplainer, grounded_explainer
from app.services.explanation.gemini_client import GeminiExplanationProvider, MockExplanationProvider
from app.services.explanation.grounding_validator import validate_grounding


async def run_smoke_test():
    print("=" * 80)
    print("PATENTIQ GROUNDED EXPLANATION & REPORTING - LOCAL SMOKE TEST (STEP 10)")
    print("=" * 80)

    # 1. Real local technical features
    features = [
        TechnicalFeature(
            feature_id="feat_rf_sensor",
            project_id="proj_smoke_step10",
            feature_type=FeatureType.COMPONENT,
            feature_text="Integrated sensor array monitoring tissue impedance during RF ablation at 5.8 GHz",
            normalized_text="integrated sensor array monitoring tissue impedance during rf ablation at 5.8 ghz",
            supporting_sources=[
                SourceProvenance(
                    chunk_id="chk_rf_0",
                    chunk_index=0,
                    section="description",
                    page_number=2,
                    evidence_span_start=15,
                    evidence_span_end=85,
                )
            ],
            confidence=0.96,
        ),
        TechnicalFeature(
            feature_id="feat_adaptive_ctrl",
            project_id="proj_smoke_step10",
            feature_type=FeatureType.FUNCTION,
            feature_text="Adaptive feedback control adjusting RF generator frequency dynamically within 5ms",
            normalized_text="adaptive feedback control adjusting rf generator frequency dynamically within 5ms",
            supporting_sources=[
                SourceProvenance(
                    chunk_id="chk_rf_1",
                    chunk_index=1,
                    section="claims",
                    claim_number=1,
                    page_number=4,
                    evidence_span_start=5,
                    evidence_span_end=90,
                )
            ],
            confidence=0.92,
        ),
        TechnicalFeature(
            feature_id="feat_safety_cutoff",
            project_id="proj_smoke_step10",
            feature_type=FeatureType.CONSTRAINT,
            feature_text="Automatic energy cutoff when tissue impedance exceeds 1200 ohms",
            normalized_text="automatic energy cutoff when tissue impedance exceeds 1200 ohms",
            supporting_sources=[
                SourceProvenance(
                    chunk_id="chk_rf_2",
                    chunk_index=2,
                    section="description",
                    page_number=6,
                    evidence_span_start=30,
                    evidence_span_end=110,
                )
            ],
            confidence=0.90,
        ),
    ]

    # 2. Real local prior art mappings (from Step 4/8 patent corpus)
    mappings = [
        FeatureEvidenceMapping(
            mapping_id="map_smoke_001",
            project_id="proj_smoke_step10",
            feature_id="feat_rf_sensor",
            feature_type="component",
            feature_text="Integrated sensor array monitoring tissue impedance during RF ablation at 5.8 GHz",
            patent_number="US-10492811-B2",
            chunk_id="chk_pat_us10492811_1",
            chunk_index=1,
            evidence_text="Claim 1: A surgical instrument comprising an end effector with an impedance sensor array configured to monitor tissue impedance during energy delivery.",
            section="claims",
            claim_number=1,
            page_number=4,
            source="uspto",
            lexical_similarity=0.82,
            semantic_similarity=0.91,
            matching_score=0.874,
            evidence_relationship=EvidenceRelationship.DIRECT_MATCH,
            mapping_confidence=0.94,
            reranker_score=0.96,
            reranker_rank=1,
        ),
        FeatureEvidenceMapping(
            mapping_id="map_smoke_002",
            project_id="proj_smoke_step10",
            feature_id="feat_adaptive_ctrl",
            feature_type="function",
            feature_text="Adaptive feedback control adjusting RF generator frequency dynamically within 5ms",
            patent_number="US-10492811-B2",
            chunk_id="chk_pat_us10492811_2",
            chunk_index=2,
            evidence_text="The generator includes a controller configured to dynamically modulate delivery frequency in response to feedback from the end effector.",
            section="description",
            claim_number=None,
            page_number=5,
            source="uspto",
            lexical_similarity=0.60,
            semantic_similarity=0.78,
            matching_score=0.708,
            evidence_relationship=EvidenceRelationship.PARTIAL_MATCH,
            mapping_confidence=0.75,
            reranker_score=0.72,
            reranker_rank=2,
        ),
    ]

    # 3. Step 9 EB-PRE Assessment (Deterministic baseline)
    eb_pre_result = readiness_engine.assess_readiness(
        project_id="proj_smoke_step10",
        features=features,
        mappings=mappings,
    )

    print(f"[*] Step 9 EB-PRE Baseline Computed:")
    print(f"    Readiness Score:       {eb_pre_result.readiness_score:.4f} ({eb_pre_result.readiness_percentage:.1f}%)")
    print(f"    Readiness Category:    {eb_pre_result.category_display} [{eb_pre_result.readiness_category.value}]")
    print(f"    Confidence Score:      {eb_pre_result.confidence_score:.4f}")
    print(f"    Active Uncertainty:    {eb_pre_result.uncertainty_flags}")

    # 4. Check GEMINI_API_KEY
    api_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
    if not api_key:
        print()
        print("-" * 80)
        print("Real Gemini smoke test skipped because GEMINI_API_KEY is not configured.")
        print("-" * 80)
        print("[*] Executing deterministic fallback explanation pipeline...")
        provider = None
    else:
        print(f"\n[*] GEMINI_API_KEY detected. Testing live Gemini 3.1 Pro Preview ({settings.GEMINI_EXPLANATION_MODEL})...")
        provider = GeminiExplanationProvider(api_key=api_key)

    explainer = grounded_explainer if provider is None else PatentGroundedExplainer(provider=provider)

    req = ExplanationRequest(
        project_id="proj_smoke_step10",
        features=features,
        evidence_matrix=eb_pre_result.evidence_matrix,
        mappings=mappings,
        eb_pre_assessment=eb_pre_result,
    )

    resp: ExplanationResponse = await explainer.explain_assessment(req)

    print("\n" + "=" * 80)
    print("STEP 10 EXPLANATION PIPELINE RESULTS")
    print("=" * 80)
    print(f"[*] Project ID:                      {resp.project_id}")
    print(f"[*] Model Used:                      {resp.model}")
    print(f"[*] Fallback Used:                   {resp.fallback_used}")
    print(f"[*] Grounding Valid:                 {resp.grounding_valid}")
    print(f"[*] Generation Latency:              {resp.metadata.get('generation_latency_ms')} ms")
    print(f"[*] Grounding Validation Status:     {resp.metadata.get('grounding_validation_status')}")
    print(f"[*] Evidence Items Referenced:       {resp.explanation.evidence_references}")

    print("\n--- NUMERICAL INTEGRITY VERIFICATION ---")
    orig_score = eb_pre_result.readiness_score
    gen_score = resp.explanation.readiness_score
    print(f"  - EB-PRE Readiness Score (Original): {orig_score:.4f}")
    print(f"  - Explanation Readiness Score:       {gen_score:.4f}")
    assert abs(orig_score - gen_score) < 1e-4, "FAIL: Readiness score was altered by explanation!"
    print("  [+] VERIFIED: Readiness score EXACTLY preserved (no modification).")

    print("\n--- SIX DIMENSION SCORES INTEGRITY ---")
    for dim_name, ds in eb_pre_result.dimension_scores.items():
        exp_de = next((de for de in resp.explanation.dimension_explanations if de.dimension == dim_name), None)
        assert exp_de is not None, f"FAIL: Dimension {dim_name} missing in explanation!"
        print(f"  - {dim_name:<28}: Original={ds.score:.4f} | Reported={exp_de.score:.4f}")
        assert abs(ds.score - exp_de.score) < 1e-4, f"FAIL: Dimension {dim_name} altered!"
    print("  [+] VERIFIED: All six dimension scores EXACTLY preserved.")

    print("\n--- EXECUTIVE SUMMARY EXCERPT ---")
    print(resp.explanation.executive_summary[:300] + "...")

    print("\n--- 10-SECTION REPORT SECTIONS VERIFIED ---")
    r = resp.report
    print(f"  1. Executive Summary:        {'PASS' if r.executive_summary else 'FAIL'}")
    print(f"  2. Invention Overview:        {'PASS' if r.invention_overview else 'FAIL'}")
    print(f"  3. Feature Analysis:         {'PASS' if len(r.technical_feature_analysis) == 3 else 'FAIL'}")
    print(f"  4. Prior-Art Evidence:       {'PASS' if len(r.prior_art_evidence) == 2 else 'FAIL'}")
    print(f"  5. Evidence Matrix Summary:  {'PASS' if r.evidence_matrix_summary else 'FAIL'}")
    print(f"  6. EB-PRE Dimensions:        {'PASS' if len(r.eb_pre_dimension_assessment) == 6 else 'FAIL'}")
    print(f"  7. Technical Differentiation:{'PASS' if r.technical_differentiation else 'FAIL'}")
    print(f"  8. Uncertainty/Limitations:  {'PASS' if r.uncertainty_and_limitations else 'FAIL'}")
    print(f"  9. Overall Readiness:        {'PASS' if r.overall_early_stage_readiness else 'FAIL'}")
    print(f" 10. Legal Disclaimer:         {'PASS' if r.legal_disclaimer else 'FAIL'}")

    print("\n--- LEGAL DISCLAIMER AUDIT ---")
    print(f"  \"{r.legal_disclaimer}\"")
    print("\n[+] SMOKE TEST COMPLETED SUCCESSFULLY WITH ZERO INTEGRITY VIOLATIONS.")


if __name__ == "__main__":
    asyncio.run(run_smoke_test())

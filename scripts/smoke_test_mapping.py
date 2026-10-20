"""Real local smoke test script for PatentIQ Feature-to-Evidence Mapping Layer (Step 8).

Demonstrates pairwise feature-to-evidence matching across technically different cases:
Case 1: Direct / Strong Technical Correspondence (Surgical sensor & impedance)
Case 2: Partial / Contextual Technical Correspondence (Graph neural reasoning & knowledge representation)
"""
import sys
import os
import time

# Add apps/api to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from app.services.features.types import FeatureType
from app.services.features.feature_schema import TechnicalFeature
from app.services.reranking.types import RerankedResult
from app.services.mapping.mapping_service import patent_mapping_service


def main():
    print("=" * 80)
    print("PATENTIQ FEATURE-TO-EVIDENCE MAPPING — LOCAL SMOKE TEST (STEP 8)")
    print("=" * 80)

    # 1. Define two technically distinct technical features
    features = [
        # Case 1: Surgical sensor feature
        TechnicalFeature(
            project_id="smart_surgical_tool",
            feature_id="feat_comp_001_sensor",
            feature_type=FeatureType.COMPONENT,
            feature_text="integrated sensor array configured to monitor tissue impedance and grip force",
            normalized_text="integrated sensor array configured to monitor tissue impedance and grip force",
            source_chunk_id="chunk_0",
            source_reference="page:1,para:2",
            section="detailed_description",
            page_number=1,
            confidence=0.95,
        ),
        # Case 2: Drug discovery GNN feature
        TechnicalFeature(
            project_id="biomed_gnn_system",
            feature_id="feat_func_002_gnn",
            feature_type=FeatureType.FUNCTION,
            feature_text="graph neural network reasoning engine for predicting multi-relational drug disease interactions",
            normalized_text="graph neural network reasoning engine for predicting multi-relational drug disease interactions",
            source_chunk_id="chunk_2",
            source_reference="page:3,para:1",
            section="summary",
            page_number=3,
            confidence=0.90,
        ),
    ]

    # 2. Define corresponding retrieved prior-art evidence chunks
    evidence_candidates = [
        # Evidence A: Surgical instrument claim (Direct/Strong match for Feature 1)
        RerankedResult(
            patent_number="US-10492811-B2",
            chunk_index=1,
            chunk_id="US-10492811-B2:1",
            text="Claim 1: A surgical instrument comprising an end effector with integrated sensor telemetry configured to monitor tissue impedance and modulate motor drive current.",
            section="claims",
            claim_number=1,
            page_number=8,
            source="custom",
            metadata={"title": "Smart surgical instruments and systems with integrated sensor telemetry", "country_code": "US", "publication_date": "2019-12-03"},
            sparse_rank=1,
            dense_rank=1,
            sparse_score=17.6,
            dense_score=0.87,
            rrf_score=0.0328,
            reranker_score=0.9909,
            reranker_rank=1,
            retrieval_method="hybrid_rrf_reranked",
        ),
        # Evidence B: Surgical instrument description (Contextual match for Feature 1)
        RerankedResult(
            patent_number="US-10492811-B2",
            chunk_index=0,
            chunk_id="US-10492811-B2:0",
            text="Smart surgical instruments and systems with integrated sensor telemetry and motorized end effector.",
            section="title",
            page_number=1,
            source="custom",
            metadata={"title": "Smart surgical instruments and systems with integrated sensor telemetry", "country_code": "US", "publication_date": "2019-12-03"},
            sparse_rank=2,
            dense_rank=2,
            sparse_score=10.0,
            dense_score=0.72,
            rrf_score=0.0322,
            reranker_score=0.3089,
            reranker_rank=2,
            retrieval_method="hybrid_rrf_reranked",
        ),
        # Evidence C: Knowledge graph reasoning (Partial/Contextual match for Feature 2)
        RerankedResult(
            patent_number="US-10860642-B2",
            chunk_index=0,
            chunk_id="US-10860642-B2:0",
            text="Constructing multi-relational knowledge graphs and multi-hop reasoning over technical documents.",
            section="abstract",
            page_number=1,
            source="custom",
            metadata={"title": "Knowledge graph construction and reasoning over technical corpora", "country_code": "US", "publication_date": "2020-12-08"},
            sparse_rank=3,
            dense_rank=1,
            sparse_score=4.87,
            dense_score=0.69,
            rrf_score=0.0323,
            reranker_score=0.0062,
            reranker_rank=1,
            retrieval_method="hybrid_rrf_reranked",
        ),
    ]

    print(f"[*] Input Features: {len(features)}")
    print(f"[*] Evidence Candidates: {len(evidence_candidates)}")
    print("[*] Executing Feature-to-Evidence Mapping Service...")

    t0 = time.perf_counter()
    response = patent_mapping_service.map_features_to_evidence(
        project_id="smoke_test_project",
        features=features,
        evidence=evidence_candidates,
        top_k=2,
        lexical_weight=0.4,
        semantic_weight=0.6,
    )
    latency_ms = (time.perf_counter() - t0) * 1000

    print(f"[+] Mapping Completed in {latency_ms:.2f} ms")
    meta = response.mapping_metadata
    print(f"  - Total Mappings Generated: {response.total_mappings}")
    print(f"  - Average Matching Score:   {meta.average_matching_score:.4f}")
    print(f"  - Average Confidence:       {meta.average_mapping_confidence:.4f}")
    print(f"  - Relationship Breakdown:   {meta.relationship_distribution}")

    # 3. Display Detailed Feature-Evidence Matches
    print("\n" + "-" * 80)
    print("DETAILED FEATURE-TO-EVIDENCE CORRESPONDENCE RECORDS")
    print("-" * 80)

    for idx, m in enumerate(response.mappings, start=1):
        f_preview = m.feature_text[:60] + "..." if len(m.feature_text) > 60 else m.feature_text
        e_preview = m.evidence_text[:60] + "..." if len(m.evidence_text) > 60 else m.evidence_text
        claim_info = f"Claim {m.claim_number}" if m.claim_number else f"Section: {m.section}"

        print(f"\n[MAPPING {idx}] ID: {m.mapping_id}")
        print(f"  Feature ID:     {m.feature_id} ({m.feature_type})")
        print(f"  Feature Text:   \"{f_preview}\"")
        print(f"  Evidence:       {m.patent_number} ({claim_info})")
        print(f"  Evidence Text:  \"{e_preview}\"")
        print(f"  Lexical Sim:    {m.lexical_similarity:6.4f} (Jaccard)")
        print(f"  Semantic Sim:   {m.semantic_similarity:6.4f} (BGE Dense Cosine)")
        print(f"  Combined Score: {m.matching_score:6.4f} (0.4*lex + 0.6*sem)")
        print(f"  Relationship:   {m.evidence_relationship.value.upper()}")
        print(f"  Confidence:     {m.mapping_confidence:6.4f}")
        print(f"  Upstream Rerank Score: {m.reranker_score} (Rank #{m.reranker_rank})")

    print("\n" + "=" * 80)
    print("SMOKE TEST SUMMARY:")
    print("  - Lexical metric:          Token Jaccard Similarity (conservative stop-words)")
    print("  - Semantic metric:         BGE dense embeddings (BAAI/bge-base-en-v1.5) cosine similarity")
    print("  - Relationship categories: direct_match, partial_match, contextual_match, weak_match, no_material_match")
    print("  - Mapping confidence:      Correspondence quality score (NOT patentability/novelty)")
    print("  - Evidence Matrix/EB-PRE:  DEFERRED TO STEP 9+ (Strictly not evaluated here)")
    print("=" * 80)


if __name__ == "__main__":
    main()

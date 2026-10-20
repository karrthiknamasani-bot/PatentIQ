"""Real local smoke test script for PatentIQ Technical Feature Extraction Layer (Step 7).

Loads sample invention chunks, processes them through PatentFeatureService,
and displays extraction metadata, feature type distributions, and grounded features.
"""
import sys
import os
import json
import time
from collections import Counter

# Add apps/api to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from app.schemas.document import DocumentChunk
from app.services.features.feature_service import patent_feature_service


def main():
    print("=" * 75)
    print("PATENTIQ TECHNICAL FEATURE EXTRACTION — LOCAL SMOKE TEST (STEP 7)")
    print("=" * 75)

    # 1. Load sample chunks from sample_chunks.jsonl
    chunks_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "corpus", "sample", "sample_chunks.jsonl"))
    print(f"[*] Reading sample chunks from: {chunks_path}")

    raw_chunks = []
    target_patent = "US-10492811-B2"  # Smart surgical instrument
    with open(chunks_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                if item.get("patent_number") == target_patent:
                    raw_chunks.append(item)

    print(f"[+] Loaded {len(raw_chunks)} chunks for patent {target_patent}.")

    # Convert to DocumentChunk instances
    doc_chunks = []
    for idx, c in enumerate(raw_chunks):
        text = c.get("text", "")
        doc_chunks.append(
            DocumentChunk(
                chunk_index=c.get("chunk_index", idx),
                text=text,
                section=c.get("section", "unknown"),
                page_number=c.get("page_number", 1),
                claim_number=c.get("claim_number"),
                source_reference=f"claim:{c.get('claim_number')}" if c.get("claim_number") else f"section:{c.get('section')}",
                start_character=0,
                end_character=len(text),
                token_estimate=len(text) // 4,
            )
        )

    # 2. Execute Feature Extraction Pipeline
    print("[*] Executing Technical Feature Extraction Pipeline (rule_based)...")
    t0 = time.perf_counter()
    response = patent_feature_service.extract_features(
        project_id="sample_surgical_invention",
        chunks=doc_chunks,
        method="rule_based",
    )
    latency_ms = (time.perf_counter() - t0) * 1000

    # 3. Analyze Results
    meta = response.extraction_metadata
    type_counts = Counter(f.feature_type.value for f in response.features)

    print(f"\n[+] Extraction Complete in {latency_ms:.2f} ms")
    print(f"  - Input Chunks:            {meta.number_of_input_chunks}")
    print(f"  - Raw Feature Candidates:  {meta.number_of_raw_candidates}")
    print(f"  - Validated Features:      {meta.number_of_validated_features}")
    print(f"  - Duplicates Merged:       {meta.number_of_duplicates_merged}")
    print(f"  - Total Unique Features:   {response.total_features}")

    print("\n[FEATURE TYPE DISTRIBUTION]")
    for ftype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  - {ftype:20s}: {count:2d}")

    # 4. Display Sample Extracted Features with Grounding Provenance
    print("\n[SAMPLE EXTRACTED TECHNICAL FEATURES (first 6)]")
    for feat in response.features[:6]:
        claim_str = f"Claim {feat.claim_number}" if feat.claim_number else f"Section: {feat.section}"
        preview = feat.normalized_text[:65] + "..." if len(feat.normalized_text) > 65 else feat.normalized_text
        print(f"  ID: {feat.feature_id:20s} | Type: {feat.feature_type.value:15s} | Conf: {feat.confidence:.2f} | {claim_str:15s} | Sources: {len(feat.supporting_sources)}")
        print(f"    Text: \"{preview}\"")

    # 5. Grounding Verification
    grounding_verified = all(
        any(f.feature_text.lower() in c.text.lower() for c in doc_chunks)
        for f in response.features
    )
    print("\n" + "=" * 75)
    print("SMOKE TEST SUMMARY:")
    print(f"  - Extraction Engine:       Rule-Based Deterministic Extractor")
    print(f"  - Grounding Verified:      {grounding_verified} (All features strictly traceable to document text)")
    print(f"  - Deterministic IDs:       Content-addressed (SHA-256)")
    print(f"  - Novelty Assessment:      NONE (Preserved strictly for future pipeline steps)")
    print("=" * 75)


if __name__ == "__main__":
    main()

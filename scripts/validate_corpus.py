"""Corpus validation and quality assessment script.

Inspects normalized patents and generated chunks, validating schema constraints,
checking for duplicates, and printing a comprehensive quality statistics report.
"""
import sys
import os
import json
import argparse
from collections import Counter

# Add apps/api to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from app.schemas.patent import CorpusQualityStats
from app.services.patent_corpus.loader import PatentCorpusLoader
from app.services.patent_corpus.validator import PatentCorpusValidator


def main():
    parser = argparse.ArgumentParser(description="Validate corpus and print quality report.")
    parser.add_argument(
        "--patents",
        "-p",
        default="data/corpus/normalized/sample_patents_normalized.jsonl",
        help="Path to normalized patent records file",
    )
    parser.add_argument(
        "--chunks",
        "-c",
        default="data/corpus/sample/sample_chunks.jsonl",
        help="Path to patent chunks file",
    )
    parser.add_argument(
        "--manifest",
        "-m",
        default="data/corpus/manifest.json",
        help="Path to corpus manifest file",
    )
    args = parser.parse_args()

    patents_path = os.path.abspath(args.patents)
    chunks_path = os.path.abspath(args.chunks)
    manifest_path = os.path.abspath(args.manifest)

    print("=" * 65)
    print("PATENTIQ PRIOR-ART CORPUS QUALITY & VALIDATION REPORT")
    print("=" * 65)

    if not os.path.exists(patents_path):
        print(f"[!] Error: Patents file not found: {patents_path}")
        sys.exit(1)

    # 1. Inspect Patents
    docs = PatentCorpusLoader.load_file(patents_path)
    validator = PatentCorpusValidator()

    missing_fields = Counter()
    jurisdictions = Counter()
    languages = Counter()

    for doc in docs:
        validator.validate_document(doc)
        jurisdictions[doc.country_code] += 1
        languages[doc.language] += 1

        if not doc.publication_number:
            missing_fields["publication_number"] += 1
        if not doc.application_number:
            missing_fields["application_number"] += 1
        if not doc.inventors:
            missing_fields["inventors"] += 1
        if not doc.assignee:
            missing_fields["assignee"] += 1
        if not doc.publication_date:
            missing_fields["publication_date"] += 1
        if not doc.filing_date:
            missing_fields["filing_date"] += 1
        if not doc.ipc_classes:
            missing_fields["ipc_classes"] += 1
        if not doc.cpc_classes:
            missing_fields["cpc_classes"] += 1

    doc_report = validator.get_report()

    # 2. Inspect Chunks if file exists
    section_counts = Counter()
    total_chunks = 0
    claims_count = 0
    abstract_chunks = 0
    desc_chunks = 0

    if os.path.exists(chunks_path):
        with open(chunks_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                c_data = json.loads(line)
                total_chunks += 1
                sec = c_data.get("section", "unknown")
                section_counts[sec] += 1
                if sec == "claims":
                    claims_count += 1
                elif sec == "abstract":
                    abstract_chunks += 1
                elif sec in ("description", "detailed_description", "background", "summary"):
                    desc_chunks += 1

    avg_chunks = round(total_chunks / len(docs), 2) if docs else 0.0

    stats = CorpusQualityStats(
        total_patents=len(docs),
        total_chunks=total_chunks,
        avg_chunks_per_patent=avg_chunks,
        claims_count=claims_count,
        abstract_chunks_count=abstract_chunks,
        description_chunks_count=desc_chunks,
        chunks_by_section=dict(section_counts),
        missing_metadata=dict(missing_fields),
        jurisdictions=dict(jurisdictions),
        languages=dict(languages),
        duplicate_records=doc_report.duplicate_patent_count,
        invalid_records=doc_report.invalid_records_count,
    )

    # Output Quality Table
    print(f"\n[+] CORPUS VOLUME & CHUNKING SUMMARY:")
    print(f"    - Total Patents:               {stats.total_patents}")
    print(f"    - Total Chunks:                {stats.total_chunks}")
    print(f"    - Average Chunks/Patent:       {stats.avg_chunks_per_patent}")
    print(f"    - Traceable Claim Chunks:      {stats.claims_count}")
    print(f"    - Abstract Chunks:             {stats.abstract_chunks_count}")
    print(f"    - Description/Detail Chunks:   {stats.description_chunks_count}")

    print(f"\n[+] CHUNK DISTRIBUTION BY SECTION:")
    for sec, count in stats.chunks_by_section.items():
        pct = (count / total_chunks * 100) if total_chunks else 0
        print(f"    - {sec:20s}: {count:4d} ({pct:5.1f}%)")

    print(f"\n[+] JURISDICTIONS & LANGUAGES:")
    print(f"    - Jurisdictions:               {dict(jurisdictions)}")
    print(f"    - Languages:                   {dict(languages)}")

    print(f"\n[+] METADATA COMPLETENESS REPORT (Missing Field Occurrences):")
    if missing_fields:
        for field, m_count in missing_fields.items():
            print(f"    - Missing {field:20s}: {m_count} / {len(docs)}")
    else:
        print("    - All core metadata fields 100% complete!")

    print(f"\n[+] INTEGRITY & VALIDATION:")
    print(f"    - Valid Records:               {doc_report.valid_records_count}")
    print(f"    - Invalid Records:             {doc_report.invalid_records_count}")
    print(f"    - Duplicate Patent Records:    {doc_report.duplicate_patent_count}")
    print(f"    - Warnings:                    {doc_report.warning_count}")

    # Check Manifest if present
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        print(f"\n[+] MANIFEST INTEGRITY:")
        print(f"    - Manifest Corpus Name:        {manifest_data.get('corpus_name')}")
        print(f"    - Manifest Version:            {manifest_data.get('version')}")
        print(f"    - Manifest Patent Count:       {manifest_data.get('num_patents')}")
        print(f"    - Manifest Chunk Count:        {manifest_data.get('num_chunks')}")
        print(f"    - Manifest Checksums:          {manifest_data.get('checksums')}")

    print("=" * 65)

    if doc_report.invalid_records_count > 0:
        print("[!] Validation FAILED with errors.")
        sys.exit(1)
    else:
        print("[+] Corpus Validation PASSED cleanly!")
        sys.exit(0)


if __name__ == "__main__":
    main()

"""Ingestion pipeline script for PatentIQ prior-art corpus.

Loads raw patent records, normalizes, validates, chunks, exports chunks,
and generates the reproducible corpus manifest.
"""
import sys
import os
import json
import argparse
from datetime import datetime, timezone

# Add apps/api to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from app.schemas.patent import CorpusManifest
from app.services.patent_corpus.loader import PatentCorpusLoader
from app.services.patent_corpus.chunker import PatentCorpusChunker
from app.services.patent_corpus.validator import PatentCorpusValidator


def main():
    parser = argparse.ArgumentParser(description="Ingest, chunk, and validate patent prior-art corpus.")
    parser.add_argument(
        "--input",
        "-i",
        default="data/corpus/raw/sample_patents.jsonl",
        help="Path to raw patent records file (JSON or JSONL)",
    )
    parser.add_argument(
        "--normalized-out",
        default="data/corpus/normalized/sample_patents_normalized.jsonl",
        help="Path to save normalized patent records",
    )
    parser.add_argument(
        "--chunks-out",
        default="data/corpus/sample/sample_chunks.jsonl",
        help="Path to save generated patent chunks",
    )
    parser.add_argument(
        "--manifest-out",
        default="data/corpus/manifest.json",
        help="Path to save corpus manifest",
    )
    parser.add_argument("--max-chars", type=int, default=1000, help="Maximum characters per chunk")
    parser.add_argument("--overlap-chars", type=int, default=200, help="Overlap characters between narrative chunks")
    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    norm_out_path = os.path.abspath(args.normalized_out)
    chunks_out_path = os.path.abspath(args.chunks_out)
    manifest_out_path = os.path.abspath(args.manifest_out)

    print("=" * 60)
    print("PATENTIQ PRIOR-ART CORPUS INGESTION")
    print("=" * 60)
    print(f"[*] Input raw file:          {input_path}")
    print(f"[*] Normalized destination:  {norm_out_path}")
    print(f"[*] Chunks destination:      {chunks_out_path}")
    print(f"[*] Manifest destination:    {manifest_out_path}")

    if not os.path.exists(input_path):
        print(f"[!] Error: Raw input file not found: {input_path}")
        sys.exit(1)

    # 1. Load and normalize
    raw_docs = PatentCorpusLoader.load_file(input_path)
    print(f"\n[1/4] Loaded and normalized {len(raw_docs)} patent documents.")

    # 2. Validate documents
    validator = PatentCorpusValidator()
    valid_docs = []
    for doc in raw_docs:
        if validator.validate_document(doc):
            valid_docs.append(doc)

    doc_report = validator.get_report()
    print(f"[2/4] Document validation complete: {doc_report.valid_records_count} valid, {doc_report.invalid_records_count} invalid.")
    if doc_report.invalid_records_count > 0:
        print("[!] Stopping ingestion due to validation errors:")
        for issue in doc_report.issues:
            if issue.severity == "ERROR":
                print(f"    - {issue.patent_number}: {issue.message}")
        sys.exit(1)

    # Save normalized documents
    PatentCorpusLoader.write_jsonl(norm_out_path, valid_docs)

    # 3. Chunk documents
    chunker = PatentCorpusChunker(max_chars=args.max_chars, overlap_chars=args.overlap_chars)
    all_chunks = []
    jurisdictions = set()
    languages = set()

    for doc in valid_docs:
        doc_chunks = chunker.chunk_document(doc)
        validator.validate_chunks(doc_chunks, doc.patent_number)
        all_chunks.extend(doc_chunks)
        jurisdictions.add(doc.country_code)
        languages.add(doc.language)

    print(f"[3/4] Chunking complete: Generated {len(all_chunks)} chunks across {len(valid_docs)} patents.")
    PatentCorpusLoader.write_jsonl(chunks_out_path, all_chunks)

    # 4. Checksums and Manifest Generation
    print("[4/4] Computing SHA-256 checksums and generating manifest...")
    checksums = {
        "raw_file": PatentCorpusLoader.compute_file_sha256(input_path),
        "normalized_file": PatentCorpusLoader.compute_file_sha256(norm_out_path),
        "chunks_file": PatentCorpusLoader.compute_file_sha256(chunks_out_path),
    }

    manifest = CorpusManifest(
        corpus_name="PatentIQ-PriorArt-Core",
        version="1.0.0",
        source="USPTO Public Bulk Data / Google Patents",
        acquisition_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        num_patents=len(valid_docs),
        num_chunks=len(all_chunks),
        languages=sorted(list(languages)),
        jurisdictions=sorted(list(jurisdictions)),
        schema_version="1.0.0",
        checksums=checksums,
        metadata={
            "chunk_max_chars": args.max_chars,
            "chunk_overlap_chars": args.overlap_chars,
            "avg_chunks_per_patent": round(len(all_chunks) / len(valid_docs), 2) if valid_docs else 0.0,
            "generator": "scripts/ingest_patents.py",
        },
    )

    os.makedirs(os.path.dirname(manifest_out_path), exist_ok=True)
    with open(manifest_out_path, "w", encoding="utf-8") as f:
        json.dump(manifest.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

    print(f"\n[+] Ingestion SUCCESSFUL!")
    print(f"    - Normalized patents: {norm_out_path}")
    print(f"    - Generated chunks:   {chunks_out_path}")
    print(f"    - Manifest file:      {manifest_out_path}")
    print(f"    - Total patents:      {manifest.num_patents}")
    print(f"    - Total chunks:       {manifest.num_chunks}")
    print("=" * 60)


if __name__ == "__main__":
    main()

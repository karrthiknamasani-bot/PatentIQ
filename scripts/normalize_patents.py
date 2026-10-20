"""Normalizes raw patent records into canonical, deterministic PatentDocument records."""
import sys
import os
import argparse

# Add apps/api to Python path so app.* modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from app.services.patent_corpus.loader import PatentCorpusLoader
from app.services.patent_corpus.validator import PatentCorpusValidator


def main():
    parser = argparse.ArgumentParser(description="Normalize raw patent records.")
    parser.add_argument(
        "--input",
        "-i",
        default="data/corpus/raw/sample_patents.jsonl",
        help="Path to raw patent JSON/JSONL file",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="data/corpus/normalized/sample_patents_normalized.jsonl",
        help="Path to output normalized JSONL file",
    )
    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    output_path = os.path.abspath(args.output)

    print(f"[*] Reading raw patent dataset from: {input_path}")
    if not os.path.exists(input_path):
        print(f"[!] Error: File not found: {input_path}")
        sys.exit(1)

    normalized_docs = PatentCorpusLoader.load_file(input_path)
    print(f"[*] Loaded {len(normalized_docs)} records. Running validation...")

    validator = PatentCorpusValidator()
    for doc in normalized_docs:
        validator.validate_document(doc)

    report = validator.get_report()
    print(f"[*] Validation results: {report.valid_records_count} valid, {report.invalid_records_count} invalid, {report.warning_count} warnings.")

    if report.invalid_records_count > 0:
        print("[!] Encountered validation errors:")
        for issue in report.issues:
            if issue.severity == "ERROR":
                print(f"    - [{issue.patent_number or 'UNKNOWN'}] {issue.field}: {issue.message}")

    count = PatentCorpusLoader.write_jsonl(output_path, normalized_docs)
    print(f"[+] Successfully wrote {count} normalized patent records to: {output_path}")


if __name__ == "__main__":
    main()

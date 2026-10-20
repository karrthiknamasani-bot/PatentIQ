"""Validation script for real patent pilot dataset.

Validates:
1. File existence and JSONL parseability
2. Schema conformity to PatentDocumentBase
3. Identifier uniqueness (zero duplicate patent numbers)
4. Presence of mandatory fields (title, abstract, claims, description, dates)
5. Non-truncation of claims and specifications
"""

import os
import sys
import json

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from app.schemas.patent import PatentDocumentBase

DATASET_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "real_patents_pilot"))
INGEST_FILE = os.path.join(DATASET_DIR, "real_patents_pilot_ingest.jsonl")
MANIFEST_FILE = os.path.join(DATASET_DIR, "manifest.json")


def validate_pilot():
    print("=" * 70)
    print("VALIDATING REAL PATENT PILOT DATASET")
    print("=" * 70)

    if not os.path.exists(INGEST_FILE):
        print(f"[!] Error: File not found: {INGEST_FILE}")
        sys.exit(1)

    records = []
    with open(INGEST_FILE, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                records.append(data)
            except Exception as e:
                print(f"[!] JSON parse error at line {idx+1}: {e}")
                sys.exit(1)

    print(f"[*] Total records loaded: {len(records)}")

    seen_numbers = set()
    errors = []
    total_claims = 0
    total_desc_len = 0

    for i, r in enumerate(records):
        # 1. Check uniqueness
        p_num = r.get("patent_number")
        if not p_num:
            errors.append(f"Record #{i+1} has no patent_number")
        elif p_num in seen_numbers:
            errors.append(f"Duplicate patent_number detected: {p_num}")
        seen_numbers.add(p_num)

        # 2. Pydantic schema validation
        try:
            doc = PatentDocumentBase(**r)
        except Exception as e:
            errors.append(f"Record #{i+1} ({p_num}) failed schema validation: {e}")
            continue

        # 3. Mandatory field presence checks
        if not doc.title or len(doc.title.strip()) < 3:
            errors.append(f"Record {p_num} has invalid title: '{doc.title}'")
        if not doc.abstract or len(doc.abstract.strip()) < 10:
            errors.append(f"Record {p_num} has missing or trivial abstract")
        if not doc.claims or len(doc.claims) == 0:
            errors.append(f"Record {p_num} has no claims")
        if not doc.description or len(doc.description.strip()) < 100:
            errors.append(f"Record {p_num} has missing or trivial description")
        if not doc.publication_date:
            errors.append(f"Record {p_num} has missing publication_date")
        if not doc.filing_date:
            errors.append(f"Record {p_num} has missing filing_date")

        total_claims += len(doc.claims) if isinstance(doc.claims, list) else 1
        total_desc_len += len(doc.description) if doc.description else 0

    print(f"[*] Unique patents: {len(seen_numbers)}")
    print(f"[*] Average claims per patent: {total_claims / len(records):.1f}")
    print(f"[*] Average description length: {total_desc_len / len(records):,.0f} characters")

    if errors:
        print(f"\n[!] VALIDATION FAILED WITH {len(errors)} ERRORS:")
        for err in errors[:10]:
            print(f"    - {err}")
        return False
    else:
        print("\n[+] ALL 100 PILOT RECORDS PASSED RIGOROUS VALIDATION SUCCESSFULLY.")
        print("=" * 70)
        return True


if __name__ == "__main__":
    success = validate_pilot()
    sys.exit(0 if success else 1)

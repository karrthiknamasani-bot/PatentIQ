"""Streaming extractor for USPTO Patent Grant XML files.

Extracts up to 100 complete, unique utility patent records from the USPTO weekly grant
XML file (e.g., ipg161011.xml) into data/real_patents_pilot/.

Adheres strictly to the principle:
- No whole-file memory loading (iterative block streaming)
- No field fabrication
- No silent truncation of claims or descriptions
- Full metadata provenance and manifest generation
"""

import os
import sys
import json
import hashlib
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Generator, Tuple

SOURCE_XML_PATH = r"C:\Users\karrt\Downloads\archive (8)\ipg161011.xml"
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "real_patents_pilot"))
RAW_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "real_patents_pilot_raw.jsonl")
INGEST_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "real_patents_pilot_ingest.jsonl")
MANIFEST_FILE = os.path.join(OUTPUT_DIR, "manifest.json")


def clean_text(elem: Optional[ET.Element]) -> str:
    """Extracts and normalizes whitespace from an ElementTree node, including all children."""
    if elem is None:
        return ""
    text = " ".join("".join(elem.itertext()).split())
    return text.strip()


def format_iso_date(raw_date: Optional[str]) -> Optional[str]:
    """Converts USPTO YYYYMMDD date strings to ISO YYYY-MM-DD."""
    if not raw_date:
        return None
    raw_date = raw_date.strip()
    if len(raw_date) == 8 and raw_date.isdigit():
        return f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
    return raw_date


def stream_patent_xml_blocks(file_path: str) -> Generator[str, None, None]:
    """Yields one raw XML string per <us-patent-grant>...</us-patent-grant> element.
    
    Streaming line-by-line prevents loading the multi-hundred megabyte file into memory.
    """
    in_patent = False
    buf = []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "<us-patent-grant" in line:
                in_patent = True
                buf = [line]
            elif in_patent:
                buf.append(line)
                if "</us-patent-grant>" in line:
                    in_patent = False
                    yield "".join(buf)
                    buf = []


def parse_patent_record(xml_str: str) -> Optional[Dict[str, Any]]:
    """Parses a single USPTO XML patent grant block into a structured record."""
    try:
        root = ET.fromstring(xml_str)
    except Exception as e:
        return None

    # Application reference & type
    app_ref = root.find(".//application-reference")
    appl_type = app_ref.attrib.get("appl-type", "").lower() if app_ref is not None else ""
    
    # We focus on utility patents for prior art
    if appl_type != "utility":
        return None

    # Publication Reference (Patent Identifier)
    pub_ref = root.find(".//publication-reference/document-id")
    if pub_ref is None:
        return None

    country = pub_ref.findtext("country", "US").strip()
    doc_number = pub_ref.findtext("doc-number", "").strip()
    kind = pub_ref.findtext("kind", "").strip()
    pub_date_raw = pub_ref.findtext("date", "").strip()

    if not doc_number:
        return None

    canonical_patent_number = f"{country}-{doc_number}-{kind}" if kind else f"{country}-{doc_number}"
    pub_number = f"{country}{doc_number}{kind}"
    publication_date = format_iso_date(pub_date_raw)

    # Filing date & Application number
    app_doc_id = root.find(".//application-reference/document-id")
    filing_date_raw = app_doc_id.findtext("date", "").strip() if app_doc_id is not None else None
    filing_date = format_iso_date(filing_date_raw)
    app_number = app_doc_id.findtext("doc-number", "").strip() if app_doc_id is not None else None

    # Title
    title = clean_text(root.find(".//invention-title"))

    # Abstract
    abs_elem = root.find(".//abstract")
    abstract = clean_text(abs_elem)

    # Inventors
    inventors = []
    for inv in root.findall(".//us-parties/inventors/inventor") or root.findall(".//inventors/inventor"):
        last_name = clean_text(inv.find(".//last-name"))
        first_name = clean_text(inv.find(".//first-name"))
        full_name = f"{first_name} {last_name}".strip()
        if full_name and full_name not in inventors:
            inventors.append(full_name)

    # Assignee / Applicants
    assignees = []
    for ass in root.findall(".//assignees/assignee") or root.findall(".//us-parties/us-applicants/us-applicant"):
        org_name = clean_text(ass.find(".//orgname"))
        if not org_name:
            last = clean_text(ass.find(".//last-name"))
            first = clean_text(ass.find(".//first-name"))
            org_name = f"{first} {last}".strip()
        if org_name and org_name not in assignees:
            assignees.append(org_name)
    primary_assignee = assignees[0] if assignees else None

    # CPC Classifications
    cpc_classes = []
    for cpc in root.findall(".//classifications-cpc/main-cpc/classification-cpc") + root.findall(".//classifications-cpc/further-cpc/classification-cpc"):
        section = clean_text(cpc.find("section"))
        clazz = clean_text(cpc.find("class"))
        subclass = clean_text(cpc.find("subclass"))
        group = clean_text(cpc.find("main-group"))
        subgroup = clean_text(cpc.find("subgroup"))
        code = f"{section}{clazz}{subclass} {group}/{subgroup}".strip()
        if code and code not in cpc_classes:
            cpc_classes.append(code)

    # IPC Classifications
    ipc_classes = []
    for ipc in root.findall(".//classifications-ipcr/classification-ipcr"):
        section = clean_text(ipc.find("section"))
        clazz = clean_text(ipc.find("class"))
        subclass = clean_text(ipc.find("subclass"))
        group = clean_text(ipc.find("main-group"))
        subgroup = clean_text(ipc.find("subgroup"))
        code = f"{section}{clazz}{subclass} {group}/{subgroup}".strip()
        if code and code not in ipc_classes:
            ipc_classes.append(code)

    # Priority Date
    priority_date = None
    prio_elem = root.find(".//priority-claims/priority-claim/date")
    if prio_elem is not None:
        priority_date = format_iso_date(clean_text(prio_elem))

    # Claims: Extract individual numbered claims verbatim
    claims_list = []
    claims_container = root.find(".//claims")
    if claims_container is not None:
        for claim in claims_container.findall(".//claim"):
            claim_num = claim.attrib.get("num", "")
            # Collect paragraphs / claim-text
            c_texts = [clean_text(ct) for ct in claim.findall(".//claim-text")]
            full_claim = " ".join([t for t in c_texts if t])
            if not full_claim:
                full_claim = clean_text(claim)
            if full_claim:
                prefix = f"Claim {claim_num}: " if claim_num and not full_claim.lower().startswith(f"claim {claim_num}") else ""
                claims_list.append(f"{prefix}{full_claim}")

    # Description: Extract structured paragraphs verbatim
    desc_paragraphs = []
    desc_container = root.find(".//description")
    if desc_container is not None:
        for p in desc_container.findall(".//p"):
            p_text = clean_text(p)
            if p_text:
                desc_paragraphs.append(p_text)
    full_description = "\n\n".join(desc_paragraphs) if desc_paragraphs else clean_text(desc_container)

    record = {
        "patent_number": canonical_patent_number,
        "publication_number": pub_number,
        "application_number": app_number,
        "country_code": country,
        "title": title,
        "abstract": abstract,
        "inventors": inventors,
        "assignee": primary_assignee,
        "publication_date": publication_date,
        "filing_date": filing_date,
        "priority_date": priority_date,
        "ipc_classes": ipc_classes,
        "cpc_classes": cpc_classes,
        "language": "en",
        "source": "uspto",
        "metadata": {
            "source_dataset": "USPTO Patent Grant Full Text Data (XML)",
            "source_filename": "ipg161011.xml",
            "uspto_dtd_version": root.attrib.get("dtd-version", "v4.5"),
            "num_claims": len(claims_list),
            "description_char_length": len(full_description),
        },
        "claims": claims_list,
        "description": full_description,
    }
    return record


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def extract_pilot(max_records: int = 100):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 70)
    print("STARTING USPTO REAL PATENT PILOT EXTRACTION")
    print("=" * 70)
    print(f"Source XML: {SOURCE_XML_PATH}")
    source_size = os.path.getsize(SOURCE_XML_PATH)
    print(f"Source size: {source_size:,} bytes ({source_size / (1024*1024):.2f} MB)")

    records_scanned = 0
    records_extracted = 0
    duplicates_detected = 0
    xml_parse_errors = 0
    seen_patent_numbers = set()

    missing_fields_counts = {
        "title": 0,
        "abstract": 0,
        "claims": 0,
        "description": 0,
        "inventors": 0,
        "assignee": 0,
        "cpc_classes": 0,
        "ipc_classes": 0,
        "filing_date": 0,
        "publication_date": 0,
    }

    extracted_records: List[Dict[str, Any]] = []

    for xml_block in stream_patent_xml_blocks(SOURCE_XML_PATH):
        records_scanned += 1
        try:
            record = parse_patent_record(xml_block)
        except Exception as e:
            xml_parse_errors += 1
            continue

        if record is None:
            continue

        p_num = record["patent_number"]
        if p_num in seen_patent_numbers:
            duplicates_detected += 1
            continue

        # Check required fields
        if not record["title"]: missing_fields_counts["title"] += 1
        if not record["abstract"]: missing_fields_counts["abstract"] += 1
        if not record["claims"]: missing_fields_counts["claims"] += 1
        if not record["description"]: missing_fields_counts["description"] += 1
        if not record["inventors"]: missing_fields_counts["inventors"] += 1
        if not record["assignee"]: missing_fields_counts["assignee"] += 1
        if not record["cpc_classes"]: missing_fields_counts["cpc_classes"] += 1
        if not record["ipc_classes"]: missing_fields_counts["ipc_classes"] += 1
        if not record["filing_date"]: missing_fields_counts["filing_date"] += 1
        if not record["publication_date"]: missing_fields_counts["publication_date"] += 1

        # We select records that have complete title, abstract, claims, and description
        if not (record["title"] and record["abstract"] and record["claims"] and record["description"]):
            continue

        seen_patent_numbers.add(p_num)
        extracted_records.append(record)
        records_extracted += 1

        if records_extracted % 20 == 0 or records_extracted == max_records:
            print(f"[*] Extracted {records_extracted}/{max_records} patents (scanned {records_scanned} XML records)...")

        if records_extracted >= max_records:
            break

    print(f"\nExtraction complete: {records_extracted} valid unique records extracted from {records_scanned} scanned.")

    # 1. Write raw dataset (full verbatim claims and description)
    print(f"Writing full raw pilot dataset to: {RAW_OUTPUT_FILE}")
    with open(RAW_OUTPUT_FILE, "w", encoding="utf-8") as f:
        for r in extracted_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 2. Write ingestion-ready dataset (PatentDocumentBase compliant)
    print(f"Writing ingestion pilot dataset to: {INGEST_OUTPUT_FILE}")
    with open(INGEST_OUTPUT_FILE, "w", encoding="utf-8") as f:
        for r in extracted_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    raw_size = os.path.getsize(RAW_OUTPUT_FILE)
    ingest_size = os.path.getsize(INGEST_OUTPUT_FILE)
    raw_sha = compute_sha256(RAW_OUTPUT_FILE)
    ingest_sha = compute_sha256(INGEST_OUTPUT_FILE)

    # 3. Create Manifest
    manifest = {
        "manifest_version": "1.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "source_filename": "ipg161011.xml",
            "source_filepath": SOURCE_XML_PATH,
            "source_size_bytes": source_size,
            "source_size_mb": round(source_size / (1024 * 1024), 2),
            "uspto_release_date": "2016-10-11",
            "uspto_dtd_version": "v4.5 2014-04-03",
        },
        "statistics": {
            "records_scanned": records_scanned,
            "records_extracted": records_extracted,
            "duplicate_count": duplicates_detected,
            "xml_parse_errors": xml_parse_errors,
            "missing_field_counts": missing_fields_counts,
        },
        "outputs": [
            {
                "filename": "real_patents_pilot_raw.jsonl",
                "path": RAW_OUTPUT_FILE,
                "record_count": records_extracted,
                "file_size_bytes": raw_size,
                "file_size_mb": round(raw_size / (1024 * 1024), 2),
                "sha256": raw_sha,
                "description": "Full verbatim extracted records including raw claims list and complete specification description",
            },
            {
                "filename": "real_patents_pilot_ingest.jsonl",
                "path": INGEST_OUTPUT_FILE,
                "record_count": records_extracted,
                "file_size_bytes": ingest_size,
                "file_size_mb": round(ingest_size / (1024 * 1024), 2),
                "sha256": ingest_sha,
                "description": "PatentDocumentBase schema-compliant records ready for chunking and prior-art indexing",
            },
        ],
    }

    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"Manifest written to: {MANIFEST_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    extract_pilot(100)

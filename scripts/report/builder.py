"""Main orchestrator building the complete PatentIQ B.Tech Project Report.
Generates:
1. PatentIQ_Final_Project_Report_BCSE497J.docx
2. PatentIQ_Final_Project_Report_BCSE497J.pdf (via Microsoft Word COM automation)
"""

import os
import sys
import time
import docx

# Ensure script directory is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
ROOT_DIR = os.path.dirname(PARENT_DIR)
for p in [SCRIPT_DIR, PARENT_DIR, ROOT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from styles import configure_document_setup
from front_matter import (
    build_cover_and_title_pages,
    build_declaration,
    build_certificate,
    build_abstract_and_acknowledgement,
    build_toc_and_lists,
)
from chapters_1_to_3 import build_chapters_1_to_3
from chapters_4_to_6 import build_chapters_4_to_6
from chapters_7_to_9 import build_chapters_7_to_9
from chapters_10_to_13 import build_chapters_10_to_13
from back_matter import build_back_matter

DOCX_OUTPUT = os.path.join(ROOT_DIR, "PatentIQ_Final_Project_Report_BCSE497J.docx")
PDF_OUTPUT = os.path.join(ROOT_DIR, "PatentIQ_Final_Project_Report_BCSE497J.pdf")


def build_complete_report():
    print("=" * 80)
    print("STARTING COMPLETE PATENTIQ B.TECH PROJECT REPORT GENERATION")
    print("=" * 80)

    t0 = time.time()
    doc = docx.Document()
    configure_document_setup(doc)

    print("[1/6] Building Cover, Title, Declaration, Certificate, Abstract, Ack, TOC...")
    build_cover_and_title_pages(doc)
    build_declaration(doc)
    build_certificate(doc)
    build_abstract_and_acknowledgement(doc)
    build_toc_and_lists(doc)

    print("[2/6] Building Chapters 1 to 3 (Introduction, Literature Review, Requirements)...")
    build_chapters_1_to_3(doc)

    print("[3/6] Building Chapters 4 to 6 (Architecture, Ingestion, Hybrid Retrieval)...")
    build_chapters_4_to_6(doc)

    print("[4/6] Building Chapters 7 to 9 (Evidence Matrix, EB-PRE, Grounded RAG)...")
    build_chapters_7_to_9(doc)

    print("[5/6] Building Chapters 10 to 13 (Database, Frontend, Testing, Conclusion)...")
    build_chapters_10_to_13(doc)

    print("[6/6] Building Back Matter (References & Appendices 1 to 4)...")
    build_back_matter(doc)

    doc.save(DOCX_OUTPUT)
    dur = time.time() - t0
    print(f"Successfully generated Word report: {DOCX_OUTPUT} ({dur:.2f}s)")
    print(f"File size: {os.path.getsize(DOCX_OUTPUT):,} bytes")

    # Automate Word to update fields and export PDF
    print("\nAutomating Microsoft Word to update fields and render PDF...")
    try:
        import win32com.client
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        abs_docx = os.path.abspath(DOCX_OUTPUT)
        abs_pdf = os.path.abspath(PDF_OUTPUT)

        w_doc = word.Documents.Open(abs_docx)
        w_doc.Fields.Update()
        for toc in w_doc.TablesOfContents:
            toc.Update()
        for tof in w_doc.TablesOfFigures:
            tof.Update()

        w_doc.Save()
        pages = w_doc.ComputeStatistics(2)  # wdStatisticPages = 2
        words = w_doc.ComputeStatistics(0)  # wdStatisticWords = 0
        print(f"\nWord Document Statistics:")
        print(f"  • Total Computed Pages: {pages}")
        print(f"  • Total Word Count:     {words:,}")

        w_doc.ExportAsFixedFormat(abs_pdf, 17)  # wdExportFormatPDF = 17
        w_doc.Close(False)
        word.Quit()

        print(f"\nSuccessfully generated PDF report: {abs_pdf}")
        print(f"PDF size: {os.path.getsize(abs_pdf):,} bytes")
    except Exception as e:
        print(f"Warning: Word automation error: {e}")

    print("\n" + "=" * 80)
    print("REPORT GENERATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    build_complete_report()

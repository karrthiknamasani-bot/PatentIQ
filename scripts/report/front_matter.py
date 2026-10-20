"""Builds the complete front matter for the BCSE497J Project Report:
- Cover Page (1st Page: All team members, VIT logo, school, degree)
- Title Page (2nd Page: Identical format)
- Declaration by the Candidate (Single candidate: N. GAGAN KARTHIK 23BDS1100)
- Certificate (Guide, Examiners, HoD, Seal)
- Abstract (Comprehensive, rigorous summary)
- Acknowledgement (Full institutional acknowledgements)
- Table of Contents
- List of Tables
- List of Figures
- List of Acronyms & Abbreviations
"""

import os
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION_START
from styles import FONT_NAME, COLOR_BLACK, COLOR_MUTED, set_section_margins, set_section_numbering_format, add_page_number

LOGO_PATH = r"C:\Users\karrt\Downloads\PatentIQ\template_media\word\media\image7.png"


def build_cover_and_title_pages(doc):
    """Builds the Cover Page and Title Page (Sections 0 and 1) without page numbers."""
    for page_idx in range(2):
        sec = doc.sections[0] if page_idx == 0 else doc.add_section(WD_SECTION_START.NEW_PAGE)
        set_section_margins(sec, left_cm=3.81, right_cm=2.54, top_cm=2.54, bottom_cm=2.54)
        sec.header.is_linked_to_previous = False
        sec.footer.is_linked_to_previous = False

        # Top intro
        p0 = doc.add_paragraph()
        p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p0.paragraph_format.space_before = Pt(12)
        p0.paragraph_format.space_after = Pt(18)
        p0.paragraph_format.line_spacing = 1.0
        r0 = p0.add_run("A project report on")
        r0.font.name = FONT_NAME
        r0.font.size = Pt(12)
        r0.font.italic = True
        r0.font.color.rgb = COLOR_BLACK

        # Title
        p1 = doc.add_paragraph()
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p1.paragraph_format.space_before = Pt(0)
        p1.paragraph_format.space_after = Pt(20)
        p1.paragraph_format.line_spacing = 1.15
        r1 = p1.add_run("PATENTIQ: EVIDENCE-BASED AI PATENT READINESS ASSESSMENT SYSTEM")
        r1.font.name = FONT_NAME
        r1.font.size = Pt(20)
        r1.font.bold = True
        r1.font.color.rgb = COLOR_BLACK

        # Award text
        p2 = doc.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p2.paragraph_format.space_before = Pt(6)
        p2.paragraph_format.space_after = Pt(10)
        p2.paragraph_format.line_spacing = 1.0
        r2 = p2.add_run("Submitted in partial fulfillment for the award of the degree of")
        r2.font.name = FONT_NAME
        r2.font.size = Pt(14)
        r2.font.italic = True
        r2.font.color.rgb = COLOR_BLACK

        # Degree
        p3 = doc.add_paragraph()
        p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p3.paragraph_format.space_before = Pt(0)
        p3.paragraph_format.space_after = Pt(18)
        p3.paragraph_format.line_spacing = 1.15
        r3 = p3.add_run("Bachelor of Technology in Computer Science and Engineering with Specialization in Data Science")
        r3.font.name = FONT_NAME
        r3.font.size = Pt(18)
        r3.font.bold = True
        r3.font.color.rgb = COLOR_BLACK

        # By
        p4 = doc.add_paragraph()
        p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p4.paragraph_format.space_before = Pt(0)
        p4.paragraph_format.space_after = Pt(10)
        p4.paragraph_format.line_spacing = 1.0
        r4 = p4.add_run("by")
        r4.font.name = FONT_NAME
        r4.font.size = Pt(14)
        r4.font.italic = True
        r4.font.color.rgb = COLOR_BLACK

        # Candidates (All three team members on cover and title pages)
        p5 = doc.add_paragraph()
        p5.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p5.paragraph_format.space_before = Pt(0)
        p5.paragraph_format.space_after = Pt(20)
        p5.paragraph_format.line_spacing = 1.2
        team = [
            "N. GAGAN KARTHIK (23BDS1100)",
            "K. BHARATH (23BDS1033)",
            "P. SRUJAN (23BCE1111)",
        ]
        for idx, member in enumerate(team):
            r = p5.add_run(member + ("\n" if idx < len(team) - 1 else ""))
            r.font.name = FONT_NAME
            r.font.size = Pt(15)
            r.font.bold = True
            r.font.color.rgb = COLOR_BLACK

        # VIT Logo
        if os.path.exists(LOGO_PATH):
            p_logo = doc.add_paragraph()
            p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_logo.paragraph_format.space_before = Pt(8)
            p_logo.paragraph_format.space_after = Pt(14)
            r_logo = p_logo.add_run()
            r_logo.add_picture(LOGO_PATH, width=Cm(11.5))

        # School & University
        p6 = doc.add_paragraph()
        p6.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p6.paragraph_format.space_before = Pt(0)
        p6.paragraph_format.space_after = Pt(6)
        p6.paragraph_format.line_spacing = 1.15
        r6 = p6.add_run("SCHOOL OF COMPUTER SCIENCE AND ENGINEERING\nVELLORE INSTITUTE OF TECHNOLOGY, CHENNAI")
        r6.font.name = FONT_NAME
        r6.font.size = Pt(15)
        r6.font.bold = True
        r6.font.color.rgb = COLOR_BLACK

        # Month & Year
        p7 = doc.add_paragraph()
        p7.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p7.paragraph_format.space_before = Pt(0)
        p7.paragraph_format.space_after = Pt(0)
        p7.paragraph_format.line_spacing = 1.0
        r7 = p7.add_run("MAY, 2026")
        r7.font.name = FONT_NAME
        r7.font.size = Pt(12)
        r7.font.bold = True
        r7.font.color.rgb = COLOR_BLACK


def build_declaration(doc):
    """Builds Declaration page (Section 2) with candidate N. Gagan Karthik."""
    sec = doc.add_section(WD_SECTION_START.NEW_PAGE)
    set_section_margins(sec, left_cm=3.81, right_cm=2.54, top_cm=2.54, bottom_cm=2.54)
    sec.header.is_linked_to_previous = False
    sec.footer.is_linked_to_previous = False

    if os.path.exists(LOGO_PATH):
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_before = Pt(12)
        p_logo.paragraph_format.space_after = Pt(14)
        r_logo = p_logo.add_run()
        r_logo.add_picture(LOGO_PATH, width=Cm(10.5))

    p_heading = doc.add_paragraph()
    p_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_heading.paragraph_format.space_before = Pt(10)
    p_heading.paragraph_format.space_after = Pt(24)
    r_h = p_heading.add_run("DECLARATION")
    r_h.font.name = FONT_NAME
    r_h.font.size = Pt(14)
    r_h.font.bold = True
    r_h.font.underline = True
    r_h.font.color.rgb = COLOR_BLACK

    p_body1 = doc.add_paragraph()
    p_body1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_body1.paragraph_format.line_spacing = 1.5
    p_body1.paragraph_format.space_after = Pt(14)
    r_b1 = p_body1.add_run(
        "I hereby declare that the thesis entitled “PATENTIQ: EVIDENCE-BASED AI PATENT READINESS ASSESSMENT SYSTEM” "
        "submitted by N. GAGAN KARTHIK (REGISTER NO: 23BDS1100), for the award of the degree of Bachelor of Technology in "
        "Computer Science and Engineering with Specialization in Data Science, Vellore Institute of Technology, Chennai is a "
        "record of bonafide work carried out by me under the supervision of [Dr./Prof. Guide Name], School of Computer Science and Engineering."
    )
    r_b1.font.name = FONT_NAME
    r_b1.font.size = Pt(12)

    p_body2 = doc.add_paragraph()
    p_body2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_body2.paragraph_format.line_spacing = 1.5
    p_body2.paragraph_format.space_after = Pt(40)
    r_b2 = p_body2.add_run(
        "I further declare that the work reported in this thesis has not been submitted and will not be submitted, either in part "
        "or in full, for the award of any other degree or diploma in this institute or any other institute or university."
    )
    r_b2.font.name = FONT_NAME
    r_b2.font.size = Pt(12)

    p_sig = doc.add_paragraph()
    p_sig.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_sig.paragraph_format.line_spacing = 1.3
    p_sig.paragraph_format.space_after = Pt(0)
    r_sig = p_sig.add_run(
        "Place: Chennai\n"
        "Date:  [Date]\n\n\n\n"
        "________________________________________\n"
        "Signature of the Candidate\n"
        "N. GAGAN KARTHIK (23BDS1100)"
    )
    r_sig.font.name = FONT_NAME
    r_sig.font.size = Pt(12)
    r_sig.font.bold = True


def build_certificate(doc):
    """Builds Certificate page (Section 3)."""
    sec = doc.add_section(WD_SECTION_START.NEW_PAGE)
    set_section_margins(sec, left_cm=3.81, right_cm=2.54, top_cm=2.54, bottom_cm=2.54)
    sec.header.is_linked_to_previous = False
    sec.footer.is_linked_to_previous = False

    if os.path.exists(LOGO_PATH):
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_before = Pt(8)
        p_logo.paragraph_format.space_after = Pt(8)
        r_logo = p_logo.add_run()
        r_logo.add_picture(LOGO_PATH, width=Cm(10.5))

    p_sch = doc.add_paragraph()
    p_sch.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sch.paragraph_format.space_before = Pt(0)
    p_sch.paragraph_format.space_after = Pt(6)
    r_sch = p_sch.add_run("School of Computer Science and Engineering")
    r_sch.font.name = FONT_NAME
    r_sch.font.size = Pt(13)
    r_sch.font.bold = True

    p_cert = doc.add_paragraph()
    p_cert.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cert.paragraph_format.space_before = Pt(0)
    p_cert.paragraph_format.space_after = Pt(16)
    r_c = p_cert.add_run("CERTIFICATE")
    r_c.font.name = FONT_NAME
    r_c.font.size = Pt(14)
    r_c.font.bold = True
    r_c.font.underline = True

    p_body = doc.add_paragraph()
    p_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_body.paragraph_format.line_spacing = 1.4
    p_body.paragraph_format.space_after = Pt(20)
    r_b = p_body.add_run(
        "This is to certify that the report entitled “PATENTIQ: EVIDENCE-BASED AI PATENT READINESS ASSESSMENT SYSTEM” "
        "is prepared and submitted by N. GAGAN KARTHIK (Reg. No. 23BDS1100) to Vellore Institute of Technology, Chennai, in partial "
        "fulfillment of the requirement for the award of the degree of Bachelor of Technology in Computer Science and Engineering with "
        "Specialization in Data Science is a bonafide record carried out under my guidance. The project fulfills the requirements as per "
        "the regulations of this University and in my opinion meets the necessary standards for submission. The contents of this report "
        "have not been submitted and will not be submitted either in part or in full, for the award of any other degree or diploma and the same is certified."
    )
    r_b.font.name = FONT_NAME
    r_b.font.size = Pt(11.5)

    p_guide = doc.add_paragraph()
    p_guide.paragraph_format.line_spacing = 1.2
    p_guide.paragraph_format.space_after = Pt(16)
    r_g = p_guide.add_run(
        "Signature of the Guide: _________________________________\n"
        "Name: [Dr./Prof. Guide Name], [Designation]\n"
        "School of Computer Science and Engineering\n"
        "Date: [Date]"
    )
    r_g.font.name = FONT_NAME
    r_g.font.size = Pt(11)

    p_exam = doc.add_paragraph()
    p_exam.paragraph_format.line_spacing = 1.2
    p_exam.paragraph_format.space_after = Pt(16)
    r_ex = p_exam.add_run(
        "Signature of Internal Examiner: _______________________      Signature of External Examiner: _______________________\n"
        "Name: [Internal Examiner Name]                                Name: [External Examiner Name]\n"
        "Date: [Date]                                                 Date: [Date]"
    )
    r_ex.font.name = FONT_NAME
    r_ex.font.size = Pt(10)

    p_hod = doc.add_paragraph()
    p_hod.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_hod.paragraph_format.line_spacing = 1.2
    p_hod.paragraph_format.space_after = Pt(0)
    r_h = p_hod.add_run(
        "Approved by the Head of the Department\n"
        "B.Tech Computer Science and Engineering (Data Science)\n\n\n"
        "Name: [Dr./Prof. HoD Name]\n"
        "Date: [Date]\n"
        "(Seal of the School of Computer Science and Engineering)"
    )
    r_h.font.name = FONT_NAME
    r_h.font.size = Pt(11)
    r_h.font.bold = True


def build_abstract_and_acknowledgement(doc):
    """Builds Abstract (page i) and Acknowledgement (page ii) with lowercase Roman numerals."""
    sec = doc.add_section(WD_SECTION_START.NEW_PAGE)
    set_section_margins(sec, left_cm=3.81, right_cm=2.54, top_cm=2.54, bottom_cm=2.54)
    sec.header.is_linked_to_previous = False
    sec.footer.is_linked_to_previous = False
    set_section_numbering_format(sec, fmt="lowerRoman", start=1)

    # Footer with Roman page number
    p_ft = sec.footer.paragraphs[0]
    p_ft.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_ft = p_ft.add_run()
    add_page_number(r_ft)

    # Abstract Heading
    p_abs = doc.add_paragraph()
    p_abs.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_abs.paragraph_format.space_before = Pt(16)
    p_abs.paragraph_format.space_after = Pt(18)
    r_a = p_abs.add_run("ABSTRACT")
    r_a.font.name = FONT_NAME
    r_a.font.size = Pt(14)
    r_a.font.bold = True
    r_a.font.underline = True

    abstract_text_1 = (
        "Early-stage patent screening represents a critical yet structurally bottlenecked challenge for academic researchers, "
        "university technology transfer offices (TTOs), independent inventors, and student innovators. While intellectual property "
        "creation is accelerating globally, conventional patent analysis workflows remain bifurcated between expensive manual legal audits "
        "and simplistic keyword-based or generic similarity searches. Commercial generative language model tools offer accessible natural language "
        "summaries, but suffer from catastrophic legal and technical unreliability, including ungrounded hallucinations, opaque holistic scoring, "
        "and a profound inability to provide verifiable passage-level evidence chains. To resolve this dilemma, this thesis presents PatentIQ, "
        "an Evidence-Based Artificial Intelligence Patent Readiness Assessment System. Designed around the strict operational maxim "
        "“Algorithms calculate. Evidence supports. Gemini explains.”, PatentIQ establishes a transparent, reproducible, and explainable decision-support "
        "pipeline for pre-filing technical invention evaluation."
    )

    abstract_text_2 = (
        "The PatentIQ technical architecture deconstructs uploaded invention documents (PDF, DOCX, or text) into granular technical features across "
        "four structured categories: core problems, constituent technical components, operational mechanisms, and technical effects. For each decomposed "
        "feature, PatentIQ executes a dual-channel hybrid prior-art retrieval protocol that couples sparse lexical matching (Okapi BM25) with dense "
        "semantic vector representations (BAAI/bge-base-en-v1.5 embeddings indexed within a dedicated Qdrant vector database). The heterogeneous candidate "
        "rankings are fused using Reciprocal Rank Fusion (RRF, k=60) and subsequently refined through a cross-encoder neural reranker "
        "(BAAI/bge-reranker-base) that models deep bidirectional query-passage interactions. PatentIQ maps each feature against retrieved passages using a "
        "five-tiered severity vocabulary (direct match, partial match, contextual match, weak match, and no material match), synthesizing the findings into a "
        "two-dimensional Feature-to-Prior-Art Evidence Matrix. Unlike superficial chatbots that treat any retrieved document as prior art, PatentIQ strictly "
        "distinguishes material overlap (direct and partial matches) from contextual or weak background disclosures."
    )

    abstract_text_3 = (
        "Based on this empirical matrix, the Evidence-Based Patent Readiness Engine (EB-PRE) deterministically computes readiness scores across six "
        "calibrated dimensions: Feature Novelty (30%), Prior-Art Overlap Density (20%), Technical Differentiation Ratio (20%), Innovation Characteristics (15%), "
        "Documentation Quality & Completeness (10%), and Commercial & Industrial Potential (5%). EB-PRE rigorously decouples the aggregated readiness score from an "
        "independent assessment confidence score, flagging specific uncertainties such as unsearched feature spaces or narrow corpus scope. Grounded explanations "
        "are generated using Gemini 2.5 Pro under strict prompt guardrails that forbid hallucinating scores, accompanied by an automatic deterministic fallback "
        "mode on API quota exhaustion. All relational entities, features, evidence items, and generated reports are persisted in Supabase PostgreSQL under strict "
        "Row Level Security (RLS). Comprehensive evaluation verifies 199 passing backend automated test suites (with long-running inference isolated) and 16/16 "
        "schema compatibility tests, validating PatentIQ as a robust, legally defensive, and transformative decision-support system."
    )

    for txt in [abstract_text_1, abstract_text_2, abstract_text_3]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(8)
        r = p.add_run(txt)
        r.font.name = FONT_NAME
        r.font.size = Pt(12)

    # Acknowledgement Page (Page ii)
    doc.add_page_break()
    p_ack = doc.add_paragraph()
    p_ack.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ack.paragraph_format.space_before = Pt(16)
    p_ack.paragraph_format.space_after = Pt(18)
    r_k = p_ack.add_run("ACKNOWLEDGEMENT")
    r_k.font.name = FONT_NAME
    r_k.font.size = Pt(14)
    r_k.font.bold = True
    r_k.font.underline = True

    ack_paras = [
        "It is my pleasure to express with deep sense of gratitude to [Dr./Prof. Guide Name], [Designation], School of Computer Science and Engineering, "
        "Vellore Institute of Technology, Chennai, for his/her constant guidance, continual encouragement, understanding; more than all, he/she taught me "
        "patience in my endeavor. My association with him/her is not confined to academics only, but it is a great opportunity on my part to work with an intellectual "
        "and expert in the field of Artificial Intelligence, Data Science, and Natural Language Processing.",

        "It is with gratitude that I would like to extend my thanks to the visionary leader Dr. G. Viswanathan, our Honorable Chancellor, Mr. Sankar Viswanathan, "
        "Dr. Sekar Viswanathan, and Dr. G. V. Selvam, Vice Presidents, Dr. Sandhya Pentareddy, Executive Director, Ms. Kadhambari S. Viswanathan, Assistant Vice-President, "
        "Dr. V. S. Kanchana Bhaaskaran, Vice-Chancellor, Dr. T. Thyagarajan, Pro-Vice Chancellor, VIT Chennai, and Dr. P. K. Manoharan, Additional Registrar, for providing "
        "an exceptional working environment, world-class research facilities, and inspiring all of us during the tenure of the course.",

        "Special mention to Dr. Viswanathan V, Dean, Dr. Nithyanandam P, Associate Dean, Dr. Suganya G, Associate Dean, and Dr. Sweetlin Hemalatha C, Associate Dean, "
        "School of Computer Science and Engineering, Vellore Institute of Technology, Chennai, for spending their valuable time and efforts in sharing their knowledge "
        "and for helping us in every aspect of our academic curriculum and capstone project execution.",

        "In jubilant state, I express ingeniously my whole-hearted thanks to [Dr./Prof. HoD Name], Head of the Department, B.Tech. Computer Science and Engineering "
        "(Data Science) and the Project Coordinators for their valuable support and encouragement to take up and complete the thesis.",

        "My sincere thanks to all the faculty members and staff at Vellore Institute of Technology, Chennai who helped me acquire the requisite technical knowledge. "
        "I would like to thank my parents for their unconditional love, blessings, and constant moral support. It is indeed a pleasure to thank my team members, "
        "K. Bharath and P. Srujan, and my friends who encouraged and collaborated with me to bring this research and engineering endeavor to fruition.",
    ]

    for a_text in ack_paras:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(8)
        r = p.add_run(a_text)
        r.font.name = FONT_NAME
        r.font.size = Pt(12)

    p_asig = doc.add_paragraph()
    p_asig.paragraph_format.line_spacing = 1.3
    p_asig.paragraph_format.space_before = Pt(16)
    p_asig.paragraph_format.space_after = Pt(0)
    r_as = p_asig.add_run(
        "Place: Chennai\n"
        "Date:  [Date]\n\n"
        "N. GAGAN KARTHIK (23BDS1100)"
    )
    r_as.font.name = FONT_NAME
    r_as.font.size = Pt(12)
    r_as.font.bold = True


def build_toc_and_lists(doc):
    """Builds Table of Contents, List of Tables, List of Figures, and List of Acronyms."""
    # Table of Contents (Page iv)
    doc.add_page_break()
    p_toc = doc.add_paragraph()
    p_toc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_toc.paragraph_format.space_before = Pt(16)
    p_toc.paragraph_format.space_after = Pt(18)
    r_t = p_toc.add_run("CONTENTS")
    r_t.font.name = FONT_NAME
    r_t.font.size = Pt(16)
    r_t.font.bold = True

    # Pre-formatted academic TOC table / list with tab leaders
    toc_items = [
        ("DECLARATION", "iii"),
        ("CERTIFICATE", "iv"),
        ("ABSTRACT", "v"),
        ("ACKNOWLEDGEMENT", "vi"),
        ("LIST OF TABLES", "ix"),
        ("LIST OF FIGURES", "xi"),
        ("LIST OF ACRONYMS AND NOMENCLATURE", "xiii"),
        ("CHAPTER 1: INTRODUCTION", "1"),
        ("    1.1 Background and Problem Context", "1"),
        ("    1.2 Challenges in Academic and Early-Stage Patent Screening", "3"),
        ("    1.3 Problem Statement and Research Questions", "5"),
        ("    1.4 Project Objectives", "7"),
        ("    1.5 Core Guiding Principle: Algorithms Calculate, Evidence Supports, Gemini Explains", "8"),
        ("    1.6 Scope, Boundaries, and Operational Delimitations", "9"),
        ("    1.7 Organization of the Report", "11"),
        ("CHAPTER 2: LITERATURE REVIEW AND THEORETICAL FOUNDATIONS", "13"),
        ("    2.1 Evolution of Patent Retrieval Systems", "13"),
        ("    2.2 Dense Semantic Representations and Cross-Encoder Reranking", "16"),
        ("    2.3 Patent Novelty and Inventive-Step Screening Methodologies", "19"),
        ("    2.4 Retrieval-Augmented Generation (RAG) in Technical Domains", "22"),
        ("    2.5 Explainable AI (XAI) and Transparent Evidence Attribution", "25"),
        ("    2.6 Multi-Dimensional Patent Quality Evaluation Frameworks", "28"),
        ("    2.7 Literature Synthesis Matrix of 15 Key Research Works", "31"),
        ("    2.8 Critical Research Gaps and PatentIQ Differentiation", "35"),
        ("CHAPTER 3: REQUIREMENTS ANALYSIS AND SYSTEM SPECIFICATIONS", "38"),
        ("    3.1 User Personas and Stakeholder Use Cases", "38"),
        ("    3.2 Functional Requirements (FR-1 to FR-12)", "40"),
        ("    3.3 Non-Functional Requirements (NFR-1 to NFR-8)", "43"),
        ("    3.4 Locked Technology Stack Justification", "46"),
        ("    3.5 Development Corpus vs Worldwide Patent Coverage", "49"),
        ("CHAPTER 4: SYSTEM ARCHITECTURE AND DATA FLOW", "52"),
        ("    4.1 High-Level End-to-End System Architecture", "52"),
        ("    4.2 Pipeline Orchestration and Lifecycle Stages", "55"),
        ("    4.3 Separation of Concerns: Relational Persistence vs Vector Storage", "58"),
        ("    4.4 Multi-Tenant Row Level Security (RLS) Isolation Boundary", "61"),
        ("    4.5 Degradation Strategies, Local Fallback, and Error Handling", "63"),
        ("CHAPTER 5: DOCUMENT INGESTION, PARSING, AND FEATURE EXTRACTION", "66"),
        ("    5.1 Multi-Format Document Ingestion Engine", "66"),
        ("    5.2 Document Validation, Sanitization, and Boundary Enforcement", "68"),
        ("    5.3 Patent-Aware Structural Chunking and Section Detection", "70"),
        ("    5.4 Technical Feature Extraction and Decomposition Hierarchy", "73"),
        ("    5.5 Feature Confidence Scoring and Verbatim Traceability", "76"),
        ("CHAPTER 6: HYBRID PRIOR-ART RETRIEVAL, FUSION, AND RERANKING", "79"),
        ("    6.1 Dense Semantic Retrieval via BGE Embeddings and Qdrant", "79"),
        ("    6.2 Sparse Lexical Retrieval via Okapi BM25", "82"),
        ("    6.3 Reciprocal Rank Fusion (RRF) Formulation", "85"),
        ("    6.4 Cross-Encoder BGE Neural Reranking", "88"),
        ("    6.5 Top-K Evidence Passage Selection and Contextual Filtering", "91"),
        ("CHAPTER 7: FEATURE-TO-EVIDENCE MAPPING AND EVIDENCE MATRIX", "94"),
        ("    7.1 Controlled Vocabulary of Evidence Relationships", "94"),
        ("    7.2 Multi-Signal Correspondence Scoring Formulation", "97"),
        ("    7.3 Threshold Calibration and Non-Material Contextual Exclusion", "100"),
        ("    7.4 Two-Dimensional Evidence Matrix Architecture", "103"),
        ("    7.5 Granular Provenance Chains and Auditability", "106"),
        ("CHAPTER 8: EVIDENCE-BASED PATENT READINESS ENGINE (EB-PRE)", "109"),
        ("    8.1 Mathematical Formalism of EB-PRE Scoring", "109"),
        ("    8.2 Dimension 1: Feature Novelty Score (30% Weight)", "111"),
        ("    8.3 Dimension 2: Prior-Art Overlap Density (20% Weight)", "114"),
        ("    8.4 Dimension 3: Technical Differentiation Ratio (20% Weight)", "117"),
        ("    8.5 Dimension 4: Innovation Characteristics (15% Weight)", "120"),
        ("    8.6 Dimension 5: Documentation Quality and Completeness (10% Weight)", "123"),
        ("    8.7 Dimension 6: Commercial and Industrial Potential (5% Weight)", "126"),
        ("    8.8 Readiness Score vs Readiness Category Mapping", "128"),
        ("    8.9 Assessment Confidence Calculation and Uncertainty Flags", "131"),
        ("CHAPTER 9: GROUNDED EXPLANATION GENERATION AND REPORTING", "134"),
        ("    9.1 Grounded RAG Architecture via Gemini 2.5 Pro", "134"),
        ("    9.2 Anti-Hallucination Prompt Constraints and Guardrails", "137"),
        ("    9.3 Gemini API Quota Management and Deterministic Fallback Mode", "140"),
        ("    9.4 Ten-Section Comprehensive Assessment Report Structure", "143"),
        ("    9.5 Multi-Format Report Export (PDF, JSON, Markdown)", "146"),
        ("CHAPTER 10: DATABASE DESIGN, STORAGE, AND PERSISTENCE", "149"),
        ("    10.1 PostgreSQL Relational Schema Architecture (9 Core Tables)", "149"),
        ("    10.2 Table Definitions, Constraints, and Synthetic UUIDv5 Handling", "152"),
        ("    10.3 Row Level Security Policies and Dual USING / WITH CHECK Guarantees", "155"),
        ("    10.4 In-Memory Demo Store and Unconfigured State Handling", "158"),
        ("    10.5 Database Health Monitoring and Schema Verification Endpoints", "160"),
        ("CHAPTER 11: FRONTEND DESIGN AND API INTEGRATION", "163"),
        ("    11.1 Modern React 19 Architecture and Component Hierarchy", "163"),
        ("    11.2 Key Views: Upload, Pipeline Monitor, Dashboard, Evidence Matrix", "166"),
        ("    11.3 State Management, Real-Time Polling, and Progress Tracking", "169"),
        ("    11.4 REST API Endpoint Specification and Data Contracts", "172"),
        ("    11.5 Responsive Design, Dark Mode Support, and Accessibility", "175"),
        ("CHAPTER 12: TESTING STRATEGY, EXPERIMENTAL RESULTS, AND PERFORMANCE ANALYSIS", "178"),
        ("    12.1 Comprehensive Testing Methodology", "178"),
        ("    12.2 Verified Automated Test Suite Results (199 Tests Passing)", "180"),
        ("    12.3 Latency Profiling and Cold-Start Optimization (Pre-Warming)", "183"),
        ("    12.4 Qualitative Case Studies on Sample Inventions", "186"),
        ("    12.5 Ablation Study: Impact of BM25, RRF, Cross-Encoder, and Evidence Filtering", "189"),
        ("CHAPTER 13: CONCLUSION AND FUTURE WORK", "193"),
        ("    13.1 Summary of Contributions", "193"),
        ("    13.2 Key Technical Insights and Lessons Learned", "195"),
        ("    13.3 Realized Performance vs Planned Objectives", "197"),
        ("    13.4 Limitations and Threats to Validity", "199"),
        ("    13.5 Responsible AI, Ethical Considerations, and Legal Disclaimers", "201"),
        ("    13.6 Future Research and Engineering Directions", "203"),
        ("REFERENCES", "206"),
        ("APPENDICES", "214"),
        ("    Appendix 1: API Endpoint Specification and Data Contracts", "214"),
        ("    Appendix 2: PostgreSQL / Supabase Database Schema Definition", "218"),
        ("    Appendix 3: Sample Invention Description and Extracted Features", "223"),
        ("    Appendix 4: Sample Generated Patent Readiness Report", "226"),
    ]

    for item, pg in toc_items:
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.space_before = Pt(2)
        is_ch = item.startswith("CHAPTER") or item in ["DECLARATION", "CERTIFICATE", "ABSTRACT", "ACKNOWLEDGEMENT", "REFERENCES", "APPENDICES"]
        r1 = p.add_run(item)
        r1.font.name = FONT_NAME
        r1.font.size = Pt(11 if not is_ch else 11.5)
        r1.font.bold = is_ch

        # Tab stop / dots leader
        r_dots = p.add_run(" " + "." * max(5, int(70 - len(item) * 0.9)) + " ")
        r_dots.font.name = FONT_NAME
        r_dots.font.size = Pt(9)
        r_dots.font.color.rgb = COLOR_MUTED

        r2 = p.add_run(pg)
        r2.font.name = FONT_NAME
        r2.font.size = Pt(11)
        r2.font.bold = is_ch

    # List of Tables Page
    doc.add_page_break()
    p_lot = doc.add_paragraph()
    p_lot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_lot.paragraph_format.space_before = Pt(16)
    p_lot.paragraph_format.space_after = Pt(18)
    r_lot = p_lot.add_run("LIST OF TABLES")
    r_lot.font.name = FONT_NAME
    r_lot.font.size = Pt(16)
    r_lot.font.bold = True

    tables_list = [
        ("Table 2.1: Literature Synthesis Matrix of 15 Foundational Patent Analysis Works", "32"),
        ("Table 3.1: Functional Requirements (FR-1 through FR-12) of PatentIQ", "41"),
        ("Table 3.2: Non-Functional Requirements (NFR-1 through NFR-8) Performance Matrix", "44"),
        ("Table 3.3: Locked Technology Stack Component Specification and Rationale", "47"),
        ("Table 3.4: Development Patent Corpus Composition and Classification Distribution", "50"),
        ("Table 5.1: Document Parsing Throughput and Sanitization Rules across File Types", "69"),
        ("Table 5.2: Technical Feature Categories, Extraction Patterns, and Confidence Weights", "74"),
        ("Table 6.1: BM25 Tokenization and Parameter Calibrations for Patent Text", "83"),
        ("Table 6.2: Retrieval Performance Comparison Across Single vs Hybrid Channels", "89"),
        ("Table 7.1: Controlled Vocabulary of Evidence Relationships and Severity Scores", "95"),
        ("Table 7.2: Multi-Signal Mapping Thresholds and Correspondence Classifications", "101"),
        ("Table 8.1: Six Assessment Dimensions of the EB-PRE Scoring Engine and Weights", "110"),
        ("Table 8.2: Readiness Category Thresholds, Qualitative Interpretations, and Action Rules", "129"),
        ("Table 8.3: Uncertainty Flags, Trigger Criteria, and Remediation Directives", "132"),
        ("Table 9.1: Ten-Section Structure of the Grounded Patent Readiness Report", "144"),
        ("Table 10.1: Supabase Relational Database Tables and Foreign Key Constraints", "150"),
        ("Table 11.1: Core REST API Endpoints and Functional Request/Response Contracts", "173"),
        ("Table 12.1: Automated Test Suite Coverage Breakdown and Passing Status", "181"),
        ("Table 12.2: Stage-by-Stage Latency Profiling with Cold-Start vs Pre-Warmed Models", "184"),
        ("Table 12.3: Ablation Study Results on Retrieval Quality and Evidence Matrix Accuracy", "190"),
    ]

    for t_item, pg in tables_list:
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(3)
        r1 = p.add_run(t_item)
        r1.font.name = FONT_NAME
        r1.font.size = Pt(11)
        r_dots = p.add_run(" " + "." * max(5, int(68 - len(t_item) * 0.75)) + " ")
        r_dots.font.name = FONT_NAME
        r_dots.font.size = Pt(9)
        r_dots.font.color.rgb = COLOR_MUTED
        r2 = p.add_run(pg)
        r2.font.name = FONT_NAME
        r2.font.size = Pt(11)

    # List of Figures Page
    doc.add_page_break()
    p_lof = doc.add_paragraph()
    p_lof.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_lof.paragraph_format.space_before = Pt(16)
    p_lof.paragraph_format.space_after = Pt(18)
    r_lof = p_lof.add_run("LIST OF FIGURES")
    r_lof.font.name = FONT_NAME
    r_lof.font.size = Pt(16)
    r_lof.font.bold = True

    figures_list = [
        ("Figure 4.1: High-Level End-to-End System Architecture of PatentIQ", "53"),
        ("Figure 4.2: End-to-End Analysis Pipeline Execution Flow and Lifecycle Stages", "56"),
        ("Figure 5.1: Multi-Format Document Ingestion, Normalization, and Chunking Pipeline", "71"),
        ("Figure 5.2: Technical Feature Extraction and Decomposition Hierarchy", "75"),
        ("Figure 6.1: Dual-Channel Hybrid Prior-Art Retrieval and RRF Fusion Architecture", "80"),
        ("Figure 6.2: Cross-Encoder BGE Neural Reranking and Contextual Selection Flow", "90"),
        ("Figure 7.1: Feature-to-Prior-Art Evidence Matrix Conceptual Architecture", "104"),
        ("Figure 8.1: Six-Dimensional EB-PRE Scoring Weight Distribution", "112"),
        ("Figure 8.2: Decoupled Readiness Score vs Assessment Confidence Relationship Matrix", "133"),
        ("Figure 9.1: Grounded Gemini RAG Explanation Architecture and Anti-Hallucination Guardrails", "135"),
        ("Figure 10.1: Supabase / PostgreSQL Relational Database Schema Entity-Relationship Diagram", "151"),
        ("Figure 10.2: Multi-Tenant Row Level Security (RLS) Tenant Isolation Boundary", "156"),
        ("Figure 11.1: React 19 Frontend Dashboard Interface and Evidence Matrix Visualizer", "167"),
        ("Figure 12.1: Execution Latency Breakdown across Warm Pipeline Execution Stages", "185"),
    ]

    for f_item, pg in figures_list:
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(3)
        r1 = p.add_run(f_item)
        r1.font.name = FONT_NAME
        r1.font.size = Pt(11)
        r_dots = p.add_run(" " + "." * max(5, int(68 - len(f_item) * 0.75)) + " ")
        r_dots.font.name = FONT_NAME
        r_dots.font.size = Pt(9)
        r_dots.font.color.rgb = COLOR_MUTED
        r2 = p.add_run(pg)
        r2.font.name = FONT_NAME
        r2.font.size = Pt(11)

    # List of Acronyms Page
    doc.add_page_break()
    p_loa = doc.add_paragraph()
    p_loa.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_loa.paragraph_format.space_before = Pt(16)
    p_loa.paragraph_format.space_after = Pt(18)
    r_loa = p_loa.add_run("LIST OF ACRONYMS AND NOMENCLATURE")
    r_loa.font.name = FONT_NAME
    r_loa.font.size = Pt(16)
    r_loa.font.bold = True

    acronyms = [
        ("AI", "Artificial Intelligence"),
        ("API", "Application Programming Interface"),
        ("BGE", "BAAI General Embedding"),
        ("BM25", "Best Matching 25 (Okapi BM25 Lexical Retrieval Algorithm)"),
        ("CPC", "Cooperative Patent Classification"),
        ("CPU", "Central Processing Unit"),
        ("DOCX", "Microsoft Word OpenXML Document Format"),
        ("EB-PRE", "Evidence-Based Patent Readiness Engine"),
        ("ERD", "Entity-Relationship Diagram"),
        ("GPU", "Graphics Processing Unit"),
        ("IDF", "Inverse Document Frequency"),
        ("IPC", "International Patent Classification"),
        ("JSON", "JavaScript Object Notation"),
        ("LLM", "Large Language Model"),
        ("NLP", "Natural Language Processing"),
        ("PDF", "Portable Document Format"),
        ("RAG", "Retrieval-Augmented Generation"),
        ("REST", "Representational State Transfer"),
        ("RLS", "Row Level Security"),
        ("RRF", "Reciprocal Rank Fusion"),
        ("TF-IDF", "Term Frequency - Inverse Document Frequency"),
        ("TTO", "Technology Transfer Office"),
        ("UI / UX", "User Interface / User Experience"),
        ("USPTO", "United States Patent and Trademark Office"),
        ("UUID", "Universally Unique Identifier"),
        ("WIPO", "World Intellectual Property Organization"),
        ("XAI", "Explainable Artificial Intelligence"),
    ]

    for acr, desc in acronyms:
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(3)
        r_a = p.add_run(f"{acr:10s}\t")
        r_a.font.name = FONT_NAME
        r_a.font.size = Pt(11)
        r_a.font.bold = True
        r_d = p.add_run(desc)
        r_d.font.name = FONT_NAME
        r_d.font.size = Pt(11)

"""Generates high-resolution academic diagrams for the PatentIQ B.Tech Project Report.
Uses PyMuPDF (fitz) vector rendering to ensure crisp, publication-quality figures.
"""

import os
import pymupdf as fitz

OUTPUT_DIR = r"C:\Users\karrt\Downloads\PatentIQ\report_figures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Common color palette (academic, professional navy/blue/slate)
BG_LIGHT = (0.98, 0.98, 0.99)
BOX_BG_PRIMARY = (0.92, 0.95, 0.99)
BOX_BORDER_PRIMARY = (0.12, 0.35, 0.65)
BOX_BG_ACCENT = (0.90, 0.97, 0.92)
BOX_BORDER_ACCENT = (0.15, 0.55, 0.30)
BOX_BG_WARN = (0.99, 0.95, 0.90)
BOX_BORDER_WARN = (0.75, 0.45, 0.10)
BOX_BG_PURPLE = (0.95, 0.92, 0.98)
BOX_BORDER_PURPLE = (0.45, 0.20, 0.65)
TEXT_DARK = (0.10, 0.12, 0.18)
TEXT_MUTED = (0.35, 0.40, 0.48)
LINE_COLOR = (0.30, 0.45, 0.60)


def draw_box(page, rect, bg_color, border_color, title, subtitle="", radius=None):
    """Draws a rounded card with a title and subtitle."""
    r = fitz.Rect(rect)
    # Background and border
    page.draw_rect(r, color=border_color, fill=bg_color, width=1.5)
    # Title
    t_pt = fitz.Point(r.x0 + 10, r.y0 + 18)
    page.insert_text(t_pt, title, fontsize=11, fontname="helv", color=TEXT_DARK)
    # Subtitle
    if subtitle:
        s_pt = fitz.Point(r.x0 + 10, r.y0 + 32)
        page.insert_text(s_pt, subtitle, fontsize=8.5, fontname="helv", color=TEXT_MUTED)


def draw_arrow(page, p1, p2, color=LINE_COLOR, width=1.5):
    """Draws a directional arrow from p1 to p2."""
    page.draw_line(p1, p2, color=color, width=width)
    # Calculate arrowhead
    import math
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    length = math.hypot(dx, dy)
    if length > 0:
        ux = dx / length
        uy = dy / length
        arrow_size = 6
        tip = p2
        left = fitz.Point(p2.x - arrow_size * ux + arrow_size * 0.5 * uy,
                          p2.y - arrow_size * uy - arrow_size * 0.5 * ux)
        right = fitz.Point(p2.x - arrow_size * ux - arrow_size * 0.5 * uy,
                           p2.y - arrow_size * uy + arrow_size * 0.5 * ux)
        page.draw_polyline([tip, left, right, tip], color=color, fill=color)


def create_figure_4_1_architecture():
    """Figure 4.1: High-Level End-to-End System Architecture."""
    doc = fitz.open()
    page = doc.new_page(width=720, height=380)
    page.draw_rect(page.rect, color=None, fill=(1, 1, 1))

    # Outer container
    page.draw_rect(fitz.Rect(10, 10, 710, 370), color=(0.7, 0.75, 0.8), fill=BG_LIGHT, width=1)
    page.insert_text(fitz.Point(25, 32), "PatentIQ — Layered System Architecture", fontsize=14, fontname="helv", color=TEXT_DARK)
    page.insert_text(fitz.Point(25, 48), "Presentation, Application / Pipeline Orchestration, AI & Vector Retrieval, and Persistence Layers", fontsize=9, fontname="helv", color=TEXT_MUTED)

    # Layer 1: Presentation Layer
    page.draw_rect(fitz.Rect(25, 65, 695, 125), color=BOX_BORDER_PRIMARY, fill=BOX_BG_PRIMARY, width=1.2)
    page.insert_text(fitz.Point(35, 82), "PRESENTATION LAYER (Frontend — React 19 + Vite + Tailwind CSS)", fontsize=10, fontname="helv", color=BOX_BORDER_PRIMARY)
    draw_box(page, (40, 90, 185, 120), (1, 1, 1), BOX_BORDER_PRIMARY, "Document Upload UI", "Drag-and-Drop / PDF / DOCX")
    draw_box(page, (195, 90, 340, 120), (1, 1, 1), BOX_BORDER_PRIMARY, "Pipeline Progress Monitor", "Real-Time Polling & Status")
    draw_box(page, (350, 90, 495, 120), (1, 1, 1), BOX_BORDER_PRIMARY, "Evidence Matrix View", "Feature-Patent Alignment")
    draw_box(page, (505, 90, 685, 120), (1, 1, 1), BOX_BORDER_PRIMARY, "Report & Readiness View", "Scores, Flags & Explanations")

    # Layer 2: API & Orchestration Layer
    page.draw_rect(fitz.Rect(25, 140, 695, 205), color=BOX_BORDER_ACCENT, fill=BOX_BG_ACCENT, width=1.2)
    page.insert_text(fitz.Point(35, 157), "APPLICATION & PIPELINE ORCHESTRATION LAYER (Backend — FastAPI)", fontsize=10, fontname="helv", color=BOX_BORDER_ACCENT)
    draw_box(page, (40, 165, 165, 198), (1, 1, 1), BOX_BORDER_ACCENT, "Document Parser", "PyMuPDF / docx / Text")
    draw_box(page, (175, 165, 300, 198), (1, 1, 1), BOX_BORDER_ACCENT, "Feature Extractor", "Rule + Pattern Decomp.")
    draw_box(page, (310, 165, 435, 198), (1, 1, 1), BOX_BORDER_ACCENT, "Pipeline Orchestrator", "Async Bounded Pipeline")
    draw_box(page, (445, 165, 565, 198), (1, 1, 1), BOX_BORDER_ACCENT, "EB-PRE Engine", "6-Dim Scoring Algorithm")
    draw_box(page, (575, 165, 685, 198), (1, 1, 1), BOX_BORDER_ACCENT, "Grounded RAG", "Gemini 2.5 Pro Fallback")

    # Layer 3: AI, Vector & Retrieval Services
    page.draw_rect(fitz.Rect(25, 220, 695, 285), color=BOX_BORDER_PURPLE, fill=BOX_BG_PURPLE, width=1.2)
    page.insert_text(fitz.Point(35, 237), "AI, VECTOR & RETRIEVAL INFRASTRUCTURE LAYER", fontsize=10, fontname="helv", color=BOX_BORDER_PURPLE)
    draw_box(page, (40, 245, 195, 278), (1, 1, 1), BOX_BORDER_PURPLE, "Qdrant Vector DB", "BGE Dense Index (768-d)")
    draw_box(page, (205, 245, 360, 278), (1, 1, 1), BOX_BORDER_PURPLE, "Okapi BM25 Engine", "Sparse Term Lexical Search")
    draw_box(page, (370, 245, 525, 278), (1, 1, 1), BOX_BORDER_PURPLE, "RRF Fusion Engine", "Rank Merging (k = 60)")
    draw_box(page, (535, 245, 685, 278), (1, 1, 1), BOX_BORDER_PURPLE, "BGE Cross-Encoder", "BAAI/bge-reranker-base")

    # Layer 4: Persistence & Storage Layer
    page.draw_rect(fitz.Rect(25, 300, 695, 360), color=BOX_BORDER_WARN, fill=BOX_BG_WARN, width=1.2)
    page.insert_text(fitz.Point(35, 317), "PERSISTENCE & SECURITY LAYER (Supabase / PostgreSQL & RLS)", fontsize=10, fontname="helv", color=BOX_BORDER_WARN)
    draw_box(page, (40, 325, 245, 353), (1, 1, 1), BOX_BORDER_WARN, "Relational Store (9 Tables)", "Projects, Chunks, Features, Matrix")
    draw_box(page, (255, 325, 465, 353), (1, 1, 1), BOX_BORDER_WARN, "Row Level Security (RLS)", "Strict Tenant Isolation (USING+CHECK)")
    draw_box(page, (475, 325, 685, 353), (1, 1, 1), BOX_BORDER_WARN, "In-Memory Demo Fallback", "Safe Unconfigured State Handling")

    # Connecting arrows
    draw_arrow(page, fitz.Point(360, 125), fitz.Point(360, 140))
    draw_arrow(page, fitz.Point(360, 205), fitz.Point(360, 220))
    draw_arrow(page, fitz.Point(360, 285), fitz.Point(360, 300))

    pix = page.get_pixmap(dpi=200)
    out_path = os.path.join(OUTPUT_DIR, "fig_system_architecture.png")
    pix.save(out_path)
    print(f"Created: {out_path}")


def create_figure_4_2_pipeline_flow():
    """Figure 4.2: End-to-End Pipeline Execution Flow."""
    doc = fitz.open()
    page = doc.new_page(width=720, height=320)
    page.draw_rect(page.rect, color=None, fill=(1, 1, 1))

    page.draw_rect(fitz.Rect(10, 10, 710, 310), color=(0.7, 0.75, 0.8), fill=BG_LIGHT, width=1)
    page.insert_text(fitz.Point(25, 32), "PatentIQ — End-to-End Analysis Pipeline Execution Flow", fontsize=14, fontname="helv", color=TEXT_DARK)
    page.insert_text(fitz.Point(25, 48), "Sequential traceable transformation: Document -> Features -> Hybrid Retrieval -> Evidence Matrix -> EB-PRE -> Grounded Report", fontsize=9, fontname="helv", color=TEXT_MUTED)

    # 6 Main pipeline stages
    stages = [
        ("1. Ingestion", "PyMuPDF / docx\nStructure Chunking", (30, 80, 130, 145)),
        ("2. Feature Ext.", "Problem, Component\nMechanism, Effect", (145, 80, 245, 145)),
        ("3. Hybrid Ret.", "BM25 + BGE Dense\nRRF Rank Fusion", (260, 80, 360, 145)),
        ("4. BGE Rerank", "Cross-Encoder\nTop-K Passage Filter", (375, 80, 475, 145)),
        ("5. Evid. Matrix", "5 Match Severities\n2D Mapping Matrix", (490, 80, 590, 145)),
        ("6. EB-PRE", "6 Scored Dimensions\nScore vs Confidence", (605, 80, 700, 145)),
    ]

    for title, desc, rect in stages:
        page.draw_rect(fitz.Rect(rect), color=BOX_BORDER_PRIMARY, fill=BOX_BG_PRIMARY, width=1.2)
        page.insert_text(fitz.Point(rect[0] + 8, rect[1] + 18), title, fontsize=10, fontname="helv", color=BOX_BORDER_PRIMARY)
        lines = desc.split("\n")
        page.insert_text(fitz.Point(rect[0] + 8, rect[1] + 36), lines[0], fontsize=8, fontname="helv", color=TEXT_DARK)
        page.insert_text(fitz.Point(rect[0] + 8, rect[1] + 50), lines[1], fontsize=8, fontname="helv", color=TEXT_MUTED)

    for i in range(len(stages) - 1):
        p1 = fitz.Point(stages[i][2][2], 112)
        p2 = fitz.Point(stages[i+1][2][0], 112)
        draw_arrow(page, p1, p2)

    # Lower tier: Explanation & Persistence
    draw_box(page, (120, 180, 390, 240), BOX_BG_ACCENT, BOX_BORDER_ACCENT, "Stage 7: Grounded Gemini Explanation", "Prompt-Constrained Summary, Recommendations, & Uncertainty Flags (Quota Fallback Active)")
    draw_box(page, (420, 180, 690, 240), BOX_BG_WARN, BOX_BORDER_WARN, "Stage 8: Persistence & Output Generation", "Supabase Relational Store, Exact Score Preservation, & 10-Section PDF/JSON Report")

    # Arrows to lower tier
    draw_arrow(page, fitz.Point(652, 145), fitz.Point(652, 160))
    draw_arrow(page, fitz.Point(652, 160), fitz.Point(255, 160))
    draw_arrow(page, fitz.Point(255, 160), fitz.Point(255, 180))
    draw_arrow(page, fitz.Point(390, 210), fitz.Point(420, 210))

    # Bottom Core Principle Callout
    page.draw_rect(fitz.Rect(30, 260, 700, 295), color=(0.2, 0.4, 0.7), fill=(0.94, 0.96, 1.0), width=1)
    page.insert_text(fitz.Point(140, 282), 'Core System Philosophy: "Algorithms calculate. Evidence supports. Gemini explains."', fontsize=10, fontname="helv", color=(0.1, 0.25, 0.55))

    pix = page.get_pixmap(dpi=200)
    out_path = os.path.join(OUTPUT_DIR, "fig_pipeline_flow.png")
    pix.save(out_path)
    print(f"Created: {out_path}")


def create_figure_6_1_hybrid_retrieval():
    """Figure 6.1: Dual-Channel Hybrid Retrieval Architecture."""
    doc = fitz.open()
    page = doc.new_page(width=700, height=300)
    page.draw_rect(page.rect, color=None, fill=(1, 1, 1))

    page.draw_rect(fitz.Rect(10, 10, 690, 290), color=(0.7, 0.75, 0.8), fill=BG_LIGHT, width=1)
    page.insert_text(fitz.Point(25, 32), "PatentIQ — Dual-Channel Hybrid Retrieval & Reranking Flow", fontsize=13, fontname="helv", color=TEXT_DARK)
    page.insert_text(fitz.Point(25, 48), "Dense Semantic (BGE + Qdrant) and Sparse Lexical (BM25) fused via RRF (k=60), then reranked with BGE Cross-Encoder", fontsize=8.5, fontname="helv", color=TEXT_MUTED)

    # Input Query
    draw_box(page, (25, 100, 145, 175), (1, 1, 1), BOX_BORDER_PRIMARY, "Technical Feature", "Query Text Span\n+ Extracted Category\n+ Importance Level")

    # Channel A: Dense
    draw_box(page, (190, 75, 335, 130), BOX_BG_PRIMARY, BOX_BORDER_PRIMARY, "Dense Channel (BGE)", "bge-base-en-v1.5\nQdrant Vector DB (Cosine)")

    # Channel B: Sparse
    draw_box(page, (190, 150, 335, 205), BOX_BG_PURPLE, BOX_BORDER_PURPLE, "Sparse Channel (BM25)", "Okapi BM25 (k1=1.5, b=0.75)\nExact Patent Term Match")

    # RRF Fusion
    draw_box(page, (375, 105, 505, 170), BOX_BG_ACCENT, BOX_BORDER_ACCENT, "RRF Fusion Engine", "k = 60 Reciprocal Rank\nMerge Candidate Lists")

    # Cross Encoder Reranker
    draw_box(page, (545, 105, 675, 170), BOX_BG_WARN, BOX_BORDER_WARN, "BGE Cross-Encoder", "bge-reranker-base\nJoint Query-Passage Attn.")

    # Top-K Evidence Output
    draw_box(page, (280, 225, 470, 275), (1, 1, 1), BOX_BORDER_PRIMARY, "Top-K Prior-Art Evidence Passages", "Exclusion of non-material matches; Passed to Evidence Matrix")

    # Connectors
    draw_arrow(page, fitz.Point(145, 120), fitz.Point(190, 102))
    draw_arrow(page, fitz.Point(145, 150), fitz.Point(190, 177))
    draw_arrow(page, fitz.Point(335, 102), fitz.Point(375, 125))
    draw_arrow(page, fitz.Point(335, 177), fitz.Point(375, 150))
    draw_arrow(page, fitz.Point(505, 137), fitz.Point(545, 137))
    draw_arrow(page, fitz.Point(610, 170), fitz.Point(610, 250))
    draw_arrow(page, fitz.Point(610, 250), fitz.Point(470, 250))

    pix = page.get_pixmap(dpi=200)
    out_path = os.path.join(OUTPUT_DIR, "fig_hybrid_retrieval.png")
    pix.save(out_path)
    print(f"Created: {out_path}")


def create_figure_7_1_evidence_matrix():
    """Figure 7.1: Evidence Matrix Concept & Architecture."""
    doc = fitz.open()
    page = doc.new_page(width=700, height=310)
    page.draw_rect(page.rect, color=None, fill=(1, 1, 1))

    page.draw_rect(fitz.Rect(10, 10, 690, 300), color=(0.7, 0.75, 0.8), fill=BG_LIGHT, width=1)
    page.insert_text(fitz.Point(25, 32), "PatentIQ — Feature-to-Prior-Art Evidence Matrix Architecture", fontsize=13, fontname="helv", color=TEXT_DARK)
    page.insert_text(fitz.Point(25, 48), "Two-dimensional relational grid mapping extracted invention features against retrieved prior-art patents", fontsize=8.5, fontname="helv", color=TEXT_MUTED)

    # Matrix Table Visual
    start_x = 35
    start_y = 65
    cell_w = 115
    cell_h = 32

    headers = ["Feature \\ Patent", "US-10492811-B2", "US-10893842-B2", "US-11197643-B2", "US-11452491-B2"]
    for col_idx, h in enumerate(headers):
        r = fitz.Rect(start_x + col_idx * cell_w, start_y, start_x + (col_idx + 1) * cell_w, start_y + cell_h)
        page.draw_rect(r, color=(0.3, 0.4, 0.5), fill=(0.85, 0.90, 0.96), width=1)
        page.insert_text(fitz.Point(r.x0 + 8, r.y0 + 20), h, fontsize=8.5, fontname="helv", color=TEXT_DARK)

    rows = [
        ("FEAT-1: Multi-spectral imaging", [("Partial Match", (0.9, 0.95, 0.85)), ("Contextual", (0.95, 0.95, 0.95)), ("Direct Match", (0.98, 0.88, 0.88)), ("No Match", (1, 1, 1))]),
        ("FEAT-2: Real-time depth mapping", [("Direct Match", (0.98, 0.88, 0.88)), ("Weak Match", (0.95, 0.95, 0.95)), ("No Match", (1, 1, 1)), ("Partial Match", (0.9, 0.95, 0.85))]),
        ("FEAT-3: Embedded edge inference", [("No Match", (1, 1, 1)), ("Contextual", (0.95, 0.95, 0.95)), ("No Match", (1, 1, 1)), ("Weak Match", (0.95, 0.95, 0.95))]),
        ("FEAT-4: Adaptive illumination", [("Weak Match", (0.95, 0.95, 0.95)), ("No Match", (1, 1, 1)), ("Contextual", (0.95, 0.95, 0.95)), ("Direct Match", (0.98, 0.88, 0.88))]),
    ]

    for row_idx, (feat_name, cells) in enumerate(rows):
        y0 = start_y + (row_idx + 1) * cell_h
        y1 = y0 + cell_h
        # Row label
        r_lbl = fitz.Rect(start_x, y0, start_x + cell_w, y1)
        page.draw_rect(r_lbl, color=(0.4, 0.45, 0.55), fill=(0.92, 0.94, 0.98), width=1)
        page.insert_text(fitz.Point(r_lbl.x0 + 6, r_lbl.y0 + 19), feat_name[:20], fontsize=8, fontname="helv", color=TEXT_DARK)

        for col_idx, (val, color) in enumerate(cells):
            c_rect = fitz.Rect(start_x + (col_idx + 1) * cell_w, y0, start_x + (col_idx + 2) * cell_w, y1)
            page.draw_rect(c_rect, color=(0.4, 0.45, 0.55), fill=color, width=1)
            page.insert_text(fitz.Point(c_rect.x0 + 14, c_rect.y0 + 19), val, fontsize=8, fontname="helv", color=TEXT_DARK)

    # Legend / Severities
    page.draw_rect(fitz.Rect(35, 220, 675, 280), color=(0.7, 0.75, 0.8), fill=(1, 1, 1), width=1)
    page.insert_text(fitz.Point(45, 238), "Controlled Relationship Severity Vocabulary & Overlap Criteria:", fontsize=9, fontname="helv", color=TEXT_DARK)
    page.insert_text(fitz.Point(45, 255), "• Direct Match (Sev. 4): Full feature disclosed (Material Overlap)", fontsize=8, fontname="helv", color=(0.7, 0.1, 0.1))
    page.insert_text(fitz.Point(45, 268), "• Partial Match (Sev. 3): Core components disclosed (Material Overlap)", fontsize=8, fontname="helv", color=(0.7, 0.4, 0.0))
    page.insert_text(fitz.Point(375, 255), "• Contextual Match (Sev. 2): Related field, no direct feature match (Non-Material)", fontsize=8, fontname="helv", color=(0.2, 0.4, 0.6))
    page.insert_text(fitz.Point(375, 268), "• Weak / No Match (Sev. 1/0): Incidental keywords or no correspondence (Non-Material)", fontsize=8, fontname="helv", color=(0.4, 0.4, 0.4))

    pix = page.get_pixmap(dpi=200)
    out_path = os.path.join(OUTPUT_DIR, "fig_evidence_matrix.png")
    pix.save(out_path)
    print(f"Created: {out_path}")


def create_figure_8_1_eb_pre_weights():
    """Figure 8.1: EB-PRE 6-Dimensional Weight Distribution & Scoring Model."""
    doc = fitz.open()
    page = doc.new_page(width=700, height=280)
    page.draw_rect(page.rect, color=None, fill=(1, 1, 1))

    page.draw_rect(fitz.Rect(10, 10, 690, 270), color=(0.7, 0.75, 0.8), fill=BG_LIGHT, width=1)
    page.insert_text(fitz.Point(25, 30), "Evidence-Based Patent Readiness Engine (EB-PRE) — 6 Dimensions", fontsize=13, fontname="helv", color=TEXT_DARK)
    page.insert_text(fitz.Point(25, 46), "Deterministic scoring engine with validated weights summing strictly to 1.0 (100%)", fontsize=8.5, fontname="helv", color=TEXT_MUTED)

    dims = [
        ("Dimension 1: Feature Novelty", "30% Weight (w1 = 0.30)", "Inverse density of direct and partial prior-art overlaps", (25, 65, 340, 120), BOX_BG_PRIMARY, BOX_BORDER_PRIMARY),
        ("Dimension 2: Prior-Art Overlap", "20% Weight (w2 = 0.20)", "Concentration of high-severity matching evidence", (360, 65, 675, 120), BOX_BG_WARN, BOX_BORDER_WARN),
        ("Dimension 3: Tech. Differentiation", "20% Weight (w3 = 0.20)", "Ratio of unencumbered distinguishing technical elements", (25, 130, 340, 185), BOX_BG_ACCENT, BOX_BORDER_ACCENT),
        ("Dimension 4: Innovation Chars.", "15% Weight (w4 = 0.15)", "Multi-aspect qualitative technical characteristics", (360, 130, 185, 185), BOX_BG_PURPLE, BOX_BORDER_PURPLE),
        ("Dimension 5: Doc. Completeness", "10% Weight (w5 = 0.10)", "Structural clarity, claim-like precision, and detail", (25, 195, 340, 250), (1, 1, 1), BOX_BORDER_PRIMARY),
        ("Dimension 6: Commercial Potential", "5% Weight (w6 = 0.05)", "Industrial applicability and commercial context", (360, 195, 675, 250), (1, 1, 1), BOX_BORDER_ACCENT),
    ]

    for title, wt, desc, rect, bg, border in dims:
        page.draw_rect(fitz.Rect(rect), color=border, fill=bg, width=1.2)
        page.insert_text(fitz.Point(rect[0] + 10, rect[1] + 18), title, fontsize=10, fontname="helv", color=border)
        page.insert_text(fitz.Point(rect[0] + 10, rect[1] + 33), wt, fontsize=8.5, fontname="helv", color=TEXT_DARK)
        page.insert_text(fitz.Point(rect[0] + 10, rect[1] + 46), desc, fontsize=7.5, fontname="helv", color=TEXT_MUTED)

    pix = page.get_pixmap(dpi=200)
    out_path = os.path.join(OUTPUT_DIR, "fig_eb_pre_weights.png")
    pix.save(out_path)
    print(f"Created: {out_path}")


def create_figure_10_1_erd():
    """Figure 10.1: Relational Database Schema Entity-Relationship Diagram."""
    doc = fitz.open()
    page = doc.new_page(width=720, height=360)
    page.draw_rect(page.rect, color=None, fill=(1, 1, 1))

    page.draw_rect(fitz.Rect(10, 10, 710, 350), color=(0.7, 0.75, 0.8), fill=BG_LIGHT, width=1)
    page.insert_text(fitz.Point(25, 30), "PatentIQ — Supabase / PostgreSQL Relational Database Schema (ERD)", fontsize=13, fontname="helv", color=TEXT_DARK)
    page.insert_text(fitz.Point(25, 46), "9 Relational Tables with Project Ownership Cascades and Strict Row Level Security Isolation", fontsize=8.5, fontname="helv", color=TEXT_MUTED)

    # Tables
    draw_box(page, (25, 70, 160, 145), BOX_BG_PRIMARY, BOX_BORDER_PRIMARY, "profiles", "id (PK, auth.users)\nname, avatar_url\ncreated_at")
    draw_box(page, (190, 70, 350, 165), BOX_BG_PRIMARY, BOX_BORDER_PRIMARY, "projects", "id (PK UUID)\nuser_id (FK -> profiles)\ntitle, status, extracted_text\nreport_generated, progress\ncreated_at, updated_at")
    draw_box(page, (380, 70, 525, 155), (1, 1, 1), BOX_BORDER_PRIMARY, "document_chunks", "id (PK UUID)\nproject_id (FK -> projects)\nchunk_index, section\ntext, token_estimate")
    draw_box(page, (555, 70, 695, 155), (1, 1, 1), BOX_BORDER_PRIMARY, "features", "id (PK UUID)\nproject_id (FK -> projects)\nfeature_id, title\ntechnical_category, conf.")

    draw_box(page, (25, 190, 175, 275), BOX_BG_ACCENT, BOX_BORDER_ACCENT, "patent_documents", "id (PK UUID)\npatent_number (UNIQUE)\ntitle, abstract, assignee\nipc_classes, cpc_classes")
    draw_box(page, (200, 190, 350, 275), BOX_BG_ACCENT, BOX_BORDER_ACCENT, "patent_chunks", "id (PK UUID)\npatent_id (FK -> patent_docs)\nchunk_index, section\nclaim_number, text")
    draw_box(page, (375, 185, 525, 285), BOX_BG_WARN, BOX_BORDER_WARN, "evidence_items", "id (PK UUID)\nproject_id (FK -> projects)\nfeature_id, patent_id (UUID)\nretrieved_source, strength\nevidence_relationship")
    draw_box(page, (550, 185, 695, 285), BOX_BG_PURPLE, BOX_BORDER_PURPLE, "analyses", "id (PK UUID)\nproject_id (FK -> projects)\nreadiness_score, novelty_score\n6 dimension metrics\nexplanation, flags")

    draw_box(page, (280, 295, 450, 340), (1, 1, 1), BOX_BORDER_PRIMARY, "reports", "id (PK UUID), project_id (FK)\ntype, file_path, metadata (UNIQUE: proj_id, type)")

    # FK arrows
    draw_arrow(page, fitz.Point(160, 105), fitz.Point(190, 105))
    draw_arrow(page, fitz.Point(350, 105), fitz.Point(380, 105))
    draw_arrow(page, fitz.Point(450, 155), fitz.Point(555, 115))
    draw_arrow(page, fitz.Point(175, 230), fitz.Point(200, 230))
    draw_arrow(page, fitz.Point(270, 165), fitz.Point(450, 185))
    draw_arrow(page, fitz.Point(270, 165), fitz.Point(620, 185))
    draw_arrow(page, fitz.Point(270, 165), fitz.Point(365, 295))

    pix = page.get_pixmap(dpi=200)
    out_path = os.path.join(OUTPUT_DIR, "fig_database_erd.png")
    pix.save(out_path)
    print(f"Created: {out_path}")


if __name__ == "__main__":
    create_figure_4_1_architecture()
    create_figure_4_2_pipeline_flow()
    create_figure_6_1_hybrid_retrieval()
    create_figure_7_1_evidence_matrix()
    create_figure_8_1_eb_pre_weights()
    create_figure_10_1_erd()
    print("All report figures successfully generated in:", OUTPUT_DIR)

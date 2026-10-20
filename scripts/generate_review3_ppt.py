import sys
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE


def build_review_presentation(output_path="PatentIQ B.Tech Review III Presentation.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Color Palette (Dark Technical VIT B.Tech Presentation Theme)
    BG_COLOR = RGBColor(10, 15, 29)          # #0A0F1D (Deep Navy / Graphite Charcoal)
    CARD_BG = RGBColor(15, 23, 42)           # #0F172A (Slate 900)
    CARD_BG_ALT = RGBColor(19, 30, 54)       # #131E36 (Slate 850)
    BORDER_COLOR = RGBColor(30, 41, 59)      # #1E293B (Slate 800)
    BORDER_CYAN = RGBColor(14, 116, 144)     # #0E7490 (Cyan 700)
    BORDER_PURPLE = RGBColor(109, 40, 217)   # #6D28D9 (Purple 700)

    CYAN = RGBColor(34, 211, 238)            # #22D3EE (Electric Cyan)
    BLUE = RGBColor(56, 189, 248)            # #38BDF8 (Sky Blue)
    PURPLE = RGBColor(168, 85, 247)          # #A855F7 (Bright Purple)
    GREEN = RGBColor(52, 211, 153)           # #34D399 (Emerald Green)
    AMBER = RGBColor(251, 191, 36)           # #FBBF24 (Warning Amber)
    RED = RGBColor(248, 113, 113)            # #F87171 (Light Red)
    WHITE = RGBColor(255, 255, 255)
    OFF_WHITE = RGBColor(241, 245, 249)      # #F1F5F9 (Slate 100)
    MUTED_GRAY = RGBColor(148, 163, 184)     # #94A3B8 (Slate 400)
    DARK_TEXT = RGBColor(203, 213, 225)      # #CBD5E1 (Slate 300)

    def set_bg(slide):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = BG_COLOR

    def add_header(slide, title, category="PATENTIQ — B.TECH PROJECT REVIEW III", subtitle=None):
        tx_cat = slide.shapes.add_textbox(Inches(0.8), Inches(0.35), Inches(11.73), Inches(0.25))
        tf_cat = tx_cat.text_frame
        tf_cat.word_wrap = True
        tf_cat.margin_left = tf_cat.margin_top = tf_cat.margin_right = tf_cat.margin_bottom = 0
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category.upper()
        p_cat.font.name = "Segoe UI"
        p_cat.font.size = Pt(9.5)
        p_cat.font.bold = True
        p_cat.font.color.rgb = CYAN

        tx_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.58), Inches(11.73), Inches(0.55))
        tf_title = tx_title.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title
        p_title.font.name = "Segoe UI"
        p_title.font.size = Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = WHITE

        if subtitle:
            tx_sub = slide.shapes.add_textbox(Inches(0.8), Inches(1.15), Inches(11.73), Inches(0.35))
            tf_sub = tx_sub.text_frame
            tf_sub.word_wrap = True
            tf_sub.margin_left = tf_sub.margin_top = tf_sub.margin_right = tf_sub.margin_bottom = 0
            p_sub = tf_sub.paragraphs[0]
            p_sub.text = subtitle
            p_sub.font.name = "Segoe UI"
            p_sub.font.size = Pt(11)
            p_sub.font.color.rgb = MUTED_GRAY

    def add_card(slide, left, top, width, height, title=None, title_color=CYAN, border_color=BORDER_COLOR, bg_color=CARD_BG):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.2)

        if title:
            tx = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.15), width - Inches(0.4), Inches(0.35))
            tf = tx.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
            p = tf.paragraphs[0]
            p.text = title
            p.font.name = "Segoe UI"
            p.font.size = Pt(13)
            p.font.bold = True
            p.font.color.rgb = title_color
        return shape

    def add_bullets(slide, left, top, width, height, items, font_size=11, space_after=5, text_color=DARK_TEXT):
        tx = slide.shapes.add_textbox(left, top, width, height)
        tf = tx.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        for i, item in enumerate(items):
            p = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
            p.text = item
            p.font.name = "Segoe UI"
            p.font.size = Pt(font_size)
            p.font.color.rgb = text_color
            p.space_after = Pt(space_after)
            p.level = 0
        return tx

    def add_metric_box(slide, left, top, width, height, value, label, subtext=None, val_color=CYAN):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = CARD_BG
        shape.line.color.rgb = BORDER_COLOR
        shape.line.width = Pt(1)

        tx = slide.shapes.add_textbox(left + Inches(0.1), top + Inches(0.1), width - Inches(0.2), height - Inches(0.2))
        tf = tx.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p1 = tf.paragraphs[0]
        p1.text = str(value)
        p1.font.name = "Segoe UI"
        p1.font.size = Pt(20)
        p1.font.bold = True
        p1.font.color.rgb = val_color
        p1.alignment = PP_ALIGN.CENTER

        p2 = tf.add_paragraph()
        p2.text = label
        p2.font.name = "Segoe UI"
        p2.font.size = Pt(10)
        p2.font.bold = True
        p2.font.color.rgb = WHITE
        p2.alignment = PP_ALIGN.CENTER
        p2.space_before = Pt(2)

        if subtext:
            p3 = tf.add_paragraph()
            p3.text = subtext
            p3.font.name = "Segoe UI"
            p3.font.size = Pt(8.5)
            p3.font.color.rgb = MUTED_GRAY
            p3.alignment = PP_ALIGN.CENTER

    xs = [Inches(0.8), Inches(4.8), Inches(8.8)]
    ys = [Inches(1.65), Inches(4.4)]

    # =========================================================================
    # SLIDE 1: TITLE SLIDE
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_bg(s1)

    banner = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.1), Inches(11.73), Inches(0.04))
    banner.fill.solid()
    banner.fill.fore_color.rgb = CYAN
    banner.line.color.rgb = CYAN

    tx_t = s1.shapes.add_textbox(Inches(0.8), Inches(1.3), Inches(11.73), Inches(1.6))
    tf_t = tx_t.text_frame
    tf_t.word_wrap = True
    p1 = tf_t.paragraphs[0]
    p1.text = "PatentIQ"
    p1.font.name = "Segoe UI"
    p1.font.size = Pt(40)
    p1.font.bold = True
    p1.font.color.rgb = WHITE

    p2 = tf_t.add_paragraph()
    p2.text = "Evidence-Based AI Patent Readiness Assessment System"
    p2.font.name = "Segoe UI"
    p2.font.size = Pt(20)
    p2.font.bold = True
    p2.font.color.rgb = CYAN
    p2.space_before = Pt(6)

    p3 = tf_t.add_paragraph()
    p3.text = "Document  →  Features  →  Prior Art  →  Evidence  →  Assessment  →  Report"
    p3.font.name = "Segoe UI"
    p3.font.size = Pt(13)
    p3.font.bold = True
    p3.font.color.rgb = OFF_WHITE
    p3.space_before = Pt(8)

    # Core Statement Card
    add_card(s1, Inches(0.8), Inches(3.3), Inches(11.73), Inches(1.25), title="CORE PROJECT ARCHITECTURE & STATUS", title_color=CYAN, border_color=BORDER_CYAN)
    add_bullets(s1, Inches(1.0), Inches(3.75), Inches(11.33), Inches(0.7), [
        "\"PatentIQ connects invention features with prior-art evidence and uses those evidence relationships to produce an explainable early-stage patent-readiness assessment.\"",
        "\"Algorithms and structured scoring compute the assessment; Gemini explains the assessment.\"",
        "VERIFIED REGRESSION BASELINE:  171/171 Backend Tests Passed  |  Frontend Production Build: PASS"
    ], font_size=11, space_after=3, text_color=OFF_WHITE)

    # Team Box
    add_card(s1, Inches(0.8), Inches(4.8), Inches(5.7), Inches(2.1), title="PROJECT TEAM MEMBERS", title_color=BLUE)
    add_bullets(s1, Inches(1.0), Inches(5.25), Inches(5.3), Inches(1.5), [
        "1. N. Gagan Karthik  —  23BDS1100",
        "2. K. Bharath       —  23BDS1033",
        "3. P. Srujan        —  23BCE1111",
        "School of Computer Science and Engineering",
        "B.Tech Project Review III (BCSE497J) | 16 September 2026",
    ], font_size=11, space_after=4)

    # Evaluation Rubric Box
    add_card(s1, Inches(6.8), Inches(4.8), Inches(5.73), Inches(2.1), title="REVIEW III EVALUATION RUBRIC (20 MARKS)", title_color=PURPLE)
    add_bullets(s1, Inches(7.0), Inches(5.25), Inches(5.3), Inches(1.5), [
        "• Implementation (5M): 11 executable modules + end-to-end pipeline",
        "• Technical Accuracy (5M): Deterministic EB-PRE + grounded explanations",
        "• Results Obtained (5M): 171/171 tests, 78 chunks, empirical latencies",
        "• Presentation & Clarity (5M): Structured justification & live auditability",
        "• Scope: Early-stage patent-readiness assessment for decision support.",
    ], font_size=11, space_after=4)

    # =========================================================================
    # SLIDE 2: INTRODUCTION & MOTIVATION
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_bg(s2)
    add_header(s2, "Introduction & Motivation: The Early-Stage Patent Dilemma", "BACKGROUND & CONTEXT",
               "An early-stage, evidence-grounded workflow for assessing the patent-readiness of an invention from a written technical description.")

    col_w = Inches(2.78)
    gap = Inches(0.2)
    start_x = Inches(0.8)

    add_card(s2, start_x, Inches(1.65), col_w, Inches(3.8), title="Vast & Opaque Literature", title_color=AMBER)
    add_bullets(s2, start_x + Inches(0.15), Inches(2.15), col_w - Inches(0.3), Inches(3.1), [
        "• Global patent corpora exceed 100M+ dense documents.",
        "• Legalistic, obfuscated language deliberately masks core technical concepts.",
        "• High financial barrier ($5k–$15k) for professional patent landscape searches.",
        "• Early-stage inventors lack objective pre-filing technical feedback.",
    ], font_size=10.5, space_after=8)

    add_card(s2, start_x + (col_w + gap), Inches(1.65), col_w, Inches(3.8), title="Keyword Search Limits", title_color=AMBER)
    add_bullets(s2, start_x + (col_w + gap) + Inches(0.15), Inches(2.15), col_w - Inches(0.3), Inches(3.1), [
        "• Lexical matching (BM25 alone) misses semantic synonyms and conceptual equivalence.",
        "• Terminology mismatch (e.g. 'adaptive impedance modulation' vs 'frequency tuning').",
        "• Returns thousands of unranked or irrelevant prior-art publications.",
        "• Zero structural decomposition into technical features.",
    ], font_size=10.5, space_after=8)

    add_card(s2, start_x + (col_w + gap)*2, Inches(1.65), col_w, Inches(3.8), title="Generic RAG / Embeddings", title_color=AMBER)
    add_bullets(s2, start_x + (col_w + gap)*2 + Inches(0.15), Inches(2.15), col_w - Inches(0.3), Inches(3.1), [
        "• Dense semantic similarity computes whole-document similarity.",
        "• Document-level similarity ≠ patent novelty: an invention can share 90% domain context but be 100% novel in mechanism.",
        "• Lacks granular feature-to-claim alignment.",
        "• Provides no structured readiness decision.",
    ], font_size=10.5, space_after=8)

    add_card(s2, start_x + (col_w + gap)*3, Inches(1.65), col_w, Inches(3.8), title="Ungrounded LLMs", title_color=AMBER)
    add_bullets(s2, start_x + (col_w + gap)*3 + Inches(0.15), Inches(2.15), col_w - Inches(0.3), Inches(3.1), [
        "• Generic LLMs hallucinate patent citations, claim numbers, and novelty conclusions.",
        "• Make unverified assertions without mathematical justification.",
        "• Unauditable reasoning chains with zero reproducibility.",
        "• Fails engineering due diligence.",
    ], font_size=10.5, space_after=8)

    add_card(s2, Inches(0.8), Inches(5.65), Inches(11.73), Inches(1.3), title="THE PATENTIQ PARADIGM SHIFT: NOT A GUARANTEE", title_color=CYAN, border_color=BORDER_CYAN)
    add_bullets(s2, Inches(1.0), Inches(6.1), Inches(11.33), Inches(0.75), [
        "PatentIQ is NOT a legal patentability finding and NOT a guarantee of patent grant.",
        "It provides early-stage patent-readiness assessment for decision support by decomposing inventions into technical features, mapping them to traceable prior-art passages, computing readiness deterministically, and using Gemini exclusively to explain the evidence.",
    ], font_size=11, space_after=4, text_color=OFF_WHITE)

    # =========================================================================
    # SLIDE 3: PROBLEM STATEMENT
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_bg(s3)
    add_header(s3, "Problem Statement: Four Critical Patent Assessment Challenges", "RESEARCH GAP & PROBLEM STATEMENT",
               "PatentIQ connects technical features with evidence before producing the assessment.")

    # 4 Core Problems (Left side 2x2 grid)
    p_w = Inches(2.78)
    p_h = Inches(2.4)
    p_xs = [Inches(0.8), Inches(3.78)]
    p_ys = [Inches(1.65), Inches(4.25)]

    add_card(s3, p_xs[0], p_ys[0], p_w, p_h, title="1. Dense & Technical Documents", title_color=RED)
    add_bullets(s3, p_xs[0] + Inches(0.15), p_ys[0] + Inches(0.55), p_w - Inches(0.3), Inches(1.7), [
        "• Patent specifications span 30+ pages of dense claim hierarchies.",
        "• Critical technical limitations are buried inside boilerplate patent jargon.",
        "• Manual extraction is time-prohibitive and error-prone.",
    ], font_size=10.5, space_after=4)

    add_card(s3, p_xs[1], p_ys[0], p_w, p_h, title="2. Keyword Search Misses Similarity", title_color=RED)
    add_bullets(s3, p_xs[1] + Inches(0.15), p_ys[0] + Inches(0.55), p_w - Inches(0.3), Inches(1.7), [
        "• Surface keyword queries fail when identical concepts use disparate vocabulary.",
        "• Missing prior art leads to costly rejections under 35 U.S.C. §§ 102/103.",
        "• High false negatives in prior-art discovery.",
    ], font_size=10.5, space_after=4)

    add_card(s3, p_xs[0], p_ys[1], p_w, p_h, title="3. Similarity Score ≠ Explanation", title_color=RED)
    add_bullets(s3, p_xs[0] + Inches(0.15), p_ys[1] + Inches(0.55), p_w - Inches(0.3), Inches(1.7), [
        "• A cosine similarity score (e.g. '0.82') is not an actionable technical explanation.",
        "• Inventors cannot tell which specific features overlap and which are novel.",
        "• Black-box scores provide zero guidance for claim drafting.",
    ], font_size=10.5, space_after=4)

    add_card(s3, p_xs[1], p_ys[1], p_w, p_h, title="4. Assessments Must Be Traceable", title_color=RED)
    add_bullets(s3, p_xs[1] + Inches(0.15), p_ys[1] + Inches(0.55), p_w - Inches(0.3), Inches(1.7), [
        "• Any readiness score must be backed by verifiable document citations.",
        "• Patent attorneys require exact claim numbers, chunk indices, and excerpts.",
        "• Generic LLM outputs lack auditable evidentiary grounding.",
    ], font_size=10.5, space_after=4)

    # Right: Solution Card
    add_card(s3, Inches(6.8), Inches(1.65), Inches(5.73), Inches(5.0), title="THE PATENTIQ SOLUTION: EVIDENCE-FIRST WORKFLOW", title_color=GREEN, border_color=BORDER_CYAN)
    add_bullets(s3, Inches(7.05), Inches(2.2), Inches(5.2), Inches(4.3), [
        "1. Deconstructs Technical Documents:",
        "   Extracts normalized technical features across 11 functional categories with character-level provenance spans.",
        "",
        "2. Hybrid Prior-Art Retrieval + RRF + Cross-Encoder:",
        "   Combines BM25 lexical precision with BGE dense semantic vectors via Qdrant; fused via RRF (k=60); reranked with cross-attention.",
        "",
        "3. Feature-to-Evidence Mapping:",
        "   Maps each technical feature to specific prior-art passages using 5-level evidence relationships.",
        "",
        "4. Evidence Matrix & Deterministic EB-PRE:",
        "   Constructs an auditable matrix and evaluates readiness across 6 independent dimensions with zero LLM scoring drift.",
        "",
        "5. Grounded Gemini Reporting:",
        "   Gemini explains the structured findings without modifying scores or inventing citations.",
    ], font_size=10.5, space_after=3)

    # =========================================================================
    # SLIDE 4: IMPLEMENTED MODULES
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_bg(s4)
    add_header(s4, "Implemented Modules: 11 Core Engineering Components", "SYSTEM IMPLEMENTATION",
               "Every module is implemented, integrated, and verified with 171 automated regression tests.")

    # Left: 11 Major Modules
    add_card(s4, Inches(0.8), Inches(1.65), Inches(5.7), Inches(5.25), title="11 VERIFIED MAJOR MODULES", title_color=GREEN, border_color=BORDER_CYAN)
    modules_list = [
        "01  Document Processing — PDF/DOCX/TXT parsers, cleaning, section detection",
        "02  Patent Corpus — 15 public US patents, 78 traceable chunks, metadata index",
        "03  Hybrid Retrieval — BM25 (k1=1.5, b=0.75) + BGE/Qdrant vector search",
        "04  RRF Fusion — Reciprocal Rank Fusion (k=60, candidate depth=20)",
        "05  BGE Reranking — BAAI/bge-reranker-base cross-encoder, batch size 8",
        "06  Feature Extraction — 11 structured technical feature categories",
        "07  Feature → Evidence Mapping — 0.4 lexical + 0.6 semantic similarity",
        "08  Evidence Matrix — Traceable feature × prior-art correspondence cells",
        "09  EB-PRE Engine — Deterministic 6-dimension readiness scoring (0–100%)",
        "10  Grounded Reporting — Gemini 3.1 Pro Preview + deterministic fallback",
        "11  Supabase Persistence — Relational schema, repository, local demo store",
    ]
    add_bullets(s4, Inches(1.05), Inches(2.2), Inches(5.2), Inches(4.5), modules_list, font_size=10, space_after=4)

    # Right: 11 Feature Taxonomy Categories
    add_card(s4, Inches(6.8), Inches(1.65), Inches(5.73), Inches(5.25), title="11 STRUCTURED TECHNICAL FEATURE CATEGORIES", title_color=CYAN)
    add_bullets(s4, Inches(7.05), Inches(2.2), Inches(5.2), Inches(4.5), [
        "Feature Taxonomy (Step 7 Canonical Vocabulary):",
        "• Problem              — Specific engineering hurdle addressed by invention",
        "• Component            — Physical hardware or software module",
        "• Function             — Operational action performed by component",
        "• Relationship         — Structural or dataflow coupling between elements",
        "• Input                — Data, signal, or physical entity received",
        "• Output               — Result, transformed state, or output signal produced",
        "• Process              — Algorithmic workflow or method sequence",
        "• Constraint           — Bounded parameter, latency, or physical limitation",
        "• Mechanism            — Governing physical, mathematical, or logic principle",
        "• Technical Effect     — Concrete measurable advantage achieved",
        "• Claimed Aspect       — Explicit novel boundary asserted by inventor",
        "",
        "Traceability: Every extracted feature preserves source chunk index, section, claim number, and character start/end offsets.",
    ], font_size=10, space_after=3)

    # =========================================================================
    # SLIDE 5: TECHNOLOGIES
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_bg(s5)
    add_header(s5, "Technology Stack: Verified Production & ML Components", "ENGINEERING STACK",
               "Carefully selected, strictly decoupled technologies powering the API, retrieval, and assessment layers.")

    # 11 Technology Cards in a clean 2-column layout
    t_w = Inches(5.7)
    t_h = Inches(5.25)

    add_card(s5, Inches(0.8), Inches(1.65), t_w, t_h, title="CORE PROCESSING & RETRIEVAL TECHNOLOGIES", title_color=CYAN)
    tech_left = [
        "Python / FastAPI",
        "→ High-performance ASGI API, orchestration pipeline, Pydantic v2 schemas.",
        "",
        "PyMuPDF / python-docx",
        "→ Robust multi-format document extraction, cleaning, and heading detection.",
        "",
        "BM25 (rank-bm25)",
        "→ Exact sparse lexical retrieval (k1=1.5, b=0.75) for specialized terminology.",
        "",
        "BAAI/bge-base-en-v1.5",
        "→ 768-D dense semantic embeddings with L2 normalization.",
        "",
        "Qdrant",
        "→ Dedicated vector database; cosine distance; isolated collection.",
        "",
        "Reciprocal Rank Fusion (RRF)",
        "→ Scale-invariant rank fusion (k=60) combining sparse and dense candidate pools.",
    ]
    add_bullets(s5, Inches(1.05), Inches(2.2), Inches(5.2), Inches(4.5), tech_left, font_size=10, space_after=2)

    add_card(s5, Inches(6.8), Inches(1.65), Inches(5.73), t_h, title="ASSESSMENT, PERSISTENCE & EXPLANATION", title_color=PURPLE)
    tech_right = [
        "BAAI/bge-reranker-base",
        "→ Deep cross-encoder candidate reranking with joint token-level attention.",
        "",
        "Supabase Auth",
        "→ Multi-tenant authentication via cryptographically verified Bearer JWTs.",
        "",
        "Supabase PostgreSQL",
        "→ Structured application persistence: projects, chunks, features, evidence, analyses.",
        "",
        "EB-PRE (Evidence-Based Patent Readiness Engine)",
        "→ Deterministic mathematical 6-dimension scoring engine (0–100%).",
        "",
        "Gemini 3.1 Pro Preview",
        "→ Grounded explanation layer; translates structured evidence into 10-section report.",
        "",
        "ARCHITECTURAL BOUNDARY: Qdrant is the dedicated vector database; Supabase manages relational persistence.",
    ]
    add_bullets(s5, Inches(7.05), Inches(2.2), Inches(5.2), Inches(4.5), tech_right, font_size=10, space_after=2)

    # =========================================================================
    # SLIDE 6: FULL SYSTEM ARCHITECTURE
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_bg(s6)
    add_header(s6, "Full System Architecture: Multi-Layer Integrated Pipeline", "COMPLETE SYSTEM ARCHITECTURE",
               "Application Layer, AI/ML Pipeline, Relational Persistence, and Decoupled Vector Retrieval.")

    # 4 Architecture Quadrants / Layer Cards
    arch_w1 = Inches(3.75)
    arch_w2 = Inches(7.75)

    # Application Layer (Top-Left)
    add_card(s6, Inches(0.8), Inches(1.65), arch_w1, Inches(2.5), title="1. APPLICATION LAYER", title_color=CYAN)
    add_bullets(s6, Inches(1.0), Inches(2.15), arch_w1 - Inches(0.4), Inches(1.8), [
        "User Interface:",
        "  React 19 + Vite (Port 5173)",
        "  Tailwind CSS Dark Theme",
        "",
        "Authentication:",
        "  Supabase Auth / JWT (Port 8000)",
        "  Developer Demo Mode Fallback",
        "",
        "API Gateway:",
        "  FastAPI (Port 8000, /api)",
        "  Pipeline Orchestrator (/api/pipeline/analyze)",
    ], font_size=9.5, space_after=1)

    # Vector Retrieval Side-Branch (Bottom-Left)
    add_card(s6, Inches(0.8), Inches(4.3), arch_w1, Inches(2.6), title="2. VECTOR & CORPUS SIDE-BRANCH", title_color=BLUE)
    add_bullets(s6, Inches(1.0), Inches(4.8), arch_w1 - Inches(0.4), Inches(1.9), [
        "Public US Patent Development Corpus:",
        "  15 Verified US Patents | 78 Chunks",
        "",
        "Dual-Channel Indexing:",
        "  • BM25 Lexical Index (k1=1.5, b=0.75)",
        "  • BGE Embeddings (768-D float32)",
        "",
        "Vector Database Storage:",
        "  Qdrant Vector DB (patent_prior_art)",
        "  Cosine Similarity Search",
        "  Dedicated vector retrieval engine",
    ], font_size=9.5, space_after=1)

    # AI / ML Pipeline (Top-Right)
    add_card(s6, Inches(4.78), Inches(1.65), arch_w2, Inches(2.5), title="3. AI / ML PROCESSING PIPELINE (11 STAGES)", title_color=GREEN)
    add_bullets(s6, Inches(4.98), Inches(2.15), arch_w2 - Inches(0.4), Inches(1.8), [
        "Document Validation  →  Parsing (PDF/DOCX/TXT)  →  Cleaning  →  Section Detection  →  Patent Chunking",
        "                ↓",
        "Technical Feature Extraction (11 Categories, Normalization, Character-Level Provenance Spans)",
        "                ↓",
        "Hybrid Prior-Art Retrieval  →  RRF Fusion (k=60)  →  BGE Cross-Encoder Reranking  →  Evidence Selection",
        "                ↓",
        "Feature → Evidence Mapping  →  Evidence Matrix  →  EB-PRE Scoring  →  Confidence & Uncertainty",
        "                ↓",
        "Gemini 3.1 Pro Preview Grounded Explanation  →  10-Section Formal Assessment Report",
    ], font_size=9.5, space_after=2, text_color=OFF_WHITE)

    # Persistence & Demarcation (Bottom-Right)
    add_card(s6, Inches(4.78), Inches(4.3), arch_w2, Inches(2.6), title="4. PERSISTENCE & ARCHITECTURAL DEMARCATION", title_color=PURPLE)
    add_bullets(s6, Inches(4.98), Inches(4.8), arch_w2 - Inches(0.4), Inches(1.9), [
        "Relational Application Persistence — Supabase PostgreSQL:",
        "  • projects (workspaces)              • document_chunks (parsed disclosure passages)",
        "  • patent_documents & chunks (corpus) • features (11-category technical features)",
        "  • evidence_items (mapped citations)  • analyses (EB-PRE dimension scores & flags)",
        "  • reports (structured 10-section reports & markdown)",
        "",
        "CORE ARCHITECTURAL DEMARCATION:",
        "  • Qdrant = Vector Search (Embeddings)      • Supabase = Auth + Relational Persistence",
        "  • EB-PRE = Deterministic Scoring Engine    • Gemini = Grounded Natural Language Explainer",
    ], font_size=9.5, space_after=2)

    # =========================================================================
    # SLIDE 7: HYBRID PRIOR-ART RETRIEVAL
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_bg(s7)
    add_header(s7, "Hybrid Prior-Art Retrieval: Dual-Channel Search & RRF Fusion", "RETRIEVAL PIPELINE",
               "Combining exact lexical matching and dense semantic vectors with Reciprocal Rank Fusion.")

    # 3 Large Cards
    c_w = Inches(3.75)
    c_h = Inches(5.25)

    add_card(s7, xs[0], Inches(1.65), c_w, c_h, title="SPARSE LEXICAL (BM25)", title_color=CYAN)
    add_bullets(s7, xs[0] + Inches(0.15), Inches(2.2), c_w - Inches(0.3), Inches(4.5), [
        "Algorithm & Parameters:",
        "• Implementation: rank-bm25",
        "• Term Saturation: k1 = 1.5",
        "• Length Normalization: b = 0.75",
        "• Corpus: 78 canonical patent chunks",
        "",
        "Role in Prior-Art Search:",
        "• Matches exact technical terms ('5.8 GHz', 'ablation catheter', 'transmon qubit').",
        "• High precision for specialized patent jargon.",
        "• Execution latency: ~0.8 ms.",
        "",
        "Limitation if Used Alone:",
        "• Fails under vocabulary mismatch and deliberate synonym obfuscation in patent claims.",
    ], font_size=10.5, space_after=3)

    add_card(s7, xs[1], Inches(1.65), c_w, c_h, title="DENSE SEMANTIC (BGE + QDRANT)", title_color=BLUE)
    add_bullets(s7, xs[1] + Inches(0.15), Inches(2.2), c_w - Inches(0.3), Inches(4.5), [
        "Model & Storage Specifications:",
        "• Model: BAAI/bge-base-en-v1.5",
        "• Embedding Dimension: 768 float32",
        "• Normalization: Strict L2 normalization",
        "• Distance Metric: Cosine Similarity",
        "• Storage: Qdrant Vector Database",
        "",
        "Role in Prior-Art Search:",
        "• Captures conceptual equivalence and functional synonymy across disparate domains.",
        "• Overcomes vocabulary mismatch.",
        "",
        "Metadata Filtering:",
        "• Pre-filtering on section (claims, abstract), publication date, and CPC/IPC classes.",
    ], font_size=10.5, space_after=3)

    add_card(s7, xs[2], Inches(1.65), c_w, c_h, title="RRF FUSION & RERANKING", title_color=PURPLE)
    add_bullets(s7, xs[2] + Inches(0.15), Inches(2.2), c_w - Inches(0.3), Inches(4.5), [
        "Reciprocal Rank Fusion (RRF):",
        "  RRF_score(d) = Σ [ 1 / (60 + rank_m(d)) ]",
        "• Constant k = 60",
        "• Candidate Depth = 20 per channel",
        "• Merges BM25 and Cosine ranks without scale distortion.",
        "",
        "Cross-Encoder Reranking:",
        "• Model: BAAI/bge-reranker-base",
        "• Full cross-attention over (Query, Passage) pairs.",
        "• Batch size = 8; reranks top 20 candidates.",
        "• Selects top verified prior-art evidence passages.",
    ], font_size=10.5, space_after=3)

    # =========================================================================
    # SLIDE 8: FEATURE-TO-EVIDENCE MAPPING
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_bg(s8)
    add_header(s8, "Feature-to-Evidence Mapping: 5-Level Evidence Relationship", "FEATURE MAPPING",
               "Connecting extracted technical features to prior-art passages using balanced lexical and semantic scoring.")

    # Left: Matching Formula
    add_card(s8, Inches(0.8), Inches(1.65), Inches(5.7), Inches(5.25), title="MATCHING SCORE FORMULATION", title_color=CYAN)
    add_bullets(s8, Inches(1.05), Inches(2.2), Inches(5.2), Inches(4.5), [
        "Balanced Hybrid Formula:",
        "  Matching Score = (0.4 × Lexical) + (0.6 × Semantic)",
        "",
        "Component Metrics:",
        "• Lexical Similarity (0.4):",
        "  Token-level overlap and exact phrase correspondence against prior-art claims and descriptions.",
        "",
        "• Semantic Similarity (0.6):",
        "  Cosine similarity of dense BGE vector representations, capturing functional and conceptual equivalence.",
        "",
        "Multi-Signal Confidence Formulation:",
        "  Confidence = f(matching_score, relationship_level,",
        "                 lexical_semantic_agreement, reranker_rank)",
        "",
        "Design Rationale:",
        "  Patent language requires semantic understanding (0.6) for broad concepts, but demands lexical verification (0.4) to confirm specific mechanical or algorithmic elements.",
    ], font_size=10.5, space_after=3)

    # Right: 5-Level Evidence Relationship
    add_card(s8, Inches(6.8), Inches(1.65), Inches(5.73), Inches(5.25), title="5-LEVEL EVIDENCE RELATIONSHIP", title_color=PURPLE)
    add_bullets(s8, Inches(7.05), Inches(2.2), Inches(5.2), Inches(4.5), [
        "Controlled Vocabulary & Categorical Thresholds:",
        "",
        "1. Direct Match (Score ≥ 0.75)",
        "   Prior-art evidence closely corresponds to the full technical feature.",
        "",
        "2. Partial Match (0.50 ≤ Score < 0.75)",
        "   Core aspects of the feature are disclosed; minor sub-elements differ.",
        "",
        "3. Contextual Match (0.30 ≤ Score < 0.50)",
        "   Provides relevant technological context without disclosing the specific mechanism.",
        "",
        "4. Weak Match (0.15 ≤ Score < 0.30)",
        "   Incidental keyword overlap; limited technical correspondence.",
        "",
        "5. No Material Match (Score < 0.15)",
        "   No meaningful technical correspondence in candidate evidence.",
        "",
        "DISCLAIMER: Provides engineering decision support only; does not constitute a legal assessment.",
    ], font_size=10.5, space_after=2)

    # =========================================================================
    # SLIDE 9: THE EVIDENCE MATRIX
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_bg(s9)
    add_header(s9, "The Evidence Matrix: Bridge Between Retrieval and Assessment", "EVIDENCE MATRIX",
               "The Evidence Matrix is the bridge between retrieval and assessment.")

    # Top Concept Card
    add_card(s9, Inches(0.8), Inches(1.65), Inches(11.73), Inches(1.3), title="EVIDENCE MATRIX ARCHITECTURAL ROLE", title_color=GREEN, border_color=BORDER_CYAN)
    add_bullets(s9, Inches(1.0), Inches(2.1), Inches(11.33), Inches(0.75), [
        "\"The Evidence Matrix is the bridge between retrieval and assessment.\"",
        "Every cell in the matrix represents an atomic, verifiable correspondence link: Feature  →  Evidence Relationship  →  Patent Chunk  →  Source.",
        "Assessments are never computed from ungrounded text summaries; they are derived directly from this auditable matrix.",
    ], font_size=11, space_after=3, text_color=OFF_WHITE)

    # 3 Structural Columns Below
    em_w = Inches(3.75)
    em_h = Inches(4.0)

    add_card(s9, xs[0], Inches(3.1), em_w, em_h, title="1. Feature Traceability", title_color=CYAN)
    add_bullets(s9, xs[0] + Inches(0.15), Inches(3.65), em_w - Inches(0.3), Inches(3.3), [
        "• Feature ID (e.g. feat_a1b2c3d4)",
        "• Feature Category (Component, Function, Constraint, etc.)",
        "• Verbatim Feature Text",
        "• Normalized Text",
        "• Document Source Provenance (Chunk index, Section, Claim #, Page #)",
        "• Feature Extraction Confidence",
    ], font_size=10.5, space_after=4)

    add_card(s9, xs[1], Inches(3.1), em_w, em_h, title="2. Evidence Correspondence", title_color=BLUE)
    add_bullets(s9, xs[1] + Inches(0.15), Inches(3.65), em_w - Inches(0.3), Inches(3.3), [
        "• 5-Level Evidence Relationship (Direct, Partial, Contextual, Weak, No Material Match)",
        "• Combined Matching Score (0.4 lex + 0.6 sem)",
        "• Mapping Confidence Score [0.0, 1.0]",
        "• Reranker Alignment & Score",
        "• Retrieval Rank & Method",
    ], font_size=10.5, space_after=4)

    add_card(s9, xs[2], Inches(3.1), em_w, em_h, title="3. Patent Citation Provenance", title_color=PURPLE)
    add_bullets(s9, xs[2] + Inches(0.15), Inches(3.65), em_w - Inches(0.3), Inches(3.3), [
        "• Patent Number (e.g. US-10492811-B2)",
        "• Publication Date & Jurisdiction",
        "• Patent Chunk Index & Section",
        "• Specific Claim Number (if from claims)",
        "• Verbatim Prior-Art Passage Excerpt",
        "• CPC / IPC Classification Codes",
    ], font_size=10.5, space_after=4)

    # =========================================================================
    # SLIDE 10: EB-PRE ENGINE
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_bg(s10)
    add_header(s10, "Evidence-Based Patent Readiness Engine (EB-PRE)", "DETERMINISTIC SCORING ENGINE",
               "Deterministic assessment from structured evidence.")

    # Top Formula Box
    add_card(s10, Inches(0.8), Inches(1.65), Inches(11.73), Inches(1.2), title="DETERMINISTIC READINESS FORMULATION", title_color=GREEN, border_color=BORDER_CYAN)
    add_bullets(s10, Inches(1.0), Inches(2.1), Inches(11.33), Inches(0.65), [
        "Readiness Score = Σ (w_i × S_i) = 0.30×Novelty + 0.20×Overlap + 0.20×Diff + 0.15×Innovation + 0.10×Docs + 0.05×Commercial",
        "where w_i represents the dimension weight (sum = 100%), and S_i represents the normalized evidence score [0.0, 1.0].",
        "CORE TECHNICAL PRINCIPLE: EB-PRE does not depend on the LLM for scoring. Scores are 100% deterministic and mathematically reproducible.",
    ], font_size=10.5, space_after=2, text_color=OFF_WHITE)

    # 6 Dimension Breakdown Cards (3 columns x 2 rows)
    d_w = Inches(3.75)
    d_h = Inches(1.8)
    d_ys = [Inches(3.0), Inches(4.95)]

    add_card(s10, xs[0], d_ys[0], d_w, d_h, title="Novelty — 30%", title_color=CYAN)
    add_bullets(s10, xs[0] + Inches(0.12), d_ys[0] + Inches(0.45), d_w - Inches(0.24), Inches(1.25), [
        "• Measures inverse direct prior-art anticipation.",
        "• Strongly penalizes Direct Matches in corpus.",
        "• High score = low matching density in prior art.",
    ], font_size=10, space_after=2)

    add_card(s10, xs[1], d_ys[0], d_w, d_h, title="Prior-Art Overlap — 20%", title_color=CYAN)
    add_bullets(s10, xs[1] + Inches(0.12), d_ys[0] + Inches(0.45), d_w - Inches(0.24), Inches(1.25), [
        "• Evaluates density and severity of retrieved claims.",
        "• Direct = 4 pts, Partial = 3 pts, Contextual = 2 pts.",
        "• Exposes crowded prior-art technology sectors.",
    ], font_size=10, space_after=2)

    add_card(s10, xs[2], d_ys[0], d_w, d_h, title="Technical Differentiation — 20%", title_color=CYAN)
    add_bullets(s10, xs[2] + Inches(0.12), d_ys[0] + Inches(0.45), d_w - Inches(0.24), Inches(1.25), [
        "• Ratio of novel feature elements to known prior-art.",
        "• Quantifies technical divergence from citations.",
        "• Identifies unique mechanical/functional aspects.",
    ], font_size=10, space_after=2)

    add_card(s10, xs[0], d_ys[1], d_w, d_h, title="Innovation Characteristics — 15%", title_color=BLUE)
    add_bullets(s10, xs[0] + Inches(0.12), d_ys[1] + Inches(0.45), d_w - Inches(0.24), Inches(1.25), [
        "• Structural diversity across feature categories.",
        "• Rewards multi-element system inventions with components, functions, constraints, and mechanisms.",
    ], font_size=10, space_after=2)

    add_card(s10, xs[1], d_ys[1], d_w, d_h, title="Documentation Quality — 10%", title_color=BLUE)
    add_bullets(s10, xs[1] + Inches(0.12), d_ys[1] + Inches(0.45), d_w - Inches(0.24), Inches(1.25), [
        "• Provenance completeness and traceable spans.",
        "• Evaluates clarity, specificity, and parameter boundaries in disclosure text.",
    ], font_size=10, space_after=2)

    add_card(s10, xs[2], d_ys[1], d_w, d_h, title="Commercial Potential — 5%", title_color=BLUE)
    add_bullets(s10, xs[2] + Inches(0.12), d_ys[1] + Inches(0.45), d_w - Inches(0.24), Inches(1.25), [
        "• Presence of technical problem-solution framing, concrete outputs, and practical operational constraints.",
    ], font_size=10, space_after=2)

    cat_banner = s10.shapes.add_textbox(Inches(0.8), Inches(6.9), Inches(11.73), Inches(0.35))
    cat_tf = cat_banner.text_frame
    cat_p = cat_tf.paragraphs[0]
    cat_p.text = "READINESS CATEGORIES:  [0.0 - 0.39] LOW (High Prior-Art Overlap)  |  [0.40 - 0.69] MODERATE (Partial Differentiation)  |  [0.70 - 1.00] HIGH (Strong Differentiation)"
    cat_p.font.name = "Segoe UI"
    cat_p.font.size = Pt(9.5)
    cat_p.font.bold = True
    cat_p.font.color.rgb = CYAN
    cat_p.alignment = PP_ALIGN.CENTER

    # =========================================================================
    # SLIDE 11: CONFIDENCE + UNCERTAINTY
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_bg(s11)
    add_header(s11, "Assessment Confidence & Uncertainty Tracking", "CONFIDENCE & UNCERTAINTY",
               "Decoupling readiness indications from statistical confidence and surfacing explicit risk flags.")

    # Left: Readiness vs Confidence Comparison
    add_card(s11, Inches(0.8), Inches(1.65), Inches(5.7), Inches(5.25), title="DECOUPLING READINESS FROM CONFIDENCE", title_color=CYAN)
    add_bullets(s11, Inches(1.05), Inches(2.2), Inches(5.2), Inches(4.5), [
        "READINESS — \"What does the available evidence indicate?\"",
        "• Computed by EB-PRE across 6 dimensions.",
        "• Reflects the degree of technical divergence from retrieved prior art.",
        "",
        "CONFIDENCE — \"How reliable is that indication?\"",
        "• Evaluates evidence adequacy, coverage breadth, and mapping stability.",
        "• Factors: coverage ratio (35%), mapping confidence (30%), provenance ratio (20%), documentation breadth (15%).",
        "",
        "CRITICAL SAFETY PRINCIPLE:",
        "• High readiness with low confidence indicates an under-searched corpus, NOT proof of novelty.",
        "• \"No retrieved prior art does NOT prove novelty.\"",
        "• The system highlights uncertainty rather than concealing it.",
    ], font_size=10.5, space_after=4)

    # Right: 6 Uncertainty Flags
    add_card(s11, Inches(6.8), Inches(1.65), Inches(5.73), Inches(5.25), title="SIX CANONICAL UNCERTAINTY FLAGS", title_color=AMBER)
    add_bullets(s11, Inches(7.05), Inches(2.2), Inches(5.2), Inches(4.5), [
        "1. insufficient_prior_art_coverage",
        "   Triggered when < 50% of technical features have mapped prior art in corpus.",
        "",
        "2. incomplete_feature_provenance",
        "   Triggered when < 60% of features possess verified document span offsets.",
        "",
        "3. limited_documentation",
        "   Triggered when < 3 distinct technical features are extractable from text.",
        "",
        "4. weak_evidence_support",
        "   Triggered when average mapping confidence across citations is < 0.35.",
        "",
        "5. commercial_information_missing",
        "   Triggered when utility and practical constraint scores fall below 0.30.",
        "",
        "6. direct_prior_art_overlap",
        "   Triggered when one or more features directly match prior-art claims.",
    ], font_size=10.5, space_after=3)

    # =========================================================================
    # SLIDE 12: GROUNDED GEMINI EXPLANATION
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_bg(s12)
    add_header(s12, "Grounded Gemini Explanation & Structured Reporting", "EXPLANATION & REPORTING",
               "Decoupled explanatory generative AI bounded by strict grounding and deterministic fallback.")

    # Left: Architecture Flow
    add_card(s12, Inches(0.8), Inches(1.65), Inches(5.7), Inches(5.25), title="STRICTLY DECOUPLED EXPLANATION ARCHITECTURE", title_color=GREEN)
    add_bullets(s12, Inches(1.05), Inches(2.2), Inches(5.2), Inches(4.5), [
        "Structured Input Context:",
        "  Evidence Matrix + EB-PRE Scores + Confidence + Uncertainty + Provenance",
        "                    ↓",
        "  Gemini 3.1 Pro Preview (REST API / Fenced Prompt)",
        "                    ↓",
        "  Grounded Explanation & 10-Section Report",
        "",
        "CORE ARCHITECTURAL RULE:",
        "\"Gemini explains the structured evidence; it does not calculate or modify the readiness score.\"",
        "",
        "Summary:",
        "• Algorithms calculate.",
        "• Evidence supports.",
        "• Gemini explains.",
    ], font_size=10.5, space_after=4)

    # Right: Anti-Hallucination & Fallback
    add_card(s12, Inches(6.8), Inches(1.65), Inches(5.73), Inches(5.25), title="GROUNDING VALIDATION & DETERMINISTIC FALLBACK", title_color=CYAN)
    add_bullets(s12, Inches(7.05), Inches(2.2), Inches(5.2), Inches(4.5), [
        "Prompt Injection & Hallucination Defense:",
        "• System prompt treats all disclosure text as untrusted data.",
        "• Post-generation validator verifies cited evidence IDs and patent numbers.",
        "• Zero score drift: strictly enforces that reported scores equal EB-PRE scores.",
        "",
        "Deterministic Fallback Mechanism:",
        "• If Gemini API is unavailable or free-tier quota is exhausted (HTTP 429):",
        "  \"If Gemini is unavailable or quota is exhausted, the deterministic fallback report preserves the EB-PRE results.\"",
        "• Generates the full 10-section report using rule-based templates.",
        "• 100% service uptime with zero unhandled exceptions.",
        "",
        "Mandatory Legal Disclaimer:",
        "• Included in all reports: assessment is an engineering decision-support tool, NOT legal advice under 35 U.S.C. §§ 101/102/103/112.",
    ], font_size=10.5, space_after=3)

    # =========================================================================
    # SLIDE 13: EMPIRICAL RESULTS
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    set_bg(s13)
    add_header(s13, "Empirical Results: Benchmarks, Latencies & Verification Metrics", "EMPIRICAL RESULTS (5 MARKS)",
               "Directly addressing the results criterion using verified figures from repository implementation reports.")

    # 6 KPI Metric Cards
    s_x = Inches(0.8)
    kw = Inches(1.8)
    kh = Inches(1.5)
    kgap = Inches(0.18)
    for i, (mval, mlbl, msub, mcol) in enumerate([
        ("171 / 171", "BACKEND TESTS", "100% Suite Pass", GREEN),
        ("PASS", "FRONTEND BUILD", "Vite Client Build", GREEN),
        ("15 Patents", "DEVELOPMENT CORPUS", "Public US Patents", CYAN),
        ("78 Chunks", "PATENT CHUNKS", "Patent-Aware Split", CYAN),
        ("768-D", "BGE EMBEDDINGS", "Cosine Distance", BLUE),
        ("0.19–0.28 ms", "EB-PRE LATENCY", "Deterministic Math", PURPLE),
    ]):
        add_metric_box(s13, s_x + i*(kw+kgap), Inches(1.65), kw, kh, mval, mlbl, msub, val_color=mcol)

    # 2 Comparison Cards Below
    add_card(s13, Inches(0.8), Inches(3.35), Inches(5.7), Inches(3.55), title="VERIFIED ENGINE PERFORMANCE", title_color=CYAN)
    add_bullets(s13, Inches(1.05), Inches(3.85), Inches(5.2), Inches(2.9), [
        "• Full Lifecycle E2E Smoke Test: PASSED (`test_e2e_smoke.py`).",
        "• Pipeline Orchestrator Test: PASSED (`test_pipeline_orchestrator.py`).",
        "• Project CRUD Test: PASSED (`test_projects_api.py`).",
        "• BGE Cross-Encoder Reranker: Tested with batch size 8; top rerank score reached 0.9909.",
        "• Score Preservation: 0.00% drift between EB-PRE math and report layer.",
        "• Scientific Rigor: No invented accuracy, precision, or recall numbers.",
    ], font_size=10, space_after=3)

    add_card(s13, Inches(6.8), Inches(3.35), Inches(5.73), Inches(3.55), title="PERSISTENCE & SCOPE STATUS", title_color=PURPLE)
    add_bullets(s13, Inches(7.05), Inches(3.85), Inches(5.2), Inches(2.9), [
        "Honest Architectural Reporting for Review III:",
        "• Supabase Persistence: Implemented — remote verification pending.",
        "  (Local developer demo store provides complete in-memory persistence fallback).",
        "• Corpus Scope: 15 public US patents in current development corpus.",
        "• Bounded Claim: No worldwide prior-art coverage claim.",
        "• Legal Scope: No legal patentability guarantee; engineering decision support only.",
    ], font_size=10, space_after=3)

    # =========================================================================
    # SLIDE 14: CURRENT STATUS & ROADMAP
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    set_bg(s14)
    add_header(s14, "Implementation Status & Project Roadmap", "STATUS & MILESTONES",
               "Completed Review III baseline vs planned scope for Review IV integration and scale.")

    # Left: Completed
    add_card(s14, Inches(0.8), Inches(1.65), Inches(5.7), Inches(5.25), title="REVIEW III — IMPLEMENTED & TESTED", title_color=GREEN, border_color=BORDER_CYAN)
    add_bullets(s14, Inches(1.05), Inches(2.2), Inches(5.2), Inches(4.5), [
        "✓ FastAPI backend (ASGI endpoints, /api base path)",
        "✓ React + Vite integration (React 19, Tailwind CSS)",
        "✓ Authentication flow (Supabase JWT + Local Demo Mode)",
        "✓ Project CRUD (List, create, get detail, delete)",
        "✓ Document processing (PDF, DOCX, TXT parsers, section detection)",
        "✓ Feature extraction (11 categories with provenance spans)",
        "✓ Hybrid retrieval (BM25 lexical + BGE dense vectors via Qdrant)",
        "✓ RRF fusion (k=60, candidate depth 20)",
        "✓ Cross-encoder reranking (BAAI/bge-reranker-base)",
        "✓ Evidence mapping (0.4 lex + 0.6 sem, 5-level relationships)",
        "✓ Evidence Matrix (Traceable feature-evidence correspondence)",
        "✓ EB-PRE scoring engine (Deterministic 6-dimension scoring)",
        "✓ Confidence & uncertainty (6 canonical risk flags)",
        "✓ Gemini grounded reporting (Gemini 3.1 Pro + fallback)",
        "✓ Persistence layer (Supabase repository + demo store)",
        "✓ 171/171 backend tests passed & frontend production build passed",
        "✓ Full lifecycle E2E automated smoke test passed",
    ], font_size=9.5, space_after=2)

    # Right: Roadmap
    add_card(s14, Inches(6.8), Inches(1.65), Inches(5.73), Inches(5.25), title="REVIEW IV — INTEGRATION & SCALE", title_color=BLUE)
    add_bullets(s14, Inches(7.05), Inches(2.2), Inches(5.2), Inches(4.5), [
        "Planned Work for Final Submission:",
        "→ Remote Supabase configuration and verification",
        "  Connect live cloud database credentials and verify production RLS.",
        "",
        "→ Cloud RLS verification",
        "  Multi-tenant security testing under live multi-user concurrency.",
        "",
        "→ Larger patent corpus expansion",
        "  Scale from 15 sample patents to 1,000+ full-text patent documents.",
        "",
        "→ Production Gemini quota provisioning",
        "  Obtain enterprise/paid API quota to eliminate free-tier 429 throttling.",
        "",
        "→ Larger-scale retrieval evaluation",
        "  Benchmark MRR@10 and Recall@20 against standard patent corpora.",
        "",
        "→ Browser-level manual E2E validation & deployment hardening",
        "  Docker containerization and cloud hosting deployment.",
    ], font_size=9.5, space_after=3)

    # =========================================================================
    # SLIDE 15: CONCLUSION & REFERENCES
    # =========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    set_bg(s15)
    add_header(s15, "Conclusion & Academic Literature References", "SUMMARY & CITATIONS",
               "Summary of accomplishments and foundational literature supporting PatentIQ.")

    # Left: Conclusion
    add_card(s15, Inches(0.8), Inches(1.65), Inches(5.5), Inches(5.25), title="CONCLUSION & KEY TAKEAWAYS", title_color=GREEN, border_color=BORDER_CYAN)
    add_bullets(s15, Inches(1.05), Inches(2.2), Inches(5.0), Inches(4.5), [
        "Core Accomplishment:",
        "\"PatentIQ introduces an evidence-first approach that moves beyond black-box similarity scores toward transparent, feature-level prior-art analysis.\"",
        "",
        "\"PatentIQ connects invention features with prior-art evidence to produce an explainable early-stage patent-readiness assessment.\"",
        "",
        "Final Active Architecture:",
        "Invention  →  Features  →  Prior Art  →  Evidence  →  Assessment  →  Report",
        "",
        "Future Work:",
        "• Larger patent corpus (1,000+ documents)",
        "• Remote Supabase verification and cloud RLS validation",
        "• Browser-level validation and UI testing",
        "• Production-scale retrieval evaluation",
        "• Gemini production quota provisioning",
        "• Expanded empirical evaluation against patent examiner office actions",
    ], font_size=10, space_after=3)

    # Right: Compact References
    add_card(s15, Inches(6.6), Inches(1.65), Inches(5.93), Inches(5.25), title="VERIFIED ACADEMIC REFERENCES", title_color=CYAN, border_color=BORDER_COLOR)
    citations = [
        "1. Vowinckel & Hähnke (2023) - SEARCHFORMER: Prior-Art Patent Search.",
        "2. Higuchi & Yanai (2023) - Patent Retrieval using Transformer Metric Learning.",
        "3. Chikkamath et al. (2024) - Natural Query Understanding for Prior Art Search.",
        "4. Stamatis et al. (2024) - A Novel Re-ranking Architecture for Patent Search.",
        "5. Schmitt & Denter (2024) - Modeling an Indicator for Statutory Patent Novelty.",
        "6. Ali et al. (2024) - Innovating Patent Retrieval: A Comprehensive Review.",
        "7. Siddharth & Luo (2024) - RAG Using Engineering Design Knowledge.",
        "8. Lee & Bai (2025) - PAI-NET: Patent AI Network for Prior-Art Analysis.",
        "9. Yoshikawa & Krestel (2025) - Do LLMs Understand Patents? A Survey.",
        "10. Ding et al. (2025) - Automatic Patent Literature Retrieval based on LLM-RAG.",
        "11. Wang et al. (2025) - Patent Text Similarity with SAO Semantics.",
        "12. Knappich et al. (SIGIR 2026) - Fine-Grained Novelty Prediction on Passages.",
        "13. Robertson & Zaragoza (2009) - The Probabilistic Relevance Framework: BM25.",
        "14. Xiao et al. (2023) - C-Pack: Packaged Resources for General Embeddings (BGE).",
        "15. Cormack et al. (2009) - Reciprocal Rank Fusion outperforms CombMNZ.",
    ]
    add_bullets(s15, Inches(6.8), Inches(2.2), Inches(5.5), Inches(4.5), citations, font_size=9, space_after=3)

    prs.save(output_path)
    print(f"[+] Presentation successfully generated: {output_path}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "PatentIQ B.Tech Review III Presentation.pptx"
    build_review_presentation(out)

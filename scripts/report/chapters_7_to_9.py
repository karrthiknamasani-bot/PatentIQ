"""Chapters 7 to 9 of the PatentIQ B.Tech Project Report:
- Chapter 7: Feature-to-Evidence Mapping and Evidence Matrix
- Chapter 8: Evidence-Based Patent Readiness Engine (EB-PRE)
- Chapter 9: Grounded Explanation Generation and Reporting
"""

import os
from docx.shared import Pt
from styles import (
    FONT_NAME, COLOR_BLACK, add_chapter_heading, add_section_heading,
    add_subsection_heading, add_subsubsection_heading, add_body_p, add_bullet_p,
    add_table_data, add_figure_image
)

FIGURES_DIR = r"C:\Users\karrt\Downloads\PatentIQ\report_figures"


def build_chapters_7_to_9(doc):
    """Generates Chapters 7, 8, and 9."""

    # =========================================================================
    # CHAPTER 7: FEATURE-TO-EVIDENCE MAPPING AND EVIDENCE MATRIX
    # =========================================================================
    doc.add_page_break()
    add_chapter_heading(doc, 7, "Feature-to-Evidence Mapping and Evidence Matrix")

    add_section_heading(doc, "7.1 Controlled Vocabulary of Evidence Relationships")
    add_body_p(
        doc,
        "A cornerstone of PatentIQ is the rigorous categorization of technical correspondence between invention features and prior-art passages. "
        "Rudimentary similarity checkers output continuous cosine numbers (e.g., '0.73 similarity') that are legally meaningless. "
        "In patent law, evidence must be classified into qualitative legal-technical relationships. PatentIQ defines a controlled five-tiered "
        "relationship vocabulary implemented as an enumerated type (EvidenceRelationship in mapping/types.py), detailed in Table 7.1."
    )

    headers_7_1 = ["Relationship Category", "Severity Rank", "Legal-Technical Definition", "Material Overlap Status", "Downstream Scoring Impact"]
    rows_7_1 = [
        ["Direct Match", "Severity 4", "The prior-art passage explicitly discloses the full technical feature, its operating mechanism, and its technical effect.", "YES (Material Overlap)", "Substantially reduces Novelty score; heavily increases Overlap score"],
        ["Partial Match", "Severity 3", "The prior-art passage discloses core structural components or principles of the feature, but omits specific claimed mechanisms.", "YES (Material Overlap)", "Moderately reduces Novelty; contributes to Overlap density"],
        ["Contextual Match", "Severity 2", "The prior-art passage operates in the same general technological domain or problem context without disclosing the inventive mechanism.", "NO (Non-Material)", "Does NOT penalize Novelty; provides background context for explanation"],
        ["Weak Match", "Severity 1", "Incidental lexical co-occurrence or remote analogical overlap without meaningful technical correspondence.", "NO (Non-Material)", "Filtered out; zero impact on Overlap score; logged for auditability"],
        ["No Material Match", "Severity 0", "No technically relevant prior-art disclosure discovered within the searched candidate pool.", "NO (Non-Material)", "Increases Differentiation ratio; triggers uncertainty if coverage is sparse"],
    ]
    col_w_7_1 = [2.2, 1.8, 4.5, 2.5, 2.6]
    add_table_data(doc, "7.1", "Controlled Vocabulary of Evidence Relationships and Severity Scores", headers_7_1, rows_7_1, col_w_7_1)

    add_section_heading(doc, "7.2 Multi-Signal Correspondence Scoring Formulation")
    add_body_p(
        doc,
        "To classify a candidate evidence passage into one of the controlled relationship categories, the EvidenceMapper service computes a composite "
        "multi-signal correspondence score. The score synthesizes dense semantic similarity, sparse lexical keyword overlap, and cross-encoder "
        "neural relevance:",
        bold_prefix="Multi-Signal Mapping Score Formulation: "
    )
    add_body_p(
        doc,
        "Score_Mapping(f_i, p_j) = α • Sim_Dense(f_i, p_j) + β • Sim_Lexical(f_i, p_j) + γ • Score_CrossEncoder(f_i, p_j)\n"
        "where α = 0.35, β = 0.25, and γ = 0.40 represent calibrated component weights summing to 1.0. Sim_Dense is the cosine similarity between the "
        "feature and passage embeddings, Sim_Lexical is the normalized BM25 score, and Score_CrossEncoder is the probability output of the BGE reranker. "
        "Additionally, a categorical compatibility bonus (+0.05) is applied when the patent passage originates from the same technical classification (CPC/IPC) "
        "as the feature category."
    )

    add_section_heading(doc, "7.3 Threshold Calibration and Non-Material Contextual Exclusion")
    add_body_p(
        doc,
        "A critical innovation in PatentIQ is the deliberate exclusion of non-material matches from prior-art overlap penalties. "
        "In many standard AI patent screening tools, any retrieved document with high keyword density is counted against the applicant. "
        "In PatentIQ, correspondence scores are mapped to relationship categories using strict, calibrated numerical thresholds, detailed in Table 7.2."
    )

    headers_7_2 = ["Relationship Category", "Score Range Threshold", "Overlap Criterion", "Exclusion Rationale & Safeguard"]
    rows_7_2 = [
        ["Direct Match", "Score ≥ 0.75", "Material Prior Art Overlap", "High-confidence structural and functional anticipation; directly impacts novelty"],
        ["Partial Match", "0.50 ≤ Score < 0.75", "Material Prior Art Overlap", "Substantial component overlap; indicates need for technical claim narrowing"],
        ["Contextual Match", "0.30 ≤ Score < 0.50", "Excluded (Non-Material)", "Common domain background; strictly excluded from prior-art overlap penalties"],
        ["Weak Match", "0.15 ≤ Score < 0.30", "Excluded (Non-Material)", "Incidental keyword match; discarded from quantitative readiness evaluation"],
        ["No Material Match", "Score < 0.15", "Excluded (Non-Material)", "Complete technical divergence; treated as unencumbered technical feature space"],
    ]
    col_w_7_2 = [2.5, 2.5, 3.2, 5.4]
    add_table_data(doc, "7.2", "Multi-Signal Mapping Thresholds and Correspondence Classifications", headers_7_2, rows_7_2, col_w_7_2)

    add_section_heading(doc, "7.4 Two-Dimensional Evidence Matrix Architecture")
    add_body_p(
        doc,
        "The classified mappings are synthesized into a two-dimensional relational data structure termed the Feature-to-Prior-Art Evidence Matrix. "
        "Figure 7.1 illustrates the structural layout of the Evidence Matrix."
    )

    fig_7_1_path = os.path.join(FIGURES_DIR, "fig_evidence_matrix.png")
    if os.path.exists(fig_7_1_path):
        add_figure_image(doc, fig_7_1_path, "7.1", "Feature-to-Prior-Art Evidence Matrix Conceptual Architecture", width_cm=14.5)

    add_body_p(
        doc,
        "In the Evidence Matrix, rows represent the applicant's extracted TechnicalFeature entities (F_1, F_2, ..., F_m), while columns represent "
        "the unique prior-art patent publications (P_1, P_2, ..., P_n) retrieved from the corpus. Each intersecting cell C(i, j) contains an EvidenceMatrixCell "
        "object that encapsulates: (1) The verbatim excerpted prior-art passage text; (2) The patent publication number, claim number, and page number; "
        "(3) The assigned evidence relationship category; (4) The multi-signal evidence strength score; and (5) The mapping confidence score. "
        "Cells exhibiting Direct or Partial matches are highlighted as material prior-art collision zones, while unencumbered cells demonstrate clear differentiation."
    )

    add_section_heading(doc, "7.5 Granular Provenance Chains and Auditability")
    add_body_p(
        doc,
        "Every cell in the Evidence Matrix maintains a complete cryptographic and relational audit trail. In the database layer, each evidence item "
        "stores project_id, feature_id, patent_id, retrieved_source, claim_number, and verbatim chunk_text. This immutable bidirectional provenance "
        "enables patent attorneys and examining officers to immediately verify the physical source document for any claimed collision, eliminating black-box ambiguity."
    )

    # =========================================================================
    # CHAPTER 8: EVIDENCE-BASED PATENT READINESS ENGINE (EB-PRE)
    # =========================================================================
    doc.add_page_break()
    add_chapter_heading(doc, 8, "Evidence-Based Patent Readiness Engine (EB-PRE)")

    add_section_heading(doc, "8.1 Mathematical Formalism of EB-PRE Scoring")
    add_body_p(
        doc,
        "The Evidence-Based Patent Readiness Engine (EB-PRE) is the deterministic algorithmic core of PatentIQ. It processes the Evidence Matrix "
        "and extracted feature representations to compute an overall Patent Readiness Score (PRS ∈ [0, 100]) alongside an independent Assessment "
        "Confidence Score (ACS ∈ [0.0, 1.0]). The engine evaluates six orthogonal assessment dimensions, illustrated in Figure 8.1."
    )

    fig_8_1_path = os.path.join(FIGURES_DIR, "fig_eb_pre_weights.png")
    if os.path.exists(fig_8_1_path):
        add_figure_image(doc, fig_8_1_path, "8.1", "Six-Dimensional EB-PRE Scoring Weight Distribution", width_cm=14.5)

    add_body_p(
        doc,
        "The overall Patent Readiness Score is computed as a strictly bounded linear combination of the six dimension scores:",
        bold_prefix="Aggregated Readiness Score Formulation: "
    )
    add_body_p(
        doc,
        "PRS = round( 100 • ∑ [ w_d • S_d ] )   for d ∈ {1, 2, ..., 6}\n"
        "where S_d ∈ [0.0, 1.0] represents the normalized score for dimension d, and w_d represents the calibrated dimension weight. "
        "Table 8.1 details the six dimensions, their exact implemented weights in the codebase, and their mathematical roles."
    )

    headers_8_1 = ["Dimension Name", "Symbol", "Code Weight", "Percentage", "Evaluated Technical Property", "Mathematical Formulation Summary"]
    rows_8_1 = [
        ["Feature Novelty", "S_nov", "settings.READINESS_WEIGHT_NOVELTY", "30%", "Absence of direct/partial anticipatory disclosures across features", "S_nov = (1 / |F|) • ∑ [ 1.0 - SeverityPenalty(f_i) ]"],
        ["Prior-Art Overlap", "S_ovl", "settings.READINESS_WEIGHT_PRIOR_ART_OVERLAP", "20%", "Inverse concentration of material matching evidence passages", "S_ovl = 1.0 - min(1.0, (N_direct + 0.6•N_partial) / (|F| • 1.5))"],
        ["Technical Differentiation", "S_dif", "settings.READINESS_WEIGHT_TECH_DIFFERENTIATION", "20%", "Proportion of technical features exhibiting unique mechanisms", "S_dif = |F_unencumbered| / |F_total|"],
        ["Innovation Characteristics", "S_inn", "settings.READINESS_WEIGHT_INNOVATION_CHARS", "15%", "Complexity, synergistic interaction, and inventive step indicators", "S_inn = 0.5•Score_Interaction + 0.5•Score_Complexity"],
        ["Documentation Quality", "S_doc", "settings.READINESS_WEIGHT_DOC_QUALITY", "10%", "Structural completeness, claim clarity, and technical specificity", "S_doc = 0.4•S_structure + 0.3•S_clarity + 0.3•S_completeness"],
        ["Commercial Potential", "S_com", "settings.READINESS_WEIGHT_COMMERCIAL_POTENTIAL", "5%", "Identified industrial application, market utility, and scalability", "S_com = 0.6•S_applicability + 0.4•S_breadth"],
    ]
    col_w_8_1 = [2.2, 1.0, 3.2, 1.2, 3.0, 3.0]
    add_table_data(doc, "8.1", "Six Assessment Dimensions of the EB-PRE Scoring Engine and Weights", headers_8_1, rows_8_1, col_w_8_1)

    add_section_heading(doc, "8.2 Dimension 1: Feature Novelty Score (30% Weight)")
    add_body_p(
        doc,
        "The Feature Novelty dimension evaluates whether the applicant's technical features are individually anticipated by prior art. "
        "For each feature f_i, the engine inspects its mapped evidence cells and identifies the maximum relationship severity. Direct matches incur a severe "
        "penalty (1.0 - 0.90 = 0.10 novelty), Partial matches incur a moderate penalty (1.0 - 0.55 = 0.45 novelty), while Contextual matches incur no penalty. "
        "Crucially, if a feature has zero retrieved prior-art candidates in the corpus, the engine does NOT award an unearned 1.0 score; instead, it conservatively "
        "anchors the feature novelty at 0.60 and triggers an uncertainty flag ('insufficient_prior_art_coverage'). This directly enforces the principle that "
        "absence of retrieved evidence does not prove novelty."
    )

    add_section_heading(doc, "8.3 Dimension 2: Prior-Art Overlap Density (20% Weight)")
    add_body_p(
        doc,
        "While Novelty evaluates features individually, Prior-Art Overlap Density evaluates the systemic concentration of adverse prior art. "
        "If multiple prior patents each disclose parts of the applicant's invention, the invention faces high risk under obviousness / inventive step "
        "invalidation (35 U.S.C. § 103). The overlap score penalizes dense clusters of direct and partial matches across the Evidence Matrix while "
        "ignoring benign contextual background passages."
    )

    add_section_heading(doc, "8.4 Dimension 3: Technical Differentiation Ratio (20% Weight)")
    add_body_p(
        doc,
        "Technical Differentiation quantifies the ratio of the invention's features that remain completely unencumbered by prior-art collisions. "
        "A feature is classified as unencumbered if its mapped prior-art candidates exhibit only Contextual, Weak, or No Match relationships. "
        "High differentiation indicates a strong inventive core around which robust, defensible patent claims can be constructed."
    )

    add_section_heading(doc, "8.5 Dimension 4: Innovation Characteristics (15% Weight)")
    add_body_p(
        doc,
        "The Innovation Characteristics dimension evaluates the structural sophistication of the invention. It analyzes whether the decomposed features "
        "exhibit synergistic functional interdependencies (where component A modifies the operational state of mechanism B) or represent a mere aggregation "
        "of known elements. Synergistic technical interactions receive high innovation ratings."
    )

    add_section_heading(doc, "8.6 Dimension 5: Documentation Quality and Completeness (10% Weight)")
    add_body_p(
        doc,
        "Even a highly novel invention will be rejected by patent examiners under statutory enablement rules (35 U.S.C. § 112) if the description is vague, "
        "incomplete, or lacks enabling technical details. The Documentation Quality dimension evaluates structural section presence, vocabulary precision, "
        "claim-like structural phrasing, and parametric specificity, providing feedback on disclosure readiness."
    )

    add_section_heading(doc, "8.7 Dimension 6: Commercial and Industrial Potential (5% Weight)")
    add_body_p(
        doc,
        "Allocated a 5% weighting, this dimension inspects the invention disclosure for explicit statements of industrial utility, target deployment "
        "environments, manufacturing scalability, and economic value proposition, aligning with statutory utility requirements."
    )

    add_section_heading(doc, "8.8 Readiness Score vs Readiness Category Mapping")
    add_body_p(
        doc,
        "The aggregated Patent Readiness Score (0 to 100) is translated into four calibrated qualitative readiness categories, detailed in Table 8.2."
    )

    headers_8_2 = ["Readiness Category", "Score Range", "Qualitative Assessment Interpretation", "Prescribed Inventor Action Directive"]
    rows_8_2 = [
        ["High Readiness", "Score ≥ 75", "Substantial novelty, clear technical differentiation, and strong documentation. Minimal prior-art overlap.", "Proceed to formal professional patent drafting; focus claims on differentiated features."],
        ["Moderate Readiness", "60 ≤ Score < 75", "Core novelty present, but significant partial overlap detected. Invention requires technical refinement.", "Narrow independent claims; emphasize specific mechanisms distinguishing over identified prior art."],
        ["Needs Differentiation", "45 ≤ Score < 60", "Extensive prior-art collisions detected. High risk of examiner anticipation or obviousness rejection.", "Restructure invention; pivot core technical mechanism away from identified patent families."],
        ["Early Stage / Conceptual", "Score < 45", "Incomplete documentation, high overlap, or conceptual ambiguity. Lacks statutory enablement.", "Conduct further laboratory experimentation; strengthen technical disclosure before filing."],
    ]
    col_w_8_2 = [2.5, 2.0, 4.5, 4.6]
    add_table_data(doc, "8.2", "Readiness Category Thresholds, Qualitative Interpretations, and Action Rules", headers_8_2, rows_8_2, col_w_8_2)

    add_section_heading(doc, "8.9 Assessment Confidence Calculation and Uncertainty Flags")
    add_body_p(
        doc,
        "A vital theoretical contribution of PatentIQ is the absolute mathematical decoupling of the Patent Readiness Score from the Assessment Confidence Score. "
        "Figure 8.2 illustrates this two-dimensional relationship matrix. An invention may receive a high readiness score (e.g., 85/100) because no prior art was found, "
        "yet have a low confidence score (e.g., 0.35) because the development corpus lacks patents in that specific technical classification. "
        "Whenever confidence falls below calibrated thresholds, EB-PRE emits explicit Uncertainty Flags, detailed in Table 8.3."
    )

    fig_8_2_path = os.path.join(FIGURES_DIR, "fig_eb_pre_weights.png")
    # Reference visual

    headers_8_3 = ["Uncertainty Flag Key", "Trigger Condition", "Underlying Risk & Theoretical Rationale", "Actionable User Guidance"]
    rows_8_3 = [
        ["insufficient_prior_art_coverage", "Fewer than 3 prior-art candidates retrieved across feature set", "Search space too narrow; danger of negative proof fallacy", "Expand retrieval query; search external international patent databases"],
        ["unsearched_feature_space", "One or more features have zero candidate matches in corpus", "Specific inventive feature completely unverified against prior art", "Conduct targeted keyword search for unsearched technical element"],
        ["low_retrieval_confidence", "Average reranker score of candidate pool < 0.30", "Retrieved documents have low semantic relevance to disclosure", "Refine technical feature descriptions; incorporate standard patent terminology"],
        ["potential_claim_overlap", "Direct match detected in independent claim passage", "Severe legal anticipation risk under 35 U.S.C. § 102", "Consult registered patent counsel immediately to review cited claim"],
        ["ambiguous_technical_disclosure", "Documentation Quality score < 0.40", "Invention description lacks statutory enablement details", "Add detailed implementation diagrams, algorithms, and parametric examples"],
    ]
    col_w_8_3 = [2.5, 2.8, 4.2, 4.1]
    add_table_data(doc, "8.3", "Uncertainty Flags, Trigger Criteria, and Remediation Directives", headers_8_3, rows_8_3, col_w_8_3)

    # =========================================================================
    # CHAPTER 9: GROUNDED EXPLANATION GENERATION AND REPORTING
    # =========================================================================
    doc.add_page_break()
    add_chapter_heading(doc, 9, "Grounded Explanation Generation and Reporting")

    add_section_heading(doc, "9.1 Grounded RAG Architecture via Gemini 2.5 Pro")
    add_body_p(
        doc,
        "The explanation tier of PatentIQ utilizes Google's state-of-the-art language model, Gemini 2.5 Pro, operating within a strictly "
        "constrained Retrieval-Augmented Generation (RAG) framework. Figure 9.1 illustrates the grounded RAG architecture, highlighting the "
        "bidirectional flow between pre-calculated EB-PRE scores, constrained prompt assembly, and the deterministic fallback engine."
    )

    fig_9_1_path = os.path.join(FIGURES_DIR, "fig_rag_guardrails.png")
    if os.path.exists(fig_9_1_path):
        add_figure_image(doc, fig_9_1_path, "9.1", "Grounded Gemini RAG Explanation Architecture and Anti-Hallucination Guardrails", width_cm=14.5)

    add_body_p(
        doc,
        "In PatentIQ, Gemini is never asked: 'Is this invention patentable?'. Such an unconstrained prompt invites legal hallucination. "
        "Instead, the prompt assembler constructs a structured payload containing: (1) The verbatim technical features extracted from the invention; "
        "(2) The exact cells of the Evidence Matrix, including patent numbers, claim numbers, and excerpted text; (3) The pre-calculated EB-PRE scores "
        "and readiness category; and (4) The active uncertainty flags. The model is instructed through strict system instructions to synthesize an "
        "executive summary and tactical differentiation recommendations that explain the empirical evidence without altering any numerical values."
    )

    add_section_heading(doc, "9.2 Anti-Hallucination Prompt Constraints and Guardrails")
    add_body_p(
        doc,
        "To enforce legal defensibility and eliminate hallucinations, the Gemini prompt implements four inviolable architectural guardrails: "
        "(1) Numerical Immutability: The prompt explicitly forbids the model from recalculating or modifying readiness scores. Scores must be quoted verbatim "
        "from the provided context; "
        "(2) Strict Evidence Boundary: The model is barred from citing external patents or inventing publication numbers not present in the supplied Evidence Matrix. "
        "If a feature has no matching evidence, the model must explicitly state that no prior art was found within the corpus; "
        "(3) Non-Legal Advisory Disclaimer: The prompt instructs the model to frame all conclusions as early-stage technical decision support rather than formal legal advice; and "
        "(4) Structured JSON / Markdown Schema Enforcement: The model outputs structured sections adhering strictly to a predefined schema."
    )

    add_section_heading(doc, "9.3 Gemini API Quota Management and Deterministic Fallback Mode")
    add_body_p(
        doc,
        "Commercial cloud LLM APIs are subject to transient rate limits, token quota exhaustion (HTTP 429), and network latencies. "
        "A production-grade system cannot crash when an external API fails. PatentIQ implements an active Quota Watchdog and Deterministic Fallback Mode. "
        "If the Gemini API returns a 429 quota exception or times out after 30 seconds, the orchestrator immediately invokes the algorithmic fallback generator. "
        "The fallback engine synthesizes a comprehensive report using rule-based templates directly populated with Evidence Matrix cells and dimension scores. "
        "The report metadata records 'model_used: deterministic_fallback', ensuring complete transparency while maintaining 100% operational uptime."
    )

    add_section_heading(doc, "9.4 Ten-Section Comprehensive Assessment Report Structure")
    add_body_p(
        doc,
        "The final deliverable generated by PatentIQ is a comprehensive 10-section Patent Readiness Report. Table 9.1 outlines the ten standardized "
        "sections and their evidentiary content."
    )

    headers_9_1 = ["Section No.", "Report Section Title", "Evidentiary Contents & Analytical Depth", "Primary Audience"]
    rows_9_1 = [
        ["Section 1", "Executive Summary", "High-level invention overview, aggregated readiness score (0-100), and readiness category", "Inventor, TTO Director, Executive"],
        ["Section 2", "Invention Feature Deconstruction", "Structured table of extracted features across problem, component, mechanism, and effect", "Inventor, Patent Attorney"],
        ["Section 3", "Multi-Dimensional Readiness Profile", "Detailed radar breakdown of the 6 EB-PRE dimensions with individual scores and weights", "Inventor, Technical Reviewer"],
        ["Section 4", "Feature-to-Prior-Art Evidence Matrix", "Full 2D tabular matrix displaying all features mapped against cited prior-art patents", "Patent Agent, Examining Officer"],
        ["Section 5", "Critical Prior-Art Collision Analysis", "In-depth passage-by-passage review of Direct and Partial matches with verbatim excerpts", "Patent Attorney, Inventor"],
        ["Section 6", "Technical Differentiation Opportunities", "Analysis of unencumbered features offering promising avenues for defensible claim drafting", "Patent Drafter, Inventor"],
        ["Section 7", "Assessment Confidence & Uncertainty Flags", "Explicit confidence score (0.0-1.0) and detailed analysis of triggered uncertainty flags", "TTO Auditor, IP Counsel"],
        ["Section 8", "Documentation Quality & Enablement Review", "Constructive audit of description completeness, claim clarity, and statutory enablement gaps", "Inventor, Technical Writer"],
        ["Section 9", "Tactical Filing Recommendations", "Prioritized action items: claim narrowing, additional prior-art searches, or drafting next steps", "Inventor, TTO Officer"],
        ["Section 10", "Methodology & Legal Disclaimers", "Formal statement of algorithmic methodology, development corpus scope, and statutory legal limits", "Legal / Compliance Officers"],
    ]
    col_w_9_1 = [1.5, 3.2, 6.5, 2.4]
    add_table_data(doc, "9.1", "Ten-Section Structure of the Grounded Patent Readiness Report", headers_9_1, rows_9_1, col_w_9_1)

    add_section_heading(doc, "9.5 Multi-Format Report Export")
    add_body_p(
        doc,
        "To serve diverse operational workflows, PatentIQ generates reports in three distinct formats: "
        "(1) Interactive Web Dashboard: Dynamic rendering within the React 19 interface with expandable evidence cells, radar charts, and interactive filtering; "
        "(2) Machine-Readable JSON: Full serialized data contracts containing all raw scores, vectors, cell mappings, and flags for programmatic TTO integration; and "
        "(3) Formal PDF Report: Beautifully styled academic PDF generated via ReportLab / PyMuPDF suitable for formal filing reviews and grant applications."
    )

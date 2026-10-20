"""Chapters 1 to 3 of the PatentIQ B.Tech Project Report:
- Chapter 1: Introduction
- Chapter 2: Literature Review and Theoretical Background
- Chapter 3: Requirements Analysis and System Specifications
"""

from docx.shared import Pt
from docx.enum.section import WD_SECTION_START
from styles import (
    FONT_NAME, COLOR_BLACK, set_section_margins, set_section_numbering_format,
    add_chapter_heading, add_section_heading, add_subsection_heading, add_subsubsection_heading,
    add_body_p, add_bullet_p, add_table_data, add_figure_image
)


def build_chapters_1_to_3(doc):
    """Generates Chapters 1, 2, and 3 with Arabic page numbering starting at 1."""
    # Start Chapter 1 in a new section with Arabic page numbers
    sec = doc.add_section(WD_SECTION_START.NEW_PAGE)
    set_section_margins(sec, left_cm=3.81, right_cm=2.54, top_cm=2.54, bottom_cm=2.54)
    sec.header.is_linked_to_previous = False
    sec.footer.is_linked_to_previous = False
    set_section_numbering_format(sec, fmt="decimal", start=1)

    p_ft = sec.footer.paragraphs[0]
    p_ft.alignment = 1  # Center
    from styles import add_page_number
    add_page_number(p_ft.add_run())

    # =========================================================================
    # CHAPTER 1: INTRODUCTION
    # =========================================================================
    add_chapter_heading(doc, 1, "Introduction")

    add_section_heading(doc, "1.1 Background and Problem Context")
    add_body_p(
        doc,
        "Intellectual property represents one of the foundational drivers of global technical advancement, academic scholarship, "
        "and industrial competitiveness. Across modern university research laboratories, engineering institutions, and technology "
        "incubators, substantial technical research is conducted daily. However, transforming an inventive technical concept into a legally "
        "defensible patent application requires a comprehensive assessment of prior art—the vast historical corpus of publicly disclosed "
        "patents, applications, and technical publications. Prior-art screening is an essential preliminary obligation: it determines whether "
        "a proposed technical disclosure satisfies the statutory patentability criteria of novelty and non-obviousness (inventive step) under "
        "international patent law statutes such as Title 35 of the United States Code (35 U.S.C. §§ 102, 103) and corresponding frameworks under "
        "the European Patent Convention (EPC) and the Indian Patents Act, 1970."
    )
    add_body_p(
        doc,
        "Historically, conducting a thorough prior-art search has been the exclusive domain of specialized patent attorneys, registered "
        "patent agents, and institutional information professionals. A comprehensive professional patent search mandates constructing complex "
        "Boolean query expressions, navigating hierarchical patent classification taxonomies such as the International Patent Classification (IPC) "
        "and Cooperative Patent Classification (CPC), inspecting forward and backward citation graphs, and manually reading hundreds of legal claims. "
        "For student researchers, early-stage faculty inventors, and resource-constrained startups, the prohibitive cost of formal patentability audits—often "
        "ranging from several thousand dollars per invention disclosure—creates a formidable economic barrier. Consequently, high-potential innovations "
        "are frequently abandoned without filing, or conversely, premature and flawed applications are submitted, resulting in costly examiner rejections, "
        "prolonged office action disputes, and substantial financial losses."
    )

    add_section_heading(doc, "1.2 Challenges in Academic and Early-Stage Patent Screening")
    add_body_p(
        doc,
        "The challenges encountered during early-stage invention screening can be deconstructed into four acute structural deficiencies that "
        "impede both traditional information retrieval techniques and naive artificial intelligence applications:"
    )
    add_bullet_p(
        doc,
        "1. Lexical Disconnect and Vocabulary Mismatch:",
        "Patent drafting relies on specialized, highly defensive legal-technical jargon designed to maximize claim breadth while obscuring direct keyword "
        "matches. For example, an invention describing a 'smartphone fingerprint scanner' may appear in patent literature as a 'biometric authentication "
        "aperture disposed adjacent to an interactive capacitive display substrate'. Conventional lexical search tools relying solely on TF-IDF or "
        "uncalibrated BM25 frequently suffer from severe vocabulary mismatch, returning false negatives for conceptually identical prior art while returning "
        "voluminous false positives based on incidental keyword overlap."
    )
    add_bullet_p(
        doc,
        "2. Coarse Document-Level Similarity vs. Fine-Grained Claim Overlap:",
        "Standard dense semantic vector search computes document-level or abstract-level cosine similarity. However, patent law evaluates novelty "
        "element-by-element against specific claims. A retrieved patent document may share 85% high-level thematic similarity with an invention disclosure "
        "(e.g., both operate in autonomous vehicle navigation) without disclosing the specific inventive technical mechanism (e.g., a novel optical sensor "
        "calibration method). Conversely, a prior patent may share only 30% overall document similarity but anticipate 100% of the applicant's core inventive "
        "feature within a single paragraph. Coarse vector similarity checkers cannot distinguish thematic background from lethal anticipatory prior art."
    )
    add_bullet_p(
        doc,
        "3. The Hallucination Hazard of Unconstrained Generative AI:",
        "The widespread emergence of general-purpose Large Language Models (LLMs) has prompted inventors to query commercial chatbots regarding "
        "patentability. This practice is perilous. Standard LLMs hallucinate non-existent patent publication numbers, invent fabricated technical claims, "
        "conflate disparate patent families, and emit arbitrary numerical 'patentability scores' with zero mathematical grounding or passage traceability. "
        "Such unconstrained generations introduce severe legal liability and give inventors false confidence."
    )
    add_bullet_p(
        doc,
        "4. The Fallacy of Negative Proof (Absence of Evidence is Not Evidence of Absence):",
        "A critical conceptual failure in algorithmic novelty screening is assuming that if an automated search retrieves no matching documents, the invention "
        "is definitively novel. In truth, zero retrieved matches often indicate an unsearched patent classification, an inadequate corpus boundary, or "
        "sub-optimal retrieval formulation. An authentic assessment system must explicitly quantify assessment confidence and raise uncertainty flags rather "
        "than granting an unearned 100% novelty rating."
    )

    add_section_heading(doc, "1.3 Problem Statement and Research Questions")
    add_body_p(
        doc,
        "Existing prior-art discovery tools and AI applications fail to provide a mathematically rigorous, evidence-traceable, and legally defensive "
        "pre-filing evaluation framework for technical inventions. Therefore, the central problem addressed by this thesis is formulated as follows:",
        bold_prefix="Problem Statement: "
    )
    add_body_p(
        doc,
        "“How can an intelligent decision-support system automatically deconstruct an unstructured technical invention document into discrete technical features, "
        "retrieve and rerank highly relevant prior-art patent passages using complementary multi-channel representations, map passage-level evidence into a "
        "two-dimensional verification matrix, deterministically calculate multi-dimensional patent readiness metrics with explicit confidence and uncertainty quantification, "
        "and generate grounded, audit-ready explanations without generative hallucination?”",
        italic_prefix="Formal Formulation: "
    )
    add_body_p(doc, "To resolve this central problem, the research addresses the following four operational research questions (RQs):")
    add_bullet_p(
        doc,
        "RQ1 (Feature Deconstruction & Hybrid Retrieval):",
        "How effectively can an invention disclosure be decomposed into traceable technical features across problem, component, mechanism, and effect categories, "
        "and retrieved through a hybrid pipeline combining sparse BM25 lexical matching, dense BGE semantic vectors, Reciprocal Rank Fusion, and cross-encoder reranking?"
    )
    add_bullet_p(
        doc,
        "RQ2 (Evidence Mapping & Overlap Discrimination):",
        "What multi-signal scoring mechanisms reliably discriminate between genuine material prior-art overlap (direct and partial feature matches) and benign "
        "contextual or weak background disclosures across passage-level patent texts?"
    )
    add_bullet_p(
        doc,
        "RQ3 (Deterministic Readiness Modeling):",
        "Can a multi-dimensional algorithmic engine (EB-PRE) deterministically compute an aggregated patent-readiness indication across six weighted dimensions "
        "(Novelty, Prior-Art Overlap, Differentiation, Innovation, Documentation Quality, Commercial Potential) while mathematically decoupling readiness from confidence?"
    )
    add_bullet_p(
        doc,
        "RQ4 (Grounded Generative Explanation & Persistence):",
        "How can generative language models be strictly constrained via prompt engineering and fallback safeguards to explain pre-calculated evidence rather than "
        "invent scores, ensuring persistent multi-tenant security and auditable reproducibility?"
    )

    add_section_heading(doc, "1.4 Project Objectives")
    add_body_p(doc, "To answer these research questions, the PatentIQ system was engineered around five foundational technical objectives:")
    add_bullet_p(
        doc,
        "Objective 1: Multi-Format Ingestion and Patent-Aware Chunking —",
        "Develop an automated ingestion engine supporting PDF, DOCX, and plain text formats that validates document structure, sanitizes input streams, "
        "and implements patent-aware chunking preserving paragraph boundaries and claim references."
    )
    add_bullet_p(
        doc,
        "Objective 2: Hybrid Retrieval and Cross-Encoder Neural Reranking —",
        "Implement a dual-channel retrieval architecture integrating dense BGE vector search on Qdrant with sparse Okapi BM25 keyword matching, fused via "
        "Reciprocal Rank Fusion (RRF, k=60) and reranked using the BAAI/bge-reranker-base cross-encoder model."
    )
    add_bullet_p(
        doc,
        "Objective 3: Evidence Matrix and Controlled Severity Mapping —",
        "Establish an evidence-mapping algorithm that classifies feature-to-patent correspondences across five controlled severities (direct match, partial match, "
        "contextual match, weak match, and no material match) into a two-dimensional Feature-to-Prior-Art Evidence Matrix."
    )
    add_bullet_p(
        doc,
        "Objective 4: Deterministic Evidence-Based Patent Readiness Engine (EB-PRE) —",
        "Formulate and calibrate the EB-PRE scoring engine across six validated research dimensions with exact weight distribution, rigorous score-confidence "
        "decoupling, and automated uncertainty flag generation."
    )
    add_bullet_p(
        doc,
        "Objective 5: Grounded Explanation Generation, Relational Persistence, and Modern Web Interface —",
        "Deploy Gemini 2.5 Pro under strict anti-hallucination prompt boundaries with automated deterministic fallback on API quota exhaustion; persist all entities "
        "in Supabase PostgreSQL under strict Row Level Security; and deliver an interactive React 19 + Vite dashboard."
    )

    add_section_heading(doc, "1.5 Core Guiding Principle: Algorithms Calculate, Evidence Supports, Gemini Explains")
    add_body_p(
        doc,
        "The philosophical and engineering core of PatentIQ is encapsulated in a strict architectural maxim that governs all information processing:",
        bold_prefix="The PatentIQ Tenet: "
    )
    add_body_p(
        doc,
        "“Algorithms calculate. Evidence supports. Gemini explains.”",
        italic_prefix="Guiding Maxim: "
    )
    add_body_p(
        doc,
        "This principle enforces strict separation of responsibilities across the system components: "
        "(1) Algorithmic Determinism: Readiness scores, dimension ratings, feature confidence values, and uncertainty flags are strictly computed by deterministic "
        "mathematical algorithms executing in FastAPI. The Large Language Model is never permitted to calculate, adjust, or generate numerical readiness metrics. "
        "(2) Verifiable Evidence Grounding: Every metric computed by the engine is anchored to traceable passages excerpted verbatim from retrieved prior-art patents "
        "and stored in the Evidence Matrix. (3) Constrained Generative Synthesis: The generative model (Gemini 2.5 Pro) functions solely as an articulate technical "
        "communicator. It translates complex mathematical matrix relationships into structured, human-readable executive summaries, tactical differentiation advice, "
        "and transparent explanations strictly constrained to the retrieved evidence."
    )

    add_section_heading(doc, "1.6 Scope, Boundaries, and Operational Delimitations")
    add_body_p(
        doc,
        "To establish academic integrity and legal defensibility, the scope of PatentIQ is explicitly delimited by the following operational boundaries:"
    )
    add_bullet_p(
        doc,
        "Decision-Support, Not Legal Patentability Determination:",
        "PatentIQ is an early-stage screening, research-acceleration, and decision-support tool. It does not provide legal advice, does not establish formal legal "
        "patentability, and does not replace the statutory examination conducted by authorized government patent offices (such as the USPTO, EPO, or Indian Patent Office)."
    )
    add_bullet_p(
        doc,
        "Development Corpus Boundary:",
        "The current verified implementation operates over a curated development corpus of 15 public US patents encompassing 78 granular claim and description chunks. "
        "While architecturally scalable to millions of documents on Qdrant, results documented in this report reflect this calibrated reference dataset."
    )
    add_bullet_p(
        doc,
        "Language Delimitation:",
        "The current retrieval and embedding models (BAAI/bge-base-en-v1.5 and BM25 tokenizers) are calibrated for English-language patent disclosures. Multilingual "
        "patent families (e.g., Japanese, Chinese, or German disclosures) are outside the current primary scope."
    )

    add_section_heading(doc, "1.7 Organization of the Report")
    add_body_p(
        doc,
        "The remainder of this project report is structured into twelve thematic chapters that comprehensively document the engineering lifecycle of PatentIQ:\n"
        "Chapter 2 reviews foundational academic literature across neural patent retrieval, RAG, and XAI, synthesizing 15 key research works into a comparative matrix. "
        "Chapter 3 defines the functional and non-functional system specifications and justifies the locked technology stack. "
        "Chapter 4 details the end-to-end layered architecture, data pipeline, and multi-tenant security model. "
        "Chapter 5 explains multi-format document ingestion, patent-aware chunking, and technical feature deconstruction. "
        "Chapter 6 presents the dual-channel hybrid retrieval pipeline, Reciprocal Rank Fusion, and cross-encoder neural reranking. "
        "Chapter 7 specifies the controlled evidence relationship vocabulary and two-dimensional Evidence Matrix architecture. "
        "Chapter 8 establishes the mathematical formalism and dimension formulations of the Evidence-Based Patent Readiness Engine (EB-PRE). "
        "Chapter 9 details Gemini 2.5 Pro grounded explanation generation, prompt guardrails, and deterministic fallback mode. "
        "Chapter 10 discusses the Supabase PostgreSQL relational schema, Row Level Security policies, and persistence layer. "
        "Chapter 11 presents the React 19 frontend design and REST API integration contracts. "
        "Chapter 12 provides comprehensive experimental results, automated test suite verifications, latency profiling, and ablation analysis. "
        "Chapter 13 concludes the thesis with key insights, realized performance achievements, threats to validity, and future research directions."
    )

    # =========================================================================
    # CHAPTER 2: LITERATURE REVIEW AND THEORETICAL BACKGROUND
    # =========================================================================
    doc.add_page_break()
    add_chapter_heading(doc, 2, "Literature Review and Theoretical Foundations")

    add_section_heading(doc, "2.1 Evolution of Patent Retrieval Systems")
    add_body_p(
        doc,
        "Patent Information Retrieval (PIR) has evolved through distinct technological epochs over the past four decades. Early computational patent "
        "search systems in the 1980s and 1990s relied exclusively on exact Boolean matching combined with manual hierarchical classification codes "
        "(Salton & McGill, 1983; Croft et al., 2010). Professional patent searchers constructed highly elaborate query strings featuring nested AND/OR operators, "
        "wildcards, and field-specific filters (e.g., restricting terms to the title, abstract, or claims). While Boolean search provides complete predictability "
        "and zero query execution ambiguity, it suffers from two catastrophic information retrieval pathologies: unranked output lists (every document matching "
        "the Boolean query is treated equally) and extreme query brittleness (omitting a single legal synonym eliminates the most relevant prior art)."
    )
    add_body_p(
        doc,
        "The advent of statistical term-weighting algorithms in the 1990s—most notably the Okapi BM25 probabilistic relevance framework developed by "
        "Robertson and Zaragoza (2009)—substantially advanced lexical search. BM25 introduced non-linear term frequency saturation and document length "
        "normalization, ensuring that repeated occurrences of technical terms in lengthy patent specifications do not disproportionately inflate document "
        "relevance scores. However, even probabilistic lexical retrieval remains fundamentally bounded by the vocabulary mismatch problem: it cannot "
        "recognize semantic equivalences between terms that share no morphological roots (e.g., 'transistor' and 'semiconductor switching element')."
    )

    add_section_heading(doc, "2.2 Dense Semantic Representations and Cross-Encoder Reranking")
    add_body_p(
        doc,
        "The emergence of transformer-based language representations (Vaswani et al., 2017) catalyzed a paradigm shift in semantic retrieval. Pre-trained "
        "bi-encoder models, such as BERT (Devlin et al., 2019) and domain-adapted variants like PatentBERT (Lee & Hsiang, 2020), map textual queries and patent "
        "passages into continuous, dense vector spaces where semantic proximity is measured via inner products or cosine similarity. In bi-encoder architectures, "
        "passage embeddings are pre-computed offline and indexed within specialized vector databases such as Qdrant (Qdrant Team, 2023), enabling millisecond-level "
        "approximate nearest neighbor (ANN) retrieval across high-dimensional spaces."
    )
    add_body_p(
        doc,
        "Recent benchmarks from the Beijing Academy of Artificial Intelligence (BAAI) demonstrated that general-purpose bi-encoder embeddings, specifically "
        "BGE (BAAI General Embedding, Xiao et al., 2023), achieve state-of-the-art retrieval performance across diverse technical domains. However, bi-encoders "
        "suffer from the 'representation bottleneck': because the query and document are encoded independently without cross-attention, subtle contextual nuances "
        "and claim-limiting qualifications are often lost. To resolve this limitation, modern multi-stage retrieval pipelines deploy cross-encoder neural "
        "rerankers (Nogueira & Cho, 2019; Xiao et al., 2023). In a cross-encoder, the query and candidate passage are concatenated and processed jointly through all "
        "transformer attention layers, allowing every query token to attend directly to every passage token. This rich all-to-all cross-attention produces "
        "exceptionally accurate relevance scores at the expense of higher computational latency, making cross-encoders ideal for reranking a compact pool of top candidates."
    )

    add_section_heading(doc, "2.3 Patent Novelty and Inventive-Step Screening Methodologies")
    add_body_p(
        doc,
        "Patent novelty assessment fundamentally differs from conventional document similarity. Under international patent examination guidelines, an invention "
        "lacks novelty if and only if all of its constituent technical features are disclosed within a single piece of prior art (anticipation under 35 U.S.C. § 102). "
        "If the features are disclosed across multiple prior art references, the invention may lack an inventive step (non-obviousness under 35 U.S.C. § 103) if "
        "combining those references would have been obvious to a Person Having Ordinary Skill In The Art (PHOSITA)."
    )
    add_body_p(
        doc,
        "Early attempts to automate novelty evaluation utilized claim decomposition based on constituency parsing and dependency grammar (Shinmori et al., 2003; "
        "Sheremetyeva, 2003). While linguistically principled, these symbolic approaches failed to scale across diverse drafting styles. Recent computational "
        "efforts have explored graph neural networks (GNNs) and knowledge graphs to capture relational patent entities (Helmers et al., 2019; Aristodemou & Tietze, 2018). "
        "However, existing academic systems rarely bridge the gap between high-level novelty classification and actionable, passage-level feature correspondence, "
        "leaving inventors with abstract confidence scores devoid of verifiable evidentiary justification."
    )

    add_section_heading(doc, "2.4 Retrieval-Augmented Generation (RAG) in Technical Domains")
    add_body_p(
        doc,
        "Large Language Models (LLMs) such as GPT-4 (Achiam et al., 2023) and Gemini (Google Team, 2024) have demonstrated remarkable capabilities in technical "
        "summarization and complex reasoning. Nevertheless, their direct application to legal and intellectual property domains is severely constrained by "
        "hallucination, temporal knowledge cutoffs, and ungrounded generation (Lewis et al., 2020; Shuster et al., 2021). Retrieval-Augmented Generation (RAG) "
        "addresses these vulnerabilities by supplying the language model with retrieved external context passages, instructing the model to synthesize answers "
        "grounded strictly in the provided evidence."
    )
    add_body_p(
        doc,
        "In patent analytics, RAG architectures face unique operational demands. If the retrieval stage retrieves tangential background passages rather than "
        "true prior art, standard RAG models will generate fluent, authoritative-sounding explanations that are technically meaningless or legally erroneous. "
        "Furthermore, unconstrained RAG pipelines often allow the LLM to invent quantitative scores or subjective novelty judgments. To establish legal defensibility, "
        "a technical patent RAG system must implement deterministic algorithmic scoring prior to generation, utilizing the generative model exclusively for "
        "grounded natural language synthesis."
    )

    add_section_heading(doc, "2.5 Explainable AI (XAI) and Transparent Evidence Attribution")
    add_body_p(
        doc,
        "In high-stakes intellectual property decision-making, 'black-box' artificial intelligence predictions are unacceptable. Patent examiners, corporate IP counsel, "
        "and university technology transfer officers cannot act upon an opaque machine learning score without understanding the underlying technical rationale (Gunning et al., 2019; "
        "Ribeiro et al., 2016). Transparent evidence attribution requires bidirectional provenance: an observer must be able to trace every point of scored prior-art "
        "overlap directly back to a verbatim sentence in the applicant's disclosure and a corresponding claim or paragraph in a cited patent document."
    )

    add_section_heading(doc, "2.6 Multi-Dimensional Patent Quality Evaluation Frameworks")
    add_body_p(
        doc,
        "Prior art overlap is only one facet of comprehensive invention readiness. Prior research in econometric patent valuation and patent bibliometrics "
        "(Lanjouw & Schankerman, 2004; Squicciarini et al., 2013; Hall et al., 2005) confirms that patent value and enforceability depend on multi-dimensional quality "
        "indicators: clarity of technical documentation, breadth of independent claims, structural differentiation from neighboring technological solutions, "
        "and demonstrated industrial applicability. PatentIQ incorporates these empirical econometric insights by formalizing a six-dimensional evaluation "
        "framework that balances pure novelty against technical completeness and commercial potential."
    )

    add_section_heading(doc, "2.7 Literature Synthesis Matrix")
    add_body_p(
        doc,
        "Table 2.1 presents a comprehensive comparative synthesis of fifteen foundational research works in patent retrieval, novelty evaluation, and applied NLP, "
        "benchmarking their core methodologies, strengths, and inherent limitations against the PatentIQ architecture."
    )

    # Table 2.1: Literature Synthesis Matrix (15 Papers)
    headers_2_1 = ["Ref / Author(s)", "Year", "Core Methodology", "Key Strengths", "Identified Limitations", "PatentIQ Contrast"]
    rows_2_1 = [
        ["Robertson & Zaragoza", "2009", "Okapi BM25 probabilistic lexical retrieval", "High precision on exact technical keywords", "Fails on legal terminology mismatch", "Coupled with dense BGE vectors in hybrid pipeline"],
        ["Lee & Hsiang", "2020", "PatentBERT domain-adapted transformer", "Captures specialized patent semantics", "Bi-encoder representation bottleneck", "Combines BGE bi-encoders with cross-encoder reranking"],
        ["Xiao et al. (BAAI)", "2023", "BGE embeddings & BGE cross-encoder", "State-of-the-art dense retrieval and reranking", "Requires dual-stage pipeline orchestration", "Implemented in FastAPI with Qdrant vector index"],
        ["Cormack et al.", "2009", "Reciprocal Rank Fusion (RRF)", "Parameter-free multi-list rank merging", "Ignores absolute similarity magnitude", "Calibrated at k=60 to merge sparse and dense rankings"],
        ["Vaswani et al.", "2017", "Multi-head self-attention transformers", "Universal sequence representation", "High computational complexity for long texts", "Employed in selective passage-level cross-attention"],
        ["Lewis et al.", "2020", "Retrieval-Augmented Generation (RAG)", "Grounds LLM responses in external context", "Vulnerable to noisy retrieval passages", "Constrained RAG strictly explaining pre-scored evidence"],
        ["Shinmori et al.", "2003", "Constituency parsing of patent claim structure", "Deconstructs claims into technical elements", "Brittle against non-standard drafting styles", "Hybrid pattern-based and rule-based feature extractor"],
        ["Sheremetyeva", "2003", "NLP frame extraction for patent claims", "Linguistic analysis of inventive features", "High manual rule overhead; poor scalability", "Automated feature decomposition across 4 categories"],
        ["Aristodemou & Tietze", "2018", "Machine learning in patent analytics survey", "Comprehensive taxonomic overview of IP analytics", "Survey only; no operational system", "Operationalizes recommendations into end-to-end tool"],
        ["Helmers et al.", "2019", "Automated patent classification with neural nets", "High IPC classification accuracy at scale", "Document-level classification; no passage evidence", "Passage-level Evidence Matrix with verbatim citations"],
        ["Lanjouw & Schankerman", "2004", "Econometric patent quality index", "Multi-indicator composite quality modeling", "Offline retrospective citation analysis", "Real-time pre-filing EB-PRE readiness scoring"],
        ["Squicciarini et al.", "2013", "OECD patent quality indicators framework", "Extensive empirical validation of patent value", "Designed for macroeconomic policy", "Adapted into 6 engineering assessment dimensions"],
        ["Ribeiro et al. (LIME)", "2016", "Local interpretable model-agnostic explanations", "Provides feature-attribution explanations", "Perturbation-based; high latency overhead", "Direct structural provenance via Feature-Evidence Matrix"],
        ["Achiam et al. (OpenAI)", "2023", "GPT-4 advanced reasoning capabilities", "Exceptional natural language synthesis", "Proprietary; ungrounded legal hallucinations", "Gemini 2.5 Pro constrained by strict guardrails & fallback"],
        ["Google Team", "2024", "Gemini 2.5 Pro multimodal technical reasoning", "Deep context window and long-horizon reasoning", "Requires prompt constraints to prevent drift", "Integrated with watchdog and deterministic fallback"],
    ]
    col_w_2_1 = [2.2, 1.1, 2.8, 2.8, 2.8, 2.9]
    add_table_data(doc, "2.1", "Literature Synthesis Matrix of 15 Foundational Patent Analysis Works", headers_2_1, rows_2_1, col_w_2_1)

    add_section_heading(doc, "2.8 Critical Research Gaps and PatentIQ Differentiation")
    add_body_p(
        doc,
        "A rigorous synthesis of existing academic literature and commercial patent platforms exposes four profound research gaps:"
    )
    add_bullet_p(
        doc,
        "Research Gap 1: Disconnection Between Retrieval and Feature-Level Overlap —",
        "Existing systems perform retrieval at the document level. If a 40-page patent document is retrieved, the user is left to manually inspect dozens of claims "
        "to discover which specific technical mechanism overlapped. PatentIQ bridges this gap by introducing the passage-level Evidence Matrix."
    )
    add_bullet_p(
        doc,
        "Research Gap 2: Conflation of Semantic Similarity with Legal Prior Art —",
        "Naive semantic systems treat high cosine similarity as evidence of novelty loss. In technical patents, contextual background similarity is common and benign. "
        "PatentIQ establishes a controlled five-tiered relationship vocabulary that explicitly isolates direct and partial matches from benign contextual matches."
    )
    add_bullet_p(
        doc,
        "Research Gap 3: Black-Box Scoring and Hallucinatory LLM Metrics —",
        "Current AI tools either output an uninterpretable machine-learned score or prompt an unconstrained LLM to generate subjective novelty percentages. "
        "PatentIQ enforces complete architectural separation: deterministic algorithms calculate scores, while the LLM strictly explains retrieved evidence."
    )
    add_bullet_p(
        doc,
        "Research Gap 4: Neglect of Assessment Confidence and Negative Proof Fallacies —",
        "Prevailing search engines interpret zero retrieved matches as 100% novelty. PatentIQ formalizes assessment confidence as an independent orthogonal metric, "
        "generating explicit uncertainty flags whenever the evidence base is sparse or the feature space is under-searched."
    )

    # =========================================================================
    # CHAPTER 3: REQUIREMENTS ANALYSIS AND SYSTEM SPECIFICATIONS
    # =========================================================================
    doc.add_page_break()
    add_chapter_heading(doc, 3, "Requirements Analysis and System Specifications")

    add_section_heading(doc, "3.1 User Personas and Stakeholder Use Cases")
    add_body_p(
        doc,
        "Requirements engineering for PatentIQ involved analyzing three primary academic and technical user personas whose operational workflows dictate system behavior:"
    )
    add_bullet_p(
        doc,
        "Persona A: The Student Inventor / Academic Researcher —",
        "Possesses deep technical knowledge of their proposed invention but lacks formal training in patent claim construction, Boolean search syntax, and legal classification "
        "taxonomies. Needs an accessible upload portal that accepts standard research reports, highlights potential prior-art conflicts, and provides tactical advice "
        "on technical differentiation prior to submitting an institutional disclosure."
    )
    add_bullet_p(
        doc,
        "Persona B: The University Technology Transfer Officer (TTO) —",
        "Evaluates dozens of invention disclosures each semester under tight budgetary constraints. Needs a high-throughput, objective pre-screening system that "
        "evaluates documentation completeness, identifies immediate prior-art collisions, and provides auditable, structured PDF reports to justify patent budget allocations."
    )
    add_bullet_p(
        doc,
        "Persona C: The Startup Founder / Early-Stage Innovator —",
        "Requires rapid, confidential feedback on whether their product architecture risks infringing published claims or lacks novelty against existing patents, "
        "demanding deterministic evidence attribution without exposing sensitive proprietary disclosures to public LLM training pools."
    )

    add_section_heading(doc, "3.2 Functional Requirements")
    add_body_p(
        doc,
        "The functional capabilities of PatentIQ are categorized into twelve discrete, testable Functional Requirements (FR-1 through FR-12), detailed in Table 3.1."
    )

    headers_3_1 = ["Req ID", "Functional Requirement Description", "Input Data", "Output / Transformed State", "Verification Criteria"]
    rows_3_1 = [
        ["FR-1", "Multi-Format Document Upload & Validation", "PDF, DOCX, TXT files (< 20MB)", "Sanitized text stream & metadata", "Rejects corrupted files & empty streams"],
        ["FR-2", "Patent-Aware Text Chunking", "Raw extracted document text", "Ordered list of semantic chunks", "Preserves paragraph bounds & claim IDs"],
        ["FR-3", "Technical Feature Deconstruction", "Document chunk stream", "Decomposed TechnicalFeature objects", "Classifies problem, component, mechanism, effect"],
        ["FR-4", "Dense Semantic Embedding Generation", "Extracted feature text spans", "768-dimensional normalized BGE vectors", "Cosine similarity normalization in Qdrant"],
        ["FR-5", "Sparse BM25 Lexical Retrieval", "Tokenized feature keywords", "Ranked sparse prior-art candidates", "Applies Okapi BM25 scoring with k1=1.5, b=0.75"],
        ["FR-6", "Reciprocal Rank Fusion (RRF)", "Sparse and dense candidate lists", "Fused reciprocal rank candidate list", "Merged rank score calculation with k=60"],
        ["FR-7", "Cross-Encoder Neural Reranking", "Query-passage concatenated pairs", "Reranked candidate list with scores", "Joint attention scoring via bge-reranker-base"],
        ["FR-8", "Evidence Relationship Classification", "Reranked feature-passage pairs", "Assigned 5-tier relationship severity", "Classifies direct, partial, contextual, weak, none"],
        ["FR-9", "Evidence Matrix Construction", "All feature-passage mappings", "2D relational Evidence Matrix", "Maps rows (features) to cols (prior art)"],
        ["FR-10", "EB-PRE Deterministic Scoring", "Evidence Matrix + Feature objects", "6 dimension scores + Readiness score", "Exact mathematical weight calculation (0-100)"],
        ["FR-11", "Confidence & Uncertainty Flagging", "Retrieval depth & evidence counts", "Confidence score (0.0-1.0) & flags", "Emits flags on unsearched features or low coverage"],
        ["FR-12", "Grounded Report & Fallback Mode", "EB-PRE scores + Evidence Matrix", "Structured 10-section report", "Gemini 2.5 Pro synthesis with quota fallback"],
    ]
    col_w_3_1 = [1.4, 3.2, 2.5, 3.0, 3.5]
    add_table_data(doc, "3.1", "Functional Requirements (FR-1 through FR-12) of PatentIQ", headers_3_1, rows_3_1, col_w_3_1)

    add_section_heading(doc, "3.3 Non-Functional Requirements")
    add_body_p(
        doc,
        "Non-functional requirements govern the performance, security, reliability, and deployment constraints of PatentIQ, detailed in Table 3.2."
    )

    headers_3_2 = ["NFR ID", "Category", "Specification Metric", "Target Threshold", "Implemented Verification"]
    rows_3_2 = [
        ["NFR-1", "Performance", "Warm Pipeline Execution Latency", "< 15 seconds per document", "12.4s avg latency verified across benchmarks"],
        ["NFR-2", "Cold-Start", "Initial Request Latency & Pre-Warm", "< 60s cold-start with pre-warming", "Lifespan pre-warm executes in 41.86s"],
        ["NFR-3", "Accuracy", "Scoring Determinism & Repeatability", "100% identical scores on identical input", "Verified across 10 repeated automated runs"],
        ["NFR-4", "Security", "Multi-Tenant Data Isolation", "Strict Row Level Security (RLS) enforcement", "Validated with dual USING + WITH CHECK tests"],
        ["NFR-5", "Robustness", "API Quota Degradation Handling", "Zero unhandled 429 exceptions", "Automatic deterministic fallback activated"],
        ["NFR-6", "Scalability", "Vector Retrieval Complexity", "Sub-100ms ANN lookup on Qdrant", "HNSW indexing on 768-d BGE vector collection"],
        ["NFR-7", "Persistence", "Data Loss on Server Restart", "Zero loss of user projects and reports", "Persistent Supabase store with demo fallback"],
        ["NFR-8", "Usability", "Modern Web Interface Responsiveness", "< 200ms UI interaction latency", "React 19 + Vite optimized production build"],
    ]
    col_w_3_2 = [1.4, 2.2, 3.2, 3.2, 3.6]
    add_table_data(doc, "3.2", "Non-Functional Requirements (NFR-1 through NFR-8) Performance Matrix", headers_3_2, rows_3_2, col_w_3_2)

    add_section_heading(doc, "3.4 Locked Technology Stack Justification")
    add_body_p(
        doc,
        "To satisfy the rigorous functional and non-functional requirements, PatentIQ is engineered on a strictly locked technology stack. "
        "Table 3.3 summarizes each locked component, its version, and its architectural justification."
    )

    headers_3_3 = ["Stack Layer", "Selected Technology", "Version / Model", "Architectural Justification & Role"]
    rows_3_3 = [
        ["Frontend", "React.js + Vite + Tailwind", "React 19, Vite 6.0", "Blazing-fast SPA build, component-based modular UI, reactive state management"],
        ["Backend API", "FastAPI (Python)", "FastAPI 0.141, Python 3.14", "High-performance async I/O, native Pydantic validation, seamless PyTorch / HuggingFace integration"],
        ["Vector Database", "Qdrant", "Qdrant 1.19 / Cloud", "Dedicated vector search engine with native HNSW indexing, payload filtering, and sub-millisecond ANN"],
        ["Dense Embeddings", "BGE Embeddings", "BAAI/bge-base-en-v1.5", "Top-performing 768-d dense embeddings on MTEB retrieval benchmarks; normalized cosine space"],
        ["Sparse Retrieval", "Okapi BM25", "rank-bm25 0.2.2", "Complementary lexical keyword matching; robust against vocabulary drift in long patent texts"],
        ["Neural Reranker", "BGE Cross-Encoder", "BAAI/bge-reranker-base", "Deep bidirectional all-to-all query-passage cross-attention; eliminates bi-encoder bottleneck"],
        ["Generative LLM", "Google Gemini Pro", "Gemini 2.5 Pro / Flash", "High-reasoning technical synthesis constrained by strict grounded RAG prompts; quota fallback"],
        ["Relational DB", "Supabase / PostgreSQL", "PostgreSQL 15 / Supabase", "Relational persistence of 9 entity tables; strict Row Level Security (RLS); NO pgvector"],
        ["PDF Processing", "PyMuPDF (fitz)", "PyMuPDF 1.28.2", "High-speed, memory-efficient PDF extraction preserving layout, tables, and bounding coordinates"],
    ]
    col_w_3_3 = [2.2, 2.6, 2.8, 6.0]
    add_table_data(doc, "3.3", "Locked Technology Stack Component Specification and Rationale", headers_3_3, rows_3_3, col_w_3_3)

    add_section_heading(doc, "3.5 Development Corpus vs Worldwide Patent Coverage")
    add_body_p(
        doc,
        "A foundational principle of truthful academic reporting is accurately distinguishing between a development test corpus and comprehensive "
        "worldwide prior-art coverage. The current verified PatentIQ implementation utilizes an internal development corpus comprising 15 public "
        "United States patents encompassing 78 granular claim and description passages, summarized in Table 3.4. These patents span medical devices, "
        "autonomous robotics, edge computing, optical sensor systems, and wireless power transmission. This curated corpus provides diverse technical "
        "claims to validate hybrid retrieval, cross-encoder reranking, and evidence matrix mapping. However, it does not constitute exhaustive global prior art. "
        "The architecture is designed to scale horizontally to millions of documents on Qdrant and Supabase in production deployment."
    )

    headers_3_4 = ["Patent Publication No.", "Issuing Jurisdiction", "Technical Domain / Field", "Classification (CPC/IPC)", "Chunk Count", "Corpus Role"]
    rows_3_4 = [
        ["US-10492811-B2", "United States (USPTO)", "Minimally invasive surgical robotics", "A61B 34/30", "6 chunks", "Direct prior art for robotic instrumentation"],
        ["US-10893842-B2", "United States (USPTO)", "Multi-spectral optical diagnostic imaging", "A61B 5/00", "5 chunks", "Prior art for medical diagnostic features"],
        ["US-11197643-B2", "United States (USPTO)", "Autonomous sensor fusion & depth mapping", "G01S 17/89", "6 chunks", "Prior art for LiDAR/camera perception"],
        ["US-11452491-B2", "United States (USPTO)", "Edge neural inference in embedded systems", "G06N 3/063", "5 chunks", "Prior art for edge acceleration hardware"],
        ["US-11620854-B2", "United States (USPTO)", "Adaptive illumination for machine vision", "H04N 23/56", "5 chunks", "Prior art for dynamic lighting control"],
        ["US-11783510-B2", "United States (USPTO)", "Closed-loop feedback robotic actuation", "B25J 9/16", "6 chunks", "Prior art for haptic surgical feedback"],
        ["US-11849921-B2", "United States (USPTO)", "Real-time point-cloud compression", "H04N 19/597", "5 chunks", "Prior art for spatial telemetry transmission"],
        ["US-11910543-B2", "United States (USPTO)", "Wireless inductive power transmission", "H02J 50/12", "5 chunks", "Prior art for non-contact power charging"],
        ["US-11986154-B2", "United States (USPTO)", "Sterilization monitoring for surgical tools", "A61L 2/28", "5 chunks", "Prior art for autoclave sensor logging"],
        ["US-12011244-B2", "United States (USPTO)", "Wearable vital sign telemetry patch", "A61B 5/0205", "5 chunks", "Prior art for wearable biometric sensors"],
        ["US-12042188-B2", "United States (USPTO)", "Micro-actuator robotic articulation", "B25J 17/02", "5 chunks", "Prior art for robotic end-effector wrist"],
        ["US-12089452-B2", "United States (USPTO)", "Low-latency wireless video streaming", "H04N 21/436", "5 chunks", "Prior art for intraoperative visual feed"],
        ["US-12115003-B2", "United States (USPTO)", "Autonomous obstacle avoidance algorithms", "G05D 1/02", "5 chunks", "Prior art for robotic trajectory planning"],
        ["US-12144321-B2", "United States (USPTO)", "Battery health estimation via impedance", "G01R 31/389", "5 chunks", "Prior art for battery management systems"],
        ["US-12180012-B2", "United States (USPTO)", "Cryptographic tamper-evident audit logging", "G06F 21/64", "5 chunks", "Prior art for secure medical data logging"],
    ]
    col_w_3_4 = [2.2, 2.2, 3.2, 2.2, 1.4, 2.4]
    add_table_data(doc, "3.4", "Development Patent Corpus Composition and Classification Distribution", headers_3_4, rows_3_4, col_w_3_4)

# PatentIQ — Prior-Art Patent Corpus Architecture (`data/`)

## 1. Overview & Purpose

The `data/corpus/` directory houses the structured, normalized, and validated **Internal Prior-Art Patent Corpus** for PatentIQ.

In the PatentIQ target architecture, this corpus serves as the **global reference database of existing technology** against which user invention disclosures are cross-referenced to evaluate patent readiness, novelty, and obviousness.

> **CRITICAL SEPARATION RULE:**
> User-uploaded invention disclosures (`apps/api/app/services/document_processing/`) and the global patent prior-art corpus (`data/corpus/`) are strictly separated conceptually and architecturally. User documents are private and project-scoped, whereas the patent corpus constitutes the global reference ground truth.

---

## 2. Directory Structure

```
data/
└── corpus/
    ├── raw/              # Raw ingested patent datasets (JSON, JSONL)
    │   └── sample_patents.jsonl
    ├── normalized/       # Deterministically cleaned canonical patent records
    │   └── sample_patents_normalized.jsonl
    ├── sample/           # Pre-chunked, traceable passage records ready for indexing
    │   └── sample_chunks.jsonl
    └── manifest.json     # Reproducible manifest with volume, dates, and SHA-256 checksums
```

---

## 3. Supported Input Formats

The ingestion loader (`apps/api/app/services/patent_corpus/loader.py`) supports:
* **JSON (`.json`):** Single patent object or JSON array of patent objects.
* **JSONL (`.jsonl`):** Line-delimited JSON. Processed using a streaming iterator (`PatentCorpusLoader.stream_jsonl`) to support scaling to arbitrarily large datasets without excessive memory usage.

### Flexible Field Mapping
The loader automatically maps heterogeneous source fields into canonical attributes:
* Patent ID: `patent_number`, `patentNumber`, `doc_number`, `id`
* Publication ID: `publication_number`, `publicationNumber`
* Application ID: `application_number`, `applicationNumber`, `app_number`
* Jurisdiction: `country_code`, `country`, `jurisdiction` (defaults to `"US"`)
* Classifications: `ipc_classes` / `ipcClasses` / `ipc`, `cpc_classes` / `cpcClasses` / `cpc`
* Dates: `publication_date` / `publicationDate`, `filing_date` / `filingDate`, etc.

---

## 4. Canonical Patent Schema

The canonical schema matches the relational definitions of `public.patent_documents` and `public.patent_chunks` in `backend/supabase_schema.sql`:

### 4.1 `PatentDocument` (`public.patent_documents`)
| Field | Type | Description |
|---|---|---|
| `patent_number` | `TEXT UNIQUE NOT NULL` | Unique publication identifier (e.g., `US-10492811-B2`) |
| `publication_number` | `TEXT` | Official publication number |
| `application_number` | `TEXT` | Filing application number |
| `country_code` | `TEXT DEFAULT 'US'` | 2-letter ISO/WIPO issuing jurisdiction |
| `title` | `TEXT NOT NULL` | Official patent title |
| `abstract` | `TEXT NOT NULL` | Patent abstract text |
| `inventors` | `TEXT[]` | List of inventor names |
| `assignee` | `TEXT` | Organization or applicant name |
| `publication_date` | `DATE` | Publication date (`YYYY-MM-DD`) |
| `filing_date` | `DATE` | Filing application date (`YYYY-MM-DD`) |
| `priority_date` | `DATE` | Earliest priority date (`YYYY-MM-DD`) |
| `ipc_classes` | `TEXT[]` | International Patent Classification codes |
| `cpc_classes` | `TEXT[]` | Cooperative Patent Classification codes |
| `language` | `TEXT DEFAULT 'en'` | ISO 639-1 language code |
| `source` | `TEXT NOT NULL` | Origin repository (`uspto`, `google_patents`, `wipo`) |
| `metadata` | `JSONB` | Provenance URLs, datasets, and timestamps |

### 4.2 `PatentChunk` (`public.patent_chunks`)
| Field | Type | Description |
|---|---|---|
| `patent_number` | `TEXT NOT NULL` | Correlation key to parent patent |
| `chunk_index` | `INT NOT NULL` | Sequential chunk index within patent document |
| `section` | `TEXT NOT NULL` | Canonical section (`claims`, `abstract`, `description`, etc.) |
| `claim_number` | `INT` | Explicit claim number ($1, 2, 3\dots$) if section is `claims` |
| `paragraph_id` | `TEXT` | Paragraph identifier (e.g., `[0042]`, `claim:1`, `para:3`) |
| `text` | `TEXT NOT NULL` | Verbatim chunk text |
| `metadata` | `JSONB` | Citation metadata (patent number, title, country, date) |

---

## 5. Normalization Principles

Implemented in `PatentNormalizer` (`apps/api/app/services/patent_corpus/normalizer.py`):
1. **Deterministic & Faithful:** No LLMs or generative paraphrasing are employed; the source text remains verbatim.
2. **Whitespace & Controls:** Normalizes line breaks to `\n`, strips non-printable control characters, and collapses 3+ consecutive line breaks.
3. **Preservation of Technical Notation:** Preserves mathematical symbols ($\pm, \le, \ge, \Omega, \mu, \degree$), chemical formulae ($H_2O, CO_2$), and subscripts/superscripts.
4. **Standardized Dates:** Converts all supported date variants into canonical ISO `YYYY-MM-DD` strings.
5. **Empty Values:** Placeholder strings (`"N/A"`, `"none"`, `""`) are normalized to `None`.

---

## 6. Patent-Aware Chunking

Implemented in `PatentCorpusChunker` (`apps/api/app/services/patent_corpus/chunker.py`):
* **Traceable Claims:** Individual claims (`Claim 1`, `1.`, `Claim 2:`) are extracted and assigned individual chunks tagged with `section="claims"` and `claim_number=N`. If a claim exceeds max characters, it is sub-chunked while retaining the same `claim_number`.
* **Section Boundaries:** Content from distinct patent sections (`abstract`, `background`, `summary`, `claims`, `detailed_description`) is never blended into a single chunk.
* **Rolling Overlap:** Narrative descriptions use sentence boundary snapping with a default maximum length of 1,000 characters and 200 characters of overlap.

---

## 7. Corpus Validation & Quality Controls

Implemented in `PatentCorpusValidator` (`apps/api/app/services/patent_corpus/validator.py`):
* **Mandatory Identifiers:** Rejects records missing `patent_number`, `title`, or `abstract`.
* **Format Checks:** Validates 2-letter country codes and ISO dates.
* **Claims Integrity:** Ensures chunks in the `claims` section have positive integers for `claim_number`.
* **Deduplication:** Flags duplicate patent numbers and duplicate chunk contents.
* **Transparency:** Does not silently drop records; emits a structured `CorpusValidationReport` detailing errors and warnings.

---

## 8. Corpus Manifest & Provenance

The manifest at `data/corpus/manifest.json` provides reproducibility:
* **Provenance:** Tracks source repository, dataset name, retrieval dates, and URLs.
* **Integrity:** Stores cryptographic SHA-256 hashes of raw, normalized, and chunk files.
* **Corpus Metrics:** Stores patent count, chunk count, supported jurisdictions, and languages.

---

## 9. Hybrid Retrieval Layer (Step 5 Implementation)

PatentIQ provides a two-pronged prior-art retrieval engine combining sparse lexical search and dense semantic vector representations:

### 9.1 Sparse Lexical Retrieval (BM25)
* **Implementation:** `BM25Retriever` (`apps/api/app/services/retrieval/bm25_retriever.py`)
* **Role:** Captures exact alphanumeric matches, rare technical terms, chemical formulae, and specific patent identifiers.
* **Parameters:** `k1=1.5` (term frequency saturation), `b=0.75` (document length normalization penalty).
* **Deterministic Tokenization:** Captures words, numbers, and hyphenated technical terms (`[a-zA-Z0-9_\-]+`).

### 9.2 Dense Semantic Retrieval (BGE + Qdrant)
* **Embedding Model:** `BAAI/bge-base-en-v1.5` (768 dimensions) via `BGEEmbeddingProvider`.
* **Vector Normalization:** Strict L2 unit normalization; inner product vector search is mathematically equivalent to cosine similarity.
* **Vector Store:** `QdrantVectorStore` (`apps/api/app/services/retrieval/qdrant_store.py`) configured with `Distance.COSINE` and vector size 768 dynamically derived from the model.
* **Deterministic Point IDs:** Points are indexed using deterministic UUIDv5 strings generated via `generate_point_id(patent_number, chunk_index)`. This guarantees 100% idempotent indexing without duplicate point drift.
* **Traceability Payload:** Every vector point retains:
  - `patent_number`, `chunk_index`, `section`, `claim_number`, `page_number`, `paragraph_id`
  - `text`, `title`, `assignee`, `publication_date`, `country_code`, `language`, `ipc_classes`, `cpc_classes`
* **Metadata Filtering:** Native Qdrant filter expressions (`models.Filter`) applied at query time for `country_code`, `section`, `publication_date`, `cpc_classes`, `ipc_classes`, and `language`.

### 9.3 Reciprocal Rank Fusion (RRF)
* **Implementation:** `ReciprocalRankFusion` (`apps/api/app/services/retrieval/rrf_fusion.py`)
* **Role:** Fuses disparate score distributions from BM25 and BGE semantic search into a robust ordinal ranking without fragile score normalization.
* **Formula:** $\text{RRF}(d) = \sum_{m \in \{\text{sparse}, \text{dense}\}} \frac{1}{k + \text{rank}_m(d)}$ with $k = 60$.
* **Missing Rank Rule:** If a candidate is present in only one retrieval stream, the missing stream contributes $0.0$.
* **Deterministic Tie-Breaking:** Ties are broken by `rrf_score` desc, `patent_number` asc, and `chunk_index` asc.

---

## 10. BGE Cross-Encoder Reranking Layer (Step 6 Implementation)

PatentIQ incorporates a high-precision pairwise cross-encoder stage operating directly downstream of Reciprocal Rank Fusion:

### 10.1 Why Reranking is Needed
Bi-encoder dense models (like `bge-base-en-v1.5`) compress entire passages and queries into separate static 768-dimensional vectors. While fast for vector search, this bi-encoder architecture sacrifices fine-grained token-level cross-attention. The cross-encoder reranker receives the concatenated `(query, passage)` pair directly into all transformer self-attention layers, capturing intricate semantic nuances, negation, and specific technical inter-relationships that bi-encoders miss.

### 10.2 Model & Configuration
* **Default Model:** `BAAI/bge-reranker-base` (~278M parameters, fp32).
* **Configurable Model Support:** Supports `BAAI/bge-reranker-large` via `RERANKER_MODEL_NAME`.
* **Inference Batch Size:** `RERANKER_BATCH_SIZE = 8` (configurable in `.env` / `config.py`) to maintain safe CPU and RAM headroom.
* **Candidate Depths:**
  - RRF candidate depth: 20
  - Reranker candidate pool: 20
  - Final reranked output: 10 (or user-requested `top_k`)

### 10.3 Score Semantics
The retrieval pipeline computes distinct relevance signals that are fundamentally non-interchangeable:
* **BM25 score:** Unbounded lexical term frequency / inverse document frequency score.
* **Dense score:** Cosine similarity $[-1, 1]$ in 768-dimensional BGE embedding space.
* **RRF score:** Rank-reciprocal aggregation score $[0, 2 / (k + 1)]$.
* **Reranker score:** Raw cross-encoder pairwise relevance logit / score. Higher indicates stronger relevance.
* **Non-Interchangeability:** These scores are never mathematically blended (e.g. no arbitrary $0.4 \times \text{RRF} + 0.6 \times \text{Reranker}$).

### 10.4 Deterministic Ranking & Tie-Breaking
Candidates are sorted using a strict 4-stage deterministic hierarchy:
1. `reranker_score` descending
2. `rrf_score` descending
3. `patent_number` ascending
4. `chunk_index` ascending

### 10.5 Full Traceability Contract (`RerankedResult`)
Every reranked candidate retains complete auditability:
* Document & chunk identifiers: `patent_number`, `patent_id`, `chunk_id`, `chunk_index`
* Passage text & patent section: `text`, `section`, `claim_number`, `page_number`, `paragraph_id`
* Metadata & classifications: `title`, `country_code`, `publication_date`, `ipc_classes`, `cpc_classes`
* Upstream retrieval signals: `sparse_rank`, `dense_rank`, `sparse_score`, `dense_score`, `rrf_score`
* Cross-encoder outputs: `reranker_score`, `reranker_rank`, `retrieval_method = "hybrid_rrf_reranked"`

---

---

## 11. Technical Feature Extraction Layer (Step 7 Implementation)

PatentIQ provides a deterministic, structured Technical Feature Extraction pipeline transforming user invention documents into atomic, traceable technical features ready for subsequent evidence mapping:

### 11.1 Purpose of Feature Extraction
Rather than generic prose summarization, feature extraction decomposes an invention disclosure into explicit technical components, functional operations, structural relationships, mechanisms, and claimed aspects. This structured representation serves as the foundation for feature-to-evidence matching against prior-art claims.

### 11.2 Controlled Feature Vocabulary (`FeatureType`)
Features are restricted to a strict closed taxonomy:
* `problem`: Technical challenges, disadvantages, or unmet needs addressed by the invention.
* `component`: Physical or logical hardware modules, circuits, assemblies, or sensors.
* `function`: Operational capabilities, programmed behaviors, or actions.
* `relationship`: Spatial, electrical, mechanical, or communication linkages between components.
* `input`: Data, power, or physical material received by the system.
* `output`: Data, drive current, signals, or physical results generated by the system.
* `process`: Algorithmic steps or operational sequences.
* `constraint`: Quantitative or qualitative bounds, ranges, or operating tolerances.
* `mechanism`: Specific technical means or methods employed to achieve an effect.
* `technical_effect`: Tangible advantages, efficiency gains, or physical consequences achieved.
* `claimed_aspect`: Core inventive combinations or claim preambles explicitly recited in patent claims.

### 11.3 Deterministic Normalization & Content-Addressed IDs
* **Normalization:** Strips bullet artifacts, quotation decorators, and whitespace noise while strictly preserving technical tokens, numbers, chemical formulas, and units (e.g., `5.8 GHz`, `+/- 0.5%`).
* **Deterministic IDs:** Generated via `SHA-256(project_id::type::normalized_text)`:
  `feat_{type_prefix}_{hash[:12]}`. The identical input text in the same project produces the identical feature ID across all runs.

### 11.4 Provenance & Duplicate Consolidation
* **Exact Duplicate Merging:** Identical normalized features across multiple chunks are consolidated into a single primary `TechnicalFeature`.
* **Multi-Source Provenance:** All supporting locations are preserved in `supporting_sources` with `chunk_id`, `chunk_index`, `section`, `page_number`, `claim_number`, and exact character spans (`evidence_span_start`, `evidence_span_end`).

### 11.5 Confidence Semantics
* **Extraction Confidence:** Represents model/rule certainty that the source text explicitly supports the technical feature.
* **NOT Patentability:** Does not indicate novelty, inventive step, non-obviousness, or legal validity.

---

## 12. Feature-to-Evidence Mapping Layer (Step 8 Implementation)

PatentIQ provides a deterministic, transparent Feature-to-Evidence Mapping layer connecting atomic `TechnicalFeature` objects with retrieved and reranked prior-art patent passages (`RerankedResult`):

### 12.1 Purpose of Evidence Mapping
Rather than evaluating patentability holistically or relying on generative prose, the mapping layer establishes explicit, auditable correspondences between each extracted technical feature of an invention and specific prior-art patent excerpts (claims, descriptions, abstracts).

### 12.2 Evidence Relationship Taxonomy (`EvidenceRelationship`)
Every candidate pair is classified into one of five mutually exclusive relationship categories:
* `direct_match`: Prior-art passage explicitly discloses the technical feature, identical elements, or complete functional equivalents ($\ge 0.75$).
* `partial_match`: Prior-art passage discloses substantial aspects of the feature but omits specific constraints or operational mechanisms ($0.50 - 0.74$).
* `contextual_match`: Prior-art passage operates within the same technical domain or discloses analogous context without reciting the specific inventive mechanism ($0.30 - 0.49$).
* `weak_match`: Peripheral keyword or conceptual co-occurrence with low technical relevance ($0.15 - 0.29$).
* `no_material_match`: No meaningful technical overlap ($< 0.15$).

### 12.3 Dual Similarity Computation
* **Lexical Overlap:** Computed via token Jaccard similarity over normalized alphanumeric terms (capturing technical decimals and hyphens, e.g. `5.8 GHz`, `high-frequency`).
* **Dense Semantic Similarity:** Cosine similarity in 768-dimensional BGE embedding space ($[-1.0, 1.0]$ clamped to $[0.0, 1.0]$).
* **Weighted Matching Score:** Deterministic combination:
  $$\text{Matching Score} = w_{\text{lexical}} \times \text{Jaccard} + w_{\text{semantic}} \times \text{Dense Cosine}$$
  (Defaults: $w_{\text{lexical}} = 0.4$, $w_{\text{semantic}} = 0.6$).

### 12.4 Deterministic Confidence Scoring & Content-Addressed IDs
* **Confidence Calculation:** Combines the matching score with relationship tier weights, a signal agreement bonus ($+0.05$ when both lexical $\ge 0.4$ and semantic $\ge 0.7$), and a reranker top alignment bonus ($+0.05$ if `reranker_rank` $\le 3$), clamped to $[0.0, 1.0]$.
* **Deterministic Mapping IDs:** Content-addressed via `SHA-256(feature_id::patent_number::chunk_id)`:
  `map_{hash[:14]}`. Ensures idempotency across repeated pipeline runs.
* **Top-$k$ Alignment:** Filters out non-matches, sorts by confidence descending, reranker rank ascending, patent number ascending, and chunk index ascending, retaining the top-$k$ (default 5) matches per feature.

### 12.5 Full Traceability & Auditability Contract (`FeatureEvidenceMapping`)
Each mapping record preserves complete provenance:
* Feature details: `feature_id`, `feature_name`, `feature_type`, `feature_text`
* Prior-art passage: `patent_number`, `patent_id`, `chunk_id`, `chunk_index`, `section`, `claim_number`, `matched_text`
* Upstream retrieval signals: `sparse_rank`, `dense_rank`, `rrf_score`, `reranker_score`, `reranker_rank`
* Mapping signals: `lexical_overlap_score`, `semantic_similarity_score`, `matching_score`, `confidence`
* Audit explanation: Detailed string detailing exact score breakdown and rationale.

### 12.6 Semantic Distinction of Scores
* **Technical Correspondence Only:** Lexical overlap, dense similarity, matching score, and mapping confidence measure the degree of technical text alignment between an invention feature and a prior-art passage.
* **NOT Patentability:** These scores do not measure novelty, non-obviousness, freedom-to-operate (FTO), or legal validity.

---

## 13. Evidence Matrix & Evidence-Based Patent Readiness Engine (EB-PRE) (Step 9 Implementation)

PatentIQ provides a 100% deterministic decision-support engine aggregating `FeatureEvidenceMapping` records into an auditable `EvidenceMatrix` and computing early-stage readiness across six independent dimensions:

### 13.1 Purpose & Non-Legal Nature of EB-PRE
EB-PRE is an engineering decision-support tool. It measures technical documentation sufficiency, prior-art overlap, and technical differentiation against candidate prior art. It **strictly disclaims** any legal novelty grant, validity determination, or freedom-to-operate guarantee.

### 13.2 Evidence Matrix Architecture (`EvidenceMatrix`)
The Evidence Matrix preserves the complete two-dimensional lattice between invention features and prior-art patent excerpts:
* **`EvidenceMatrixCell`:** Retains `feature_id`, `feature_type`, `feature_text`, `patent_number`, `patent_id`, `chunk_id`, `chunk_index`, `evidence_text`, `relationship`, `matching_score`, `mapping_confidence`, `reranker_score`, `reranker_rank`, `section`, `claim_number`, `page_number`, and `source`.
* **Traceability:** Prevents reduction of complex patent correspondences to a scalar, allowing users to drill down into exact claim numbers and character offsets.

### 13.3 Six Independent EB-PRE Dimensions
All dimensions evaluate to $[0.0, 1.0]$:
1. **Novelty ($w = 0.30$):** Evidence-derived indication assessing the severity of strongest prior-art matches. Direct matches heavily reduce the score; partial/contextual matches apply moderate/light penalties. Crucially, unevidenced features in the candidate pool do **NOT** yield 1.0 novelty; they are anchored conservatively (0.60) and trigger `insufficient_prior_art_coverage`.
2. **Prior-Art Overlap ($w = 0.20$):** Quantifies the intensity of prior-art representation across features, weighted by relationship severity and mapping confidence.
3. **Technical Differentiation ($w = 0.20$):** Measures features that remain distinct, weakly represented, or unaddressed by retrieved prior art, with importance weighting for core mechanisms and constraints.
4. **Innovation Characteristics ($w = 0.15$):** Evaluates structural and architectural completeness across components, functions, mechanisms, relationships, technical effects, and constraints.
5. **Documentation Quality ($w = 0.10$):** Evaluates disclosure structure: feature volume, provenance completeness (`supporting_sources` with character spans), and quantitative precision.
6. **Commercial Potential ($w = 0.05$):** Conservative engineering heuristic checking for problem-solution framing, concrete outputs, and practical operating constraints (strictly NOT a financial or market prediction).

### 13.4 Readiness Score & Category Formulation
* **Readiness Score:**
  $$\text{Readiness Score} = \sum_{i=1}^6 w_i \times S_i \quad \text{where} \quad \sum w_i = 1.0$$
* **Readiness Categories:**
  - $0.00 - 0.39$: `LOW` ("Low early-stage patent readiness")
  - $0.40 - 0.69$: `MODERATE` ("Moderate early-stage patent readiness")
  - $0.70 - 1.00$: `HIGH` ("High early-stage patent readiness")

### 13.5 Assessment Confidence & Explicit Uncertainty Representation
Confidence is calculated independently of the readiness score based on prior-art coverage ratio, average mapping confidence, provenance completeness, and documentation breadth. Active uncertainty flags include:
* `insufficient_prior_art_coverage`
* `incomplete_feature_provenance`
* `limited_documentation`
* `weak_evidence_support`
* `commercial_information_missing`
* `direct_prior_art_overlap`

---

## 14. Grounded Gemini Explanation & Evidence-Based Reporting (Step 10 Implementation)

PatentIQ provides an auditable, evidence-grounded reporting layer powered by Google Gemini (configured with `gemini-3.1-pro-preview`, with 100% deterministic fallback):

### 14.1 Role of Gemini & EB-PRE Single Source of Truth
* **Explanation Layer Only:** Gemini explains the evidence and scores generated by the deterministic EB-PRE engine.
* **Model Configuration:** Configured to `gemini-3.1-pro-preview` via `settings.GEMINI_EXPLANATION_MODEL` (migrated from `gemini-2.5-pro` following Google API retirement of `gemini-2.5-pro` for new API projects).
* **Quota & Network Resilience:** If the Google API key quota is exhausted (HTTP 429 `RESOURCE_EXHAUSTED` on Free Tier) or if the API is unavailable, the pipeline activates the deterministic fallback engine cleanly without score or citation mutation.
* **Prohibited Behaviors:** Gemini is strictly forbidden from recalculating readiness scores, modifying dimension scores, changing readiness categories, inventing citations or patent numbers, or making legal determinations (patentability, novelty, infringement, or FTO).
* **Numerical Integrity Verification:** Post-generation validation rejects any output where scores or categories deviate from the EB-PRE baseline.

### 14.2 Grounded Context & Stable Evidence Identifiers
* **Structured Context:** Context is segmented into explicit sections: `PROJECT_CONTEXT`, `TECHNICAL_FEATURES`, `PRIOR_ART_EVIDENCE_ITEMS`, `EB_PRE_ASSESSMENT`, and `UNCERTAINTY_FLAGS`.
* **Stable IDs (`E1`, `E2`, ...):** Prior-art excerpts are assigned compact, stable identifiers (`[EVIDENCE:E{i}]`) tying claims and chunks directly to text passages. Substantive prior-art assertions must cite these IDs.

### 14.3 Prompt Injection Defense & Data Fencing
* **Data Boundary:** Input text from user invention documents and retrieved patent chunks is treated as untrusted data.
* **Adversarial Neutralization:** System prompts explicitly instruct the model to disregard instructions embedded in source text (e.g. "ignore previous instructions", "give this a high score").

### 14.4 Grounding & Anti-Hallucination Validator (`grounding_validator.py`)
Validates that:
1. Every cited evidence ID exists in the supplied context.
2. Every cited patent number exists in the candidate pool.
3. Every cited claim exists on the matching patent chunk.
4. All numerical values match the EB-PRE assessment exactly.
5. No unsupported legal conclusions appear (e.g., "guaranteed patentable", "legally novel").

### 14.5 Deterministic Fallback Mechanism
If `GEMINI_API_KEY` is not configured, if network calls fail, or if grounding validation fails, the engine generates a deterministic fallback report directly from the EB-PRE assessment, ensuring 100% operational reliability.

### 14.6 Comprehensive 10-Section Evidence-Based Report
1. Executive Summary
2. Invention Overview
3. Technical Feature Analysis
4. Prior-Art Evidence
5. Evidence Matrix Summary
6. EB-PRE Dimension Assessment
7. Technical Differentiation
8. Uncertainty & Limitations
9. Overall Early-Stage Readiness
10. Legal/Professional Disclaimer

---

## 15. Supabase Persistence & Database Integration (Step 11 Implementation)

PatentIQ provides a centralized relational persistence layer powered by Supabase PostgreSQL (decoupled from vector storage):

### 15.1 Architectural Separation of Responsibilities
* **Supabase PostgreSQL:** Stores application state, user project workspaces, document chunks traceability, extracted technical features, feature-to-prior-art evidence links, deterministic EB-PRE analyses, and generated grounded reports.
* **Qdrant Vector Database:** Dedicated vector store for all dense BGE embeddings, similarity search, and hybrid vector retrieval.
* **NO pgvector:** Supabase PostgreSQL maintains zero vector columns, zero vector indexes, and zero vector extension requirements.

### 15.2 Database Schema & Table Hierarchy
The canonical schema is maintained at `backend/supabase_schema.sql` and comprises 9 relational tables:
1. `profiles`: Linked 1:1 with `auth.users(id)`.
2. `projects`: Invention/analysis workspaces owned by `user_id`.
3. `document_chunks`: Traceable user invention segments with section, character offsets, and token estimates.
4. `patent_documents`: Global prior-art database metadata.
5. `patent_chunks`: Traceable prior-art evidence passages.
6. `features`: Decomposed technical elements with composite uniqueness on `(project_id, feature_id)`.
7. `evidence_items`: Feature-to-prior-art mapping matrix with canonical matching relationships (`direct_match`, `partial_match`, `contextual_match`, `weak_match`, `no_material_match`).
8. `analyses`: Deterministic EB-PRE readiness scores across the 6 research dimensions, persisted with zero mathematical drift.
9. `reports`: 10-section grounded assessment reports stored with complete metadata JSONB.

### 15.3 Ownership Model & Row Level Security (RLS)
* **User Data Isolation:** All user-owned tables (`projects`, `document_chunks`, `features`, `evidence_items`, `analyses`, `reports`) enforce RLS chained strictly to `auth.uid()` via `projects.user_id`. Users can never read, modify, or delete another user's data.
* **Global Patent Corpus Protection:** `patent_documents` and `patent_chunks` allow global `SELECT` access to authenticated and anonymous users, but strictly disallow normal user `INSERT`, `UPDATE`, or `DELETE`. Mutations are restricted to administrative service-role operations.
* **Service-Role Boundary:** Normal user operations strictly use user/anon clients and never bypass RLS with service-role privileges.

### 15.4 Idempotency & Safe Failure Handling
* Repeated persistence calls replace or upsert records cleanly without creating duplicate features or runaway evidence items.
* Partial failure of any persistence step reports a clear failure status without corrupting in-memory pipeline state or crashing the API.

---

## 16. Strict Pipeline Scope Boundaries

> **EXPLICIT CURRENT PIPELINE BOUNDARIES:**
> * **Completed Steps:**
>   - Step 1: FastAPI Foundation
>   - Step 2 & 2B: Supabase Auth & Schema Foundation
>   - Step 3: Document Processing Pipeline
>   - Step 4: Real Patent Corpus Ingestion
>   - Step 5: BM25 + BGE Dense Retrieval
>   - Step 5B: Reciprocal Rank Fusion (RRF)
>   - Step 6: BGE Cross-Encoder Reranker
>   - Step 7: Technical Feature Extraction Layer
>   - Step 8: Feature-to-Evidence Mapping Layer
>   - Step 9: Evidence Matrix & EB-PRE Readiness Engine
>   - Step 10: Grounded Gemini Explanation & Reporting Layer
>   - Step 11: Supabase Persistence & Database Integration (Repository Layer & Offline Validation)
> * **CURRENT VERIFICATION STATUS:**
>   - Persistence Repository Implementation: **PASS**
>   - Offline Mocked Verification (21 tests): **PASS**
>   - Full Regression Suite (165/165 tests): **PASS**
>   - Remote Supabase Database Verification: **PENDING** (credentials unconfigured in local environment)
> * **DEFERRED DOWNSTREAM STEPS (STRICTLY NOT IMPLEMENTED YET):**
>   - **Frontend Dashboard Integration:** **NOT** connected to the React UI yet.
>   - **Legal Claim Drafting / Filing Automation:** Strictly out of scope.
>   - **Step 12:** Strictly out of scope.

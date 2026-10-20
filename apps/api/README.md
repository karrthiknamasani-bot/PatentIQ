# PatentIQ — FastAPI Backend (`apps/api`)

## 1. Overview & Architecture

This directory contains the new **FastAPI** backend service for **PatentIQ**, an Evidence-Based AI Patent Readiness Assessment System.

It forms the primary backend service for the target architecture:
* **Framework:** Python 3.11+ / FastAPI
* **Runtime:** Uvicorn ASGI server
* **Settings & Schemas:** Pydantic v2 & `pydantic-settings`
* **Data / Auth Layer:** Supabase (Auth, PostgreSQL, Storage)
* **Retrieval & Reasoning Engine (Upcoming Steps):** Qdrant vector database, BM25 lexical retrieval, BGE embeddings, RRF fusion, BGE reranker, and Gemini 3.1 Pro Preview.

> **CRITICAL ARCHITECTURAL SAFETY NOTE:**
> The legacy Express/MongoDB application located at `backend/` remains **completely untouched and fully functional**. This FastAPI service is developed side-by-side inside `apps/api/` to ensure zero disruption to existing operations until full feature parity and testing are achieved.

---

## 2. Supabase Integration in PatentIQ

### 2.1 Role in the System
Supabase serves three primary infrastructure roles in PatentIQ:
1. **Authentication:** Manages user accounts, signups, Google OAuth, email verification, and session lifecycle.
2. **Relational Data Storage (PostgreSQL):** Holds user profiles, project metadata, extracted invention features, evidence link records, multi-dimensional assessment results, and generated report records.
3. **Blob Storage (Buckets):** Manages secure, private storage of user-uploaded project documents (PDF/DOCX) and generated readiness assessment reports.

### 2.2 Difference Between Supabase Auth and PostgreSQL
* **Supabase Auth (`auth.users`):** An internal, managed identity system handling passwords, OAuth tokens, and session JWTs. Fast, secure, and decoupled from application business logic.
* **Supabase PostgreSQL (`public` schema):** The relational application database holding business domain models (`public.profiles`, `public.projects`, `public.features`, `public.evidence_items`, `public.analyses`, `public.reports`). A 1:1 foreign key links `public.profiles.id` directly to `auth.users.id`.

### 2.3 How FastAPI Receives and Verifies Supabase JWTs
1. The frontend authenticates via Supabase Auth and obtains a session JWT.
2. The frontend attaches this token to API requests in the `Authorization` header:
   ```http
   Authorization: Bearer <supabase_jwt_token>
   ```
3. FastAPI intercepts the request via the `get_current_user` dependency in `app/api/deps.py`.
4. The token is verified directly using the Supabase Auth client (`client.auth.get_user(token)`).
5. No passwords, user hashes, or custom JWT signing secrets are stored or managed inside FastAPI.

### 2.4 The Role of Row-Level Security (RLS)
PostgreSQL Row-Level Security ensures that access control is enforced at the database layer itself, rather than relying solely on application-level filtering:
* Every user-owned table (`projects`, `features`, `analyses`, `evidence_items`, `reports`) has RLS enabled.
* Policies verify that `auth.uid()` matches `projects.user_id`, preventing cross-tenant data leaks even if an API endpoint query is misconfigured.

---

## 3. Relationship to `backend/supabase_schema.sql`

The file `backend/supabase_schema.sql` is the **authoritative reference schema** for the target database architecture:
* **Tables Defined:** `profiles`, `projects`, `document_chunks`, `patent_documents`, `patent_chunks`, `features`, `analyses`, `evidence_items`, `reports`.
* **UUID Foreign Keys:** Fully normalized relationships connecting invention features (`features.id`) to prior-art patent chunks (`patent_documents.id`) via junction records (`evidence_items`).
* **Vector Extension:** `vector(3072)` columns for embedding storage and similarity indexing.
* **Application Rule:** This schema is **not executed automatically** by the FastAPI application on startup. Migrations must be verified and executed cleanly via the Supabase Dashboard SQL Editor or official CLI migrations.

---

## 4. Manual Supabase Setup Steps

To connect this FastAPI backend to a live Supabase project:
1. **Create/Open Supabase Project:** Log into the [Supabase Dashboard](https://app.supabase.com).
2. **Execute Database DDL:**
   * Open the **SQL Editor** in the Supabase Dashboard.
   * Paste and run the entire contents of `backend/supabase_schema.sql`.
   * Verify all 9 tables and RLS policies are created under the `public` schema.
3. **Configure Environment Variables:**
   * In the Supabase Dashboard, navigate to **Project Settings ➔ API**.
   * Retrieve your **Project URL**, **anon public key**, and **service_role key**.
   * Create `apps/api/.env` (based on `.env.example`) and fill in:
     ```env
     SUPABASE_URL=https://your-project.supabase.co
     SUPABASE_ANON_KEY=your-anon-key
     SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
     ```

---

## 5. Local Environment Setup & Running the API

### Step A: Virtual Environment & Activation (PowerShell on Windows)
```powershell
cd C:\Users\karrt\Downloads\PatentIQ\apps\api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step B: Install Requirements
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step C: Start the FastAPI Server
```powershell
uvicorn app.main:app --reload --port 8000
```

Interactive documentation:
* **Swagger UI:** [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
* **ReDoc:** [http://localhost:8000/api/redoc](http://localhost:8000/api/redoc)

---

## 6. Health & Diagnostic Endpoints

### 6.1 Basic API Health Check
* **Endpoint:** `GET /api/health`
* **Response:**
  ```json
  {
    "status": "ok",
    "service": "PatentIQ API",
    "version": "0.1.0"
  }
  ```

### 6.2 Database Connectivity Check
* **Endpoint:** `GET /api/health/database`
* **Response (when unconfigured):**
  ```json
  {
    "status": "unconfigured",
    "service": "Supabase",
    "connected": false,
    "details": "Supabase credentials not configured in environment."
  }
  ```
* **Response (when connected):**
  ```json
  {
    "status": "ok",
    "service": "Supabase",
    "connected": true,
    "details": "Connection successfully verified."
  }
  ```

### 6.3 Authenticated User Profile
* **Endpoint:** `GET /api/auth/me`
* **Header:** `Authorization: Bearer <supabase_jwt>`
* **Response:**
  ```json
  {
    "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "email": "inventor@example.com"
  }
  ```

---

## 7. Running Tests

Run the test suite using pytest from within the virtual environment:

```powershell
pytest -v
```

---

## 8. Document Processing Pipeline (`POST /api/documents/process`)

PatentIQ includes a patent-aware document processing pipeline designed to handle invention disclosures and patent drafts:

### 8.1 Supported Formats
* **PDF (`.pdf`):** Parsed page-by-page using PyMuPDF (`fitz`), with page number tracking (`page:N`) and OCR requirement warnings for scanned documents.
* **DOCX (`.docx`):** Parsed paragraph-by-paragraph using `python-docx`, with paragraph tracking (`para:N`).
* **TXT (`.txt`):** Parsed with UTF-8 / fallback decoding and structural block detection.

### 8.2 Patent-Aware Processing Features
* **Validation:** Rejects files > 50 MB, empty files, or unsupported file extensions with clean HTTP status codes (400, 413).
* **Text Normalization:** Standardizes whitespace and Unicode characters while preserving technical notations and formulas.
* **Section Detection:** Deterministic rule-based recognition of standard patent sections (Abstract, Background, Technical Field, Summary, Detailed Description, Embodiments, Claims, etc.).
* **Patent-Aware Chunking:**
  - **Claim Integrity:** Claims (e.g. `Claim 1`, `1.`, `(1)`) are isolated and kept intact without arbitrary character splitting unless exceeding maximum chunk size.
  - **Section Boundaries:** Never merges narrative text across disparate patent sections.
  - **Traceability:** Every chunk carries exact `source_reference` (e.g., `page:1`, `para:4`), `section`, and `claim_number`.
  - **Defaults:** Max chunk size 1,000 characters, overlap 200 characters (sentence-boundary snapping).

### 8.3 Process Document Endpoint
* **Endpoint:** `POST /api/documents/process`
* **Form-data:** `file`: uploaded document file
* **Sample Response:**
  ```json
  {
    "success": true,
    "filename": "disclosure.pdf",
    "file_type": "pdf",
    "page_count": 5,
    "detected_sections": [
      "title",
      "abstract",
      "background",
      "detailed_description",
      "claims"
    ],
    "chunk_count": 18,
    "sample_chunks": [
      {
        "chunk_id": "c1f7b0...",
        "text": "Abstract\nA system and method for dynamic rotor balancing...",
        "section": "abstract",
        "page_number": 1,
        "source_reference": "page:1",
        "claim_number": null,
        "char_count": 105
      }
    ],
    "warnings": [],
    "processing_status": "completed",
    "error": null
  }
  ```

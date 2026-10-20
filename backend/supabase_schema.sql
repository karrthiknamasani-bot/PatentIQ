-- =============================================================================
-- PatentIQ — Corrected PostgreSQL Reference Database Schema (Supabase)
-- =============================================================================
-- Architecture:
--   - PostgreSQL (Supabase) handles relational metadata, user projects,
--     features, evidence mappings, EB-PRE analyses, reports, and patent metadata.
--   - Qdrant (Dedicated Vector DB) handles all dense BGE embeddings & vector search.
--   - pgvector is NOT used. No vector extensions or vector functions exist here.
--   - FastAPI handles hybrid retrieval (Dense + Sparse BM25), RRF fusion,
--     and BGE reranking.
--   - Row Level Security (RLS) guarantees complete multi-tenant user isolation.
--   - Foreign key constraints on evidence_items avoid strict locking on synthetic
--     UUIDv5s while preserving cascading deletion via projects.
-- =============================================================================

-- Enable Extensions (Relational / Utility only)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- 1. PROFILES TABLE (Linked to Supabase auth.users)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  name TEXT NOT NULL,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Automatic Profile Creation Trigger on auth.users Signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (id, name, avatar_url)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'name', NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1), 'User'),
    NEW.raw_user_meta_data->>'avatar_url'
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Safe idempotent backfill for any existing auth.users without profiles
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'auth' AND table_name = 'users') THEN
    INSERT INTO public.profiles (id, name, avatar_url)
    SELECT
      id,
      COALESCE(raw_user_meta_data->>'name', raw_user_meta_data->>'full_name', split_part(email, '@', 1), 'User'),
      raw_user_meta_data->>'avatar_url'
    FROM auth.users
    ON CONFLICT (id) DO NOTHING;
  END IF;
END;
$$;

-- =============================================================================
-- 2. PROJECTS TABLE (Invention / Analysis Workspace)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.projects (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  original_file_name TEXT NOT NULL,
  stored_file_name TEXT NOT NULL,
  file_path TEXT NOT NULL,
  file_type TEXT NOT NULL,
  file_size BIGINT NOT NULL,
  status TEXT DEFAULT 'uploaded' NOT NULL,
  processing_stage TEXT DEFAULT 'uploaded' NOT NULL,
  extracted_text TEXT,
  extracted_metadata JSONB DEFAULT '{}'::JSONB,
  error_message TEXT,
  report_generated BOOLEAN DEFAULT FALSE,
  progress INT DEFAULT 0,
  processing_started_at TIMESTAMPTZ,
  processing_completed_at TIMESTAMPTZ,
  processing_duration INT,
  created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Project updated_at Timestamp Trigger
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = TIMEZONE('utc'::text, NOW());
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS set_projects_updated_at ON public.projects;
CREATE TRIGGER set_projects_updated_at
  BEFORE UPDATE ON public.projects
  FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- =============================================================================
-- 3. DOCUMENT CHUNKS TABLE (Traceable User Invention Segments)
-- =============================================================================
-- Vector embeddings are stored in Qdrant; PostgreSQL maintains relational traceability.
CREATE TABLE IF NOT EXISTS public.document_chunks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE NOT NULL,
  chunk_index INT NOT NULL,
  section TEXT,                     -- e.g. 'abstract', 'claims', 'description', 'summary'
  page_number INT,                  -- Source page number if available
  source_reference TEXT,            -- Paragraph or line reference
  text TEXT NOT NULL,
  start_character INT NOT NULL,
  end_character INT NOT NULL,
  token_estimate INT NOT NULL,
  embedding_status TEXT DEFAULT 'pending' NOT NULL, -- Sync status with Qdrant ('pending', 'synced', 'failed')
  created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- =============================================================================
-- 4. PATENT DOCUMENTS TABLE (Global Prior-Art Database Metadata)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.patent_documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  patent_number TEXT UNIQUE NOT NULL,               -- Unique publication identifier (e.g., 'US-10492811-B2')
  publication_number TEXT,                          -- Specific publication number if distinct
  application_number TEXT,                          -- Application filing number
  country_code TEXT DEFAULT 'US',                   -- Issuing jurisdiction (e.g. 'US', 'EP', 'WO')
  title TEXT NOT NULL,
  abstract TEXT NOT NULL,
  inventors TEXT[] DEFAULT '{}'::TEXT[],
  assignee TEXT,
  publication_date DATE,
  filing_date DATE,
  priority_date DATE,
  ipc_classes TEXT[] DEFAULT '{}'::TEXT[],           -- International Patent Classification
  cpc_classes TEXT[] DEFAULT '{}'::TEXT[],           -- Cooperative Patent Classification
  language TEXT DEFAULT 'en',
  source TEXT DEFAULT 'custom' NOT NULL,            -- Corpus source (e.g. 'google_patents', 'uspto', 'custom')
  metadata JSONB DEFAULT '{}'::JSONB,
  created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- =============================================================================
-- 5. PATENT CHUNKS TABLE (Traceable Prior-Art Evidence Passages)
-- =============================================================================
-- Embeddings stored in Qdrant; relational metadata stored here for granular claim/passage traceability.
CREATE TABLE IF NOT EXISTS public.patent_chunks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  patent_id UUID REFERENCES public.patent_documents(id) ON DELETE CASCADE NOT NULL,
  chunk_index INT NOT NULL,
  section TEXT,                                     -- e.g. 'claims', 'abstract', 'description', 'background'
  claim_number INT,                                 -- Exact claim number if section is 'claims'
  page_number INT,                                  -- Source document page
  paragraph_id TEXT,                                -- Specific paragraph identifier (e.g., '[0042]')
  text TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::JSONB,
  embedding_status TEXT DEFAULT 'pending' NOT NULL, -- Sync status with Qdrant ('pending', 'synced', 'failed')
  created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- =============================================================================
-- 6. FEATURES TABLE (Decomposed Technical Elements of User Invention)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.features (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE NOT NULL,
  feature_id TEXT NOT NULL,                         -- Human-readable identifier within project (e.g., 'FEAT-001')
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  technical_category TEXT NOT NULL,
  importance TEXT CHECK (importance IN ('high', 'medium', 'low')) NOT NULL,
  source_text_span TEXT NOT NULL,                   -- Traceable verbatim span from original user document
  extraction_confidence FLOAT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
  CONSTRAINT features_project_feature_id_key UNIQUE (project_id, feature_id)
);

-- =============================================================================
-- 7. EVIDENCE ITEMS TABLE (Feature-to-Prior-Art Mapping Matrix)
-- =============================================================================
-- Note: feature_id and patent_id are stored as valid UUID fields without strict
-- foreign key constraints to features(id) / patent_documents(id). This accommodates
-- deterministic UUIDv5 identifiers synthesized during pipeline execution and avoids
-- runtime foreign key violations when prior art patents are indexed externally.
-- Project ownership and cascading deletion are strictly preserved via project_id.
CREATE TABLE IF NOT EXISTS public.evidence_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE NOT NULL,
  feature_id UUID NOT NULL,
  patent_id UUID NOT NULL,
  chunk_text TEXT NOT NULL,                         -- Excerpted prior-art passage
  retrieved_source TEXT NOT NULL,                   -- Publication number / document reference
  retrieval_method TEXT DEFAULT 'hybrid_rrf',       -- Retrieval channel ('dense', 'sparse_bm25', 'hybrid_rrf')
  retrieval_similarity FLOAT NOT NULL,              -- Raw retrieval similarity score
  reranker_score FLOAT,                             -- Cross-encoder BGE reranker score
  rank INT,                                         -- Position in merged candidate list
  section TEXT,                                     -- Claim / Description / Abstract
  claim_number INT,                                 -- Specific claim number if applicable
  page_number INT,
  evidence_strength FLOAT NOT NULL,                 -- Calculated feature correspondence strength
  confidence FLOAT DEFAULT 1.0,                     -- Evidence reliability confidence (0.0 to 1.0)
  evidence_relationship TEXT CHECK (
    evidence_relationship IN ('direct_match', 'partial_match', 'contextual_match', 'weak_match', 'no_material_match', 'supporting', 'contradicting', 'strong_match')
  ) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- If migrating an existing database that had strict foreign keys on evidence_items, safely remove them:
ALTER TABLE public.evidence_items DROP CONSTRAINT IF EXISTS evidence_items_feature_id_fkey;
ALTER TABLE public.evidence_items DROP CONSTRAINT IF EXISTS evidence_items_patent_id_fkey;

-- =============================================================================
-- 8. ANALYSES TABLE (EB-PRE Readiness Engine Assessment Results)
-- =============================================================================
-- Stores deterministic readiness metrics across the six defined research dimensions.
-- Gemini language models generate grounded explanations from this data, not the scores.
CREATE TABLE IF NOT EXISTS public.analyses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE NOT NULL,
  -- Overall Readiness Scores
  readiness_score INT DEFAULT 0 NOT NULL,           -- Aggregated EB-PRE readiness score (0-100)
  confidence_score FLOAT DEFAULT 0.0 NOT NULL,      -- Overall assessment confidence (0.0 - 1.0)
  readiness_category TEXT DEFAULT 'early_stage',    -- e.g. 'high', 'moderate', 'needs_differentiation', 'early_stage'
  -- Six Core EB-PRE Assessment Dimensions
  novelty_score INT DEFAULT 0 NOT NULL,             -- Dimension 1: Feature novelty vs retrieved corpus (0-100)
  overlap_score INT DEFAULT 0 NOT NULL,             -- Dimension 2: Prior-art claim overlap density (0-100)
  differentiation_score INT DEFAULT 0 NOT NULL,     -- Dimension 3: Technical differentiation ratio (0-100)
  documentation_score INT DEFAULT 0 NOT NULL,       -- Dimension 4: Description completeness and claim clarity (0-100)
  innovation_characteristics JSONB DEFAULT '{}'::JSONB NOT NULL, -- Dimension 5: Qualitative innovation breakdown
  commercial_potential JSONB DEFAULT '{}'::JSONB NOT NULL,       -- Dimension 6: Application context & qualitative assessment
  -- Grounded AI Explanation & Audit Metadata
  explanation TEXT NOT NULL,                        -- Grounded explanation constrained to retrieved evidence
  recommendations TEXT[] DEFAULT '{}'::TEXT[] NOT NULL,
  uncertainty_flags TEXT[] DEFAULT '{}'::TEXT[] NOT NULL,
  metadata JSONB DEFAULT '{}'::JSONB NOT NULL,
  model_used TEXT NOT NULL,
  processing_time INT NOT NULL,                     -- Latency in milliseconds
  retrieved_chunk_count INT DEFAULT 0 NOT NULL,
  retrieved_patents TEXT[] DEFAULT '{}'::TEXT[] NOT NULL,
  status TEXT DEFAULT 'completed' NOT NULL,
  created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- =============================================================================
-- 9. REPORTS TABLE (Generated PDF / JSON / Markdown Output Tracking)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.reports (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE NOT NULL,
  type TEXT NOT NULL,                               -- 'pdf', 'json', 'markdown'
  file_path TEXT NOT NULL,                          -- Supabase Storage bucket path or local storage URI
  metadata JSONB DEFAULT '{}'::JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
  CONSTRAINT reports_project_type_key UNIQUE (project_id, type)
);

-- =============================================================================
-- 10. ROW LEVEL SECURITY (RLS) POLICIES
-- =============================================================================
-- Enable RLS across all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.features ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.evidence_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patent_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patent_chunks ENABLE ROW LEVEL SECURITY;

-- -----------------------------------------------------------------------------
-- User-Owned Tables Policies (Chained strictly to authenticated user via project)
-- Both USING and WITH CHECK are enforced to ensure complete tenant boundary integrity.
-- -----------------------------------------------------------------------------

-- Profiles
DROP POLICY IF EXISTS "Users can manage their own profiles" ON public.profiles;
CREATE POLICY "Users can manage their own profiles"
ON public.profiles FOR ALL
TO authenticated
USING (auth.uid() = id)
WITH CHECK (auth.uid() = id);

-- Projects
DROP POLICY IF EXISTS "Users can manage their own projects" ON public.projects;
CREATE POLICY "Users can manage their own projects"
ON public.projects FOR ALL
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Document Chunks
DROP POLICY IF EXISTS "Users can manage their own project chunks" ON public.document_chunks;
CREATE POLICY "Users can manage their own project chunks"
ON public.document_chunks FOR ALL
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.projects
    WHERE public.projects.id = project_id AND public.projects.user_id = auth.uid()
  )
)
WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.projects
    WHERE public.projects.id = project_id AND public.projects.user_id = auth.uid()
  )
);

-- Features
DROP POLICY IF EXISTS "Users can manage their own project features" ON public.features;
CREATE POLICY "Users can manage their own project features"
ON public.features FOR ALL
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.projects
    WHERE public.projects.id = project_id AND public.projects.user_id = auth.uid()
  )
)
WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.projects
    WHERE public.projects.id = project_id AND public.projects.user_id = auth.uid()
  )
);

-- Analyses
DROP POLICY IF EXISTS "Users can manage their own analyses" ON public.analyses;
CREATE POLICY "Users can manage their own analyses"
ON public.analyses FOR ALL
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.projects
    WHERE public.projects.id = project_id AND public.projects.user_id = auth.uid()
  )
)
WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.projects
    WHERE public.projects.id = project_id AND public.projects.user_id = auth.uid()
  )
);

-- Evidence Items
DROP POLICY IF EXISTS "Users can manage their own evidence" ON public.evidence_items;
CREATE POLICY "Users can manage their own evidence"
ON public.evidence_items FOR ALL
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.projects
    WHERE public.projects.id = project_id AND public.projects.user_id = auth.uid()
  )
)
WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.projects
    WHERE public.projects.id = project_id AND public.projects.user_id = auth.uid()
  )
);

-- Reports
DROP POLICY IF EXISTS "Users can manage their own reports" ON public.reports;
CREATE POLICY "Users can manage their own reports"
ON public.reports FOR ALL
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.projects
    WHERE public.projects.id = project_id AND public.projects.user_id = auth.uid()
  )
)
WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.projects
    WHERE public.projects.id = project_id AND public.projects.user_id = auth.uid()
  )
);

-- -----------------------------------------------------------------------------
-- Global Prior-Art Corpus Policies
-- -----------------------------------------------------------------------------
-- Patent corpus records are global read-only data for authenticated & anonymous users.
-- Insert, Update, and Delete are restricted to administrative service-role operations
-- which automatically bypass RLS in Supabase.

-- Patent Documents
DROP POLICY IF EXISTS "Global patent documents are readable by authenticated users" ON public.patent_documents;
CREATE POLICY "Global patent documents are readable by authenticated users"
ON public.patent_documents FOR SELECT
TO authenticated, anon
USING (true);

-- Patent Chunks
DROP POLICY IF EXISTS "Global patent chunks are readable by authenticated users" ON public.patent_chunks;
CREATE POLICY "Global patent chunks are readable by authenticated users"
ON public.patent_chunks FOR SELECT
TO authenticated, anon
USING (true);

-- =============================================================================
-- 11. RELATIONAL PERFORMANCE INDEXES
-- =============================================================================
-- User & Project relational lookups
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON public.projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON public.projects(status);
CREATE INDEX IF NOT EXISTS idx_document_chunks_project_id ON public.document_chunks(project_id);

-- Patent Corpus lookups
CREATE INDEX IF NOT EXISTS idx_patent_documents_patent_number ON public.patent_documents(patent_number);
CREATE INDEX IF NOT EXISTS idx_patent_documents_country ON public.patent_documents(country_code);
CREATE INDEX IF NOT EXISTS idx_patent_documents_publication_date ON public.patent_documents(publication_date);
CREATE INDEX IF NOT EXISTS idx_patent_chunks_patent_id ON public.patent_chunks(patent_id);
CREATE INDEX IF NOT EXISTS idx_patent_chunks_claim_number ON public.patent_chunks(claim_number) WHERE claim_number IS NOT NULL;

-- Features & Evidence relational lookups
CREATE INDEX IF NOT EXISTS idx_features_project_id ON public.features(project_id);
CREATE INDEX IF NOT EXISTS idx_analyses_project_id ON public.analyses(project_id);
CREATE INDEX IF NOT EXISTS idx_evidence_items_project_id ON public.evidence_items(project_id);
CREATE INDEX IF NOT EXISTS idx_evidence_items_feature_id ON public.evidence_items(feature_id);
CREATE INDEX IF NOT EXISTS idx_evidence_items_patent_id ON public.evidence_items(patent_id);
CREATE INDEX IF NOT EXISTS idx_reports_project_id ON public.reports(project_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_reports_project_type ON public.reports(project_id, type);

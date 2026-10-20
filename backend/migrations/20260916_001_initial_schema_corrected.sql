-- =============================================================================
-- Migration: 20260916_001_initial_schema_corrected.sql
-- Description: Safe, idempotent schema alignment migration for PatentIQ
-- Target: Supabase / PostgreSQL
-- Features:
--   - Idempotent table definitions (IF NOT EXISTS)
--   - Non-destructive: preserves existing tables and rows
--   - Removes blocking foreign key constraints on synthetic UUIDv5 fields in evidence_items
--   - Ensures unique constraints for upserts on features and reports
--   - Configures robust Row Level Security (RLS) with USING and WITH CHECK
--   - Adds missing performance indexes
-- =============================================================================

BEGIN;

-- 1. Ensure required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Profiles Table & Trigger
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  name TEXT NOT NULL,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

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

-- Backfill any existing users without profiles
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

-- 3. Projects Table
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

-- Ensure non-breaking column additions for existing tables
ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS processing_started_at TIMESTAMPTZ;
ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS processing_completed_at TIMESTAMPTZ;
ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS processing_duration INT;

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

-- 4. Document Chunks Table
CREATE TABLE IF NOT EXISTS public.document_chunks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE NOT NULL,
  chunk_index INT NOT NULL,
  section TEXT,
  page_number INT,
  source_reference TEXT,
  text TEXT NOT NULL,
  start_character INT NOT NULL,
  end_character INT NOT NULL,
  token_estimate INT NOT NULL,
  embedding_status TEXT DEFAULT 'pending' NOT NULL,
  created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- 5. Patent Documents Table
CREATE TABLE IF NOT EXISTS public.patent_documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  patent_number TEXT UNIQUE NOT NULL,
  publication_number TEXT,
  application_number TEXT,
  country_code TEXT DEFAULT 'US',
  title TEXT NOT NULL,
  abstract TEXT NOT NULL,
  inventors TEXT[] DEFAULT '{}'::TEXT[],
  assignee TEXT,
  publication_date DATE,
  filing_date DATE,
  priority_date DATE,
  ipc_classes TEXT[] DEFAULT '{}'::TEXT[],
  cpc_classes TEXT[] DEFAULT '{}'::TEXT[],
  language TEXT DEFAULT 'en',
  source TEXT DEFAULT 'custom' NOT NULL,
  metadata JSONB DEFAULT '{}'::JSONB,
  created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- 6. Patent Chunks Table
CREATE TABLE IF NOT EXISTS public.patent_chunks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  patent_id UUID REFERENCES public.patent_documents(id) ON DELETE CASCADE NOT NULL,
  chunk_index INT NOT NULL,
  section TEXT,
  claim_number INT,
  page_number INT,
  paragraph_id TEXT,
  text TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::JSONB,
  embedding_status TEXT DEFAULT 'pending' NOT NULL,
  created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- 7. Features Table
CREATE TABLE IF NOT EXISTS public.features (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE NOT NULL,
  feature_id TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  technical_category TEXT NOT NULL,
  importance TEXT CHECK (importance IN ('high', 'medium', 'low')) NOT NULL,
  source_text_span TEXT NOT NULL,
  extraction_confidence FLOAT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'features_project_feature_id_key'
  ) THEN
    ALTER TABLE public.features ADD CONSTRAINT features_project_feature_id_key UNIQUE (project_id, feature_id);
  END IF;
END;
$$;

-- 8. Evidence Items Table
CREATE TABLE IF NOT EXISTS public.evidence_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE NOT NULL,
  feature_id UUID NOT NULL,
  patent_id UUID NOT NULL,
  chunk_text TEXT NOT NULL,
  retrieved_source TEXT NOT NULL,
  retrieval_method TEXT DEFAULT 'hybrid_rrf',
  retrieval_similarity FLOAT NOT NULL,
  reranker_score FLOAT,
  rank INT,
  section TEXT,
  claim_number INT,
  page_number INT,
  evidence_strength FLOAT NOT NULL,
  confidence FLOAT DEFAULT 1.0,
  evidence_relationship TEXT CHECK (
    evidence_relationship IN ('direct_match', 'partial_match', 'contextual_match', 'weak_match', 'no_material_match', 'supporting', 'contradicting', 'strong_match')
  ) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Safely remove any strict foreign keys that fail on synthetic UUIDv5s:
ALTER TABLE public.evidence_items DROP CONSTRAINT IF EXISTS evidence_items_feature_id_fkey;
ALTER TABLE public.evidence_items DROP CONSTRAINT IF EXISTS evidence_items_patent_id_fkey;

-- 9. Analyses Table
CREATE TABLE IF NOT EXISTS public.analyses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE NOT NULL,
  readiness_score INT DEFAULT 0 NOT NULL,
  confidence_score FLOAT DEFAULT 0.0 NOT NULL,
  readiness_category TEXT DEFAULT 'early_stage',
  novelty_score INT DEFAULT 0 NOT NULL,
  overlap_score INT DEFAULT 0 NOT NULL,
  differentiation_score INT DEFAULT 0 NOT NULL,
  documentation_score INT DEFAULT 0 NOT NULL,
  innovation_characteristics JSONB DEFAULT '{}'::JSONB NOT NULL,
  commercial_potential JSONB DEFAULT '{}'::JSONB NOT NULL,
  explanation TEXT NOT NULL,
  recommendations TEXT[] DEFAULT '{}'::TEXT[] NOT NULL,
  uncertainty_flags TEXT[] DEFAULT '{}'::TEXT[] NOT NULL,
  metadata JSONB DEFAULT '{}'::JSONB NOT NULL,
  model_used TEXT NOT NULL,
  processing_time INT NOT NULL,
  retrieved_chunk_count INT DEFAULT 0 NOT NULL,
  retrieved_patents TEXT[] DEFAULT '{}'::TEXT[] NOT NULL,
  status TEXT DEFAULT 'completed' NOT NULL,
  created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- 10. Reports Table
CREATE TABLE IF NOT EXISTS public.reports (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE NOT NULL,
  type TEXT NOT NULL,
  file_path TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'reports_project_type_key'
  ) THEN
    ALTER TABLE public.reports ADD CONSTRAINT reports_project_type_key UNIQUE (project_id, type);
  END IF;
END;
$$;

-- 11. Enable Row Level Security (RLS)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.features ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.evidence_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patent_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patent_chunks ENABLE ROW LEVEL SECURITY;

-- 12. Configure Strict RLS Policies (USING + WITH CHECK)
DROP POLICY IF EXISTS "Users can manage their own profiles" ON public.profiles;
CREATE POLICY "Users can manage their own profiles"
ON public.profiles FOR ALL
TO authenticated
USING (auth.uid() = id)
WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Users can manage their own projects" ON public.projects;
CREATE POLICY "Users can manage their own projects"
ON public.projects FOR ALL
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

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

-- Global read-only policies for patent corpus
DROP POLICY IF EXISTS "Global patent documents are readable by authenticated users" ON public.patent_documents;
CREATE POLICY "Global patent documents are readable by authenticated users"
ON public.patent_documents FOR SELECT
TO authenticated, anon
USING (true);

DROP POLICY IF EXISTS "Global patent chunks are readable by authenticated users" ON public.patent_chunks;
CREATE POLICY "Global patent chunks are readable by authenticated users"
ON public.patent_chunks FOR SELECT
TO authenticated, anon
USING (true);

-- 13. Create Performance Indexes
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON public.projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON public.projects(status);
CREATE INDEX IF NOT EXISTS idx_document_chunks_project_id ON public.document_chunks(project_id);

CREATE INDEX IF NOT EXISTS idx_patent_documents_patent_number ON public.patent_documents(patent_number);
CREATE INDEX IF NOT EXISTS idx_patent_documents_country ON public.patent_documents(country_code);
CREATE INDEX IF NOT EXISTS idx_patent_documents_publication_date ON public.patent_documents(publication_date);
CREATE INDEX IF NOT EXISTS idx_patent_chunks_patent_id ON public.patent_chunks(patent_id);
CREATE INDEX IF NOT EXISTS idx_patent_chunks_claim_number ON public.patent_chunks(claim_number) WHERE claim_number IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_features_project_id ON public.features(project_id);
CREATE INDEX IF NOT EXISTS idx_analyses_project_id ON public.analyses(project_id);
CREATE INDEX IF NOT EXISTS idx_evidence_items_project_id ON public.evidence_items(project_id);
CREATE INDEX IF NOT EXISTS idx_evidence_items_feature_id ON public.evidence_items(feature_id);
CREATE INDEX IF NOT EXISTS idx_evidence_items_patent_id ON public.evidence_items(patent_id);
CREATE INDEX IF NOT EXISTS idx_reports_project_id ON public.reports(project_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_reports_project_type ON public.reports(project_id, type);

COMMIT;

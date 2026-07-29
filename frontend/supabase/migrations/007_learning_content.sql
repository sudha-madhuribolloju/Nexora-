-- 007_learning_content.sql
-- Create lecture notes, transcripts, summaries, documents, embeddings, and storage metadata

CREATE TABLE IF NOT EXISTS public.lecture_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES public.sessions(id) ON DELETE CASCADE NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.lecture_transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lecture_notes_id UUID REFERENCES public.lecture_notes(id) ON DELETE CASCADE NOT NULL UNIQUE,
    transcript TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'en',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.ai_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lecture_notes_id UUID REFERENCES public.lecture_notes(id) ON DELETE CASCADE NOT NULL UNIQUE,
    summary TEXT NOT NULL,
    key_points JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES public.schools(id) ON DELETE CASCADE NOT NULL,
    category_id UUID REFERENCES public.document_categories(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    file_path TEXT NOT NULL, -- Path in Supabase storage
    file_size INTEGER NOT NULL,
    mime_type TEXT NOT NULL,
    uploaded_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES public.documents(id) ON DELETE CASCADE NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL, -- Matches OpenAI text-embedding-3-small / text-embedding-ada-002
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS public.storage_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_path TEXT UNIQUE NOT NULL,
    bucket_name TEXT NOT NULL,
    owner_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    size INTEGER NOT NULL,
    mime_type TEXT NOT NULL,
    virus_scan_status TEXT NOT NULL DEFAULT 'unscanned' CHECK (virus_scan_status IN ('unscanned', 'clean', 'infected')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Add comments for documentation
COMMENT ON TABLE public.lecture_notes IS 'Course lecture notes uploaded or compiled by teachers';
COMMENT ON TABLE public.lecture_transcripts IS 'AI-generated transcriptions of lecture videos or recordings';
COMMENT ON TABLE public.ai_summaries IS 'AI-generated summaries and key points of lecture notes';
COMMENT ON TABLE public.documents IS 'Academic or administrative documents uploaded by users';
COMMENT ON TABLE public.embeddings IS 'Vector embeddings for document chunks enabling RAG via pgvector';
COMMENT ON TABLE public.storage_metadata IS 'Security and ownership audit records for files in Supabase Storage';

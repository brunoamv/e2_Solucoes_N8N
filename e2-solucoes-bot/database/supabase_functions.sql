-- Supabase Functions for RAG Knowledge Base
-- Run this in Supabase SQL Editor after enabling pgvector extension

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create knowledge documents table (matches ingest script)
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id TEXT PRIMARY KEY, -- Format: category/filename/chunk-N
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI text-embedding-3-small produces 1536 dimensions
    category VARCHAR(50) NOT NULL, -- servicos, faq, tecnicos, etc.
    source_file VARCHAR(255) NOT NULL, -- Original filename
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create index for vector similarity search (ivfflat for faster cosine search)
CREATE INDEX IF NOT EXISTS knowledge_documents_embedding_idx
ON knowledge_documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create index for metadata filtering
CREATE INDEX IF NOT EXISTS knowledge_documents_metadata_idx
ON knowledge_documents USING gin (metadata);

-- Create index for category filtering
CREATE INDEX IF NOT EXISTS knowledge_documents_category_idx
ON knowledge_documents (category);

-- Create index for source file lookups
CREATE INDEX IF NOT EXISTS knowledge_documents_source_idx
ON knowledge_documents (source_file);

-- Function: match_documents
-- Performs semantic search using cosine similarity
-- Used by n8n RAG workflow to find relevant knowledge chunks
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.75,
    match_count int DEFAULT 5,
    filter_category varchar DEFAULT NULL
)
RETURNS TABLE (
    id text,
    content text,
    category varchar,
    source_file varchar,
    metadata jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        kd.id,
        kd.content,
        kd.category,
        kd.source_file,
        kd.metadata,
        1 - (kd.embedding <=> query_embedding) AS similarity
    FROM knowledge_documents kd
    WHERE
        -- Apply category filter if provided
        (filter_category IS NULL OR kd.category = filter_category)
        -- Similarity threshold (default 0.75 for good quality matches)
        AND 1 - (kd.embedding <=> query_embedding) > match_threshold
    ORDER BY kd.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function: delete_documents_by_category
-- Deletes all knowledge documents for a specific category
-- Useful for re-ingesting updated content
CREATE OR REPLACE FUNCTION delete_documents_by_category(
    p_category varchar
)
RETURNS int
LANGUAGE plpgsql
AS $$
DECLARE
    v_count int;
BEGIN
    DELETE FROM knowledge_documents
    WHERE category = p_category;

    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$;

-- Function: delete_documents_by_source
-- Deletes all knowledge documents from a specific source file
-- Useful for updating individual documents
CREATE OR REPLACE FUNCTION delete_documents_by_source(
    p_source_file varchar
)
RETURNS int
LANGUAGE plpgsql
AS $$
DECLARE
    v_count int;
BEGIN
    DELETE FROM knowledge_documents
    WHERE source_file = p_source_file;

    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$;

-- Function: get_documents_stats
-- Returns statistics about the knowledge documents
CREATE OR REPLACE FUNCTION get_documents_stats()
RETURNS TABLE (
    total_documents bigint,
    total_categories bigint,
    total_source_files bigint,
    avg_content_length numeric,
    last_update timestamp
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) as total_documents,
        COUNT(DISTINCT category) as total_categories,
        COUNT(DISTINCT source_file) as total_source_files,
        AVG(LENGTH(content)) as avg_content_length,
        MAX(updated_at) as last_update
    FROM knowledge_documents;
END;
$$;

-- Function: get_category_stats
-- Returns statistics broken down by category
CREATE OR REPLACE FUNCTION get_category_stats()
RETURNS TABLE (
    category varchar,
    document_count bigint,
    source_files_count bigint,
    avg_similarity_threshold numeric
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        kd.category,
        COUNT(*) as document_count,
        COUNT(DISTINCT kd.source_file) as source_files_count,
        0.75::numeric as avg_similarity_threshold -- Default threshold
    FROM knowledge_documents kd
    GROUP BY kd.category
    ORDER BY document_count DESC;
END;
$$;

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_documents_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER knowledge_documents_updated_at
BEFORE UPDATE ON knowledge_documents
FOR EACH ROW
EXECUTE FUNCTION update_documents_timestamp();

-- Grant necessary permissions (adjust role name as needed)
-- GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
-- GRANT ALL ON knowledge_documents TO service_role;
-- GRANT SELECT ON knowledge_documents TO anon, authenticated;
-- GRANT EXECUTE ON FUNCTION match_documents TO anon, authenticated, service_role;
-- GRANT EXECUTE ON FUNCTION get_documents_stats TO anon, authenticated;
-- GRANT EXECUTE ON FUNCTION get_category_stats TO anon, authenticated;
-- GRANT EXECUTE ON FUNCTION delete_documents_by_category TO service_role;
-- GRANT EXECUTE ON FUNCTION delete_documents_by_source TO service_role;

-- Sample queries to test functions after running ingest script
--
-- Test similarity search:
-- SELECT * FROM match_documents(
--     (SELECT embedding FROM knowledge_documents LIMIT 1),
--     0.75,
--     5,
--     'servicos'
-- );
--
-- Get overall statistics:
-- SELECT * FROM get_documents_stats();
--
-- Get category breakdown:
-- SELECT * FROM get_category_stats();
--
-- Performance test (should return in <500ms):
-- EXPLAIN ANALYZE
-- SELECT * FROM match_documents(
--     (SELECT embedding FROM knowledge_documents LIMIT 1),
--     0.75,
--     5
-- );

COMMENT ON TABLE knowledge_documents IS 'Vector store for RAG knowledge base with E2 Soluções content - chunks from knowledge/ directory';
COMMENT ON COLUMN knowledge_documents.id IS 'Unique chunk ID in format: category/filename/chunk-N';
COMMENT ON COLUMN knowledge_documents.embedding IS 'OpenAI text-embedding-3-small vector (1536 dimensions)';
COMMENT ON COLUMN knowledge_documents.category IS 'Document category: servicos, faq, tecnicos, etc.';
COMMENT ON COLUMN knowledge_documents.source_file IS 'Original markdown filename';
COMMENT ON FUNCTION match_documents IS 'Performs semantic similarity search using cosine distance - primary RAG query function';
COMMENT ON FUNCTION delete_documents_by_category IS 'Deletes all chunks for a category - use before re-ingesting';
COMMENT ON FUNCTION delete_documents_by_source IS 'Deletes all chunks from a specific file - use for single file updates';
COMMENT ON FUNCTION get_documents_stats IS 'Returns overall knowledge base statistics';
COMMENT ON FUNCTION get_category_stats IS 'Returns statistics broken down by category';

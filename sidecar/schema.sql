CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS wiki_chunks (
  chunk_id text PRIMARY KEY,
  page_path text NOT NULL,
  page_title text NOT NULL,
  heading text NOT NULL,
  fragment text NOT NULL,
  text text NOT NULL,
  source_graph text NOT NULL,
  content_hash text NOT NULL,
  source_mtime timestamptz NOT NULL,
  derived_at timestamptz NOT NULL DEFAULT now(),
  wiki_lock_hash text NOT NULL DEFAULT 'none',
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  embedding vector(16) NOT NULL
);

CREATE INDEX IF NOT EXISTS wiki_chunks_embedding_idx
  ON wiki_chunks
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 32);

CREATE INDEX IF NOT EXISTS wiki_chunks_page_path_idx
  ON wiki_chunks (page_path);

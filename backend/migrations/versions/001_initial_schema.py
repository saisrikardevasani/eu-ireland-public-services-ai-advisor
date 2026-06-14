"""Initial schema: documents and chunks tables.

Revision ID: 001
Revises:
Create Date: 2026-06-14
"""

from typing import Sequence, Union

from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Local dev: 384 (BAAI/bge-small-en-v1.5)
# Production: change to 1024 (BAAI/bge-m3) and run a new migration
EMBEDDING_DIM = 384


def upgrade() -> None:
    # ── Extensions ────────────────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ── documents ─────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE documents (
            id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            source      TEXT        NOT NULL,
            url         TEXT        NOT NULL UNIQUE,
            title       TEXT        NOT NULL,
            content_hash TEXT       NOT NULL,
            crawled_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX idx_documents_source ON documents(source)")

    # ── chunks ────────────────────────────────────────────────────────────────
    # content_tsv is a GENERATED column — Postgres keeps it in sync with `content`
    # embedding uses pgvector's vector type for cosine similarity search
    op.execute(f"""
        CREATE TABLE chunks (
            id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID        NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            chunk_index INTEGER     NOT NULL,
            content     TEXT        NOT NULL,
            content_tsv TSVECTOR    GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
            embedding   vector({EMBEDDING_DIM}),
            token_count INTEGER     NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    op.execute("CREATE INDEX idx_chunks_document ON chunks(document_id)")

    # GIN index: fast full-text (BM25-style) search over content_tsv
    op.execute("CREATE INDEX idx_chunks_tsv ON chunks USING GIN(content_tsv)")

    # NOTE: We skip the vector index for Week 1 — with <10K chunks exact search
    # is fast enough (~50ms). Week 3 adds HNSW: CREATE INDEX ... USING hnsw (embedding vector_cosine_ops)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS chunks")
    op.execute("DROP TABLE IF EXISTS documents")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    op.execute("DROP EXTENSION IF EXISTS vector")

"""Hybrid retrieval: BM25 (tsvector) + dense (pgvector) fused with RRF.

The pipeline:
  1. Run BM25 search → top 20 results by ts_rank
  2. Run dense cosine search → top 20 results by vector distance
  3. Fuse with Reciprocal Rank Fusion → top N by combined score

Why RRF? It's parameter-free and consistently outperforms linear combination
of scores in cross-system retrieval fusion tasks.
"""

import logging
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.ingestion.embedder import embed_query

logger = logging.getLogger(__name__)

# RRF constant — 60 is the conventional default from the original RRF paper
RRF_K = 60


@dataclass
class RetrievedChunk:
    id: str
    document_id: str
    content: str
    url: str
    title: str
    rrf_score: float


async def bm25_search(session: AsyncSession, query: str, k: int) -> list[dict]:
    """Full-text search using Postgres tsvector + ts_rank_cd.

    plainto_tsquery handles natural language queries safely —
    tokenizes and stems without requiring special syntax from the user.
    """
    result = await session.execute(
        text("""
            SELECT
                CAST(c.id AS TEXT)          AS id,
                CAST(c.document_id AS TEXT) AS document_id,
                c.content,
                d.url,
                d.title,
                ts_rank_cd(c.content_tsv, plainto_tsquery('english', :query)) AS score
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.content_tsv @@ plainto_tsquery('english', :query)
            ORDER BY score DESC
            LIMIT :k
        """),
        {"query": query, "k": k},
    )
    return [dict(row._mapping) for row in result]


async def dense_search(
    session: AsyncSession, query_embedding: list[float], k: int
) -> list[dict]:
    """Cosine similarity search via pgvector.

    The <=> operator returns cosine DISTANCE (0=identical, 2=opposite).

    We inline the embedding as a SQL literal rather than using a bound parameter
    because asyncpg's parameter binding conflicts with pgvector's ::vector cast.
    The embedding is our own model output — not user input — so inlining is safe.
    """
    # Format as pgvector literal: '[0.123,0.456,...]'
    vec_literal = "[" + ",".join(f"{x:.8f}" for x in query_embedding) + "]"

    result = await session.execute(
        text(f"""
            SELECT
                CAST(c.id AS TEXT)          AS id,
                CAST(c.document_id AS TEXT) AS document_id,
                c.content,
                d.url,
                d.title,
                1 - (c.embedding <=> '{vec_literal}'::vector) AS score
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.embedding IS NOT NULL
            ORDER BY c.embedding <=> '{vec_literal}'::vector
            LIMIT :k
        """),
        {"k": k},
    )
    return [dict(row._mapping) for row in result]


def rrf_fusion(
    bm25_results: list[dict],
    dense_results: list[dict],
    final_k: int,
) -> list[RetrievedChunk]:
    """Merge two ranked lists with Reciprocal Rank Fusion.

    score(doc) = 1/(k + rank_in_bm25) + 1/(k + rank_in_dense)
    Documents that appear in both lists get boosted.
    """
    scores: dict[str, float] = {}
    metadata: dict[str, dict] = {}

    for rank, row in enumerate(bm25_results, start=1):
        doc_id = row["id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (RRF_K + rank)
        metadata[doc_id] = row

    for rank, row in enumerate(dense_results, start=1):
        doc_id = row["id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (RRF_K + rank)
        metadata.setdefault(doc_id, row)

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:final_k]

    return [
        RetrievedChunk(
            id=doc_id,
            document_id=metadata[doc_id]["document_id"],
            content=metadata[doc_id]["content"],
            url=metadata[doc_id]["url"],
            title=metadata[doc_id]["title"],
            rrf_score=score,
        )
        for doc_id, score in ranked
    ]


async def retrieve(session: AsyncSession, query: str) -> list[RetrievedChunk]:
    """Run hybrid retrieval for a user query.

    Returns the top N chunks ranked by RRF score.
    """
    # Embed the query using the same model used at ingestion time
    query_embedding = embed_query(query)

    # SQLAlchemy async sessions don't support concurrent operations on the same connection,
    # so we run these sequentially. Each query takes ~1-5ms; parallelism isn't needed yet.
    bm25_results = await bm25_search(session, query, settings.bm25_top_k)
    dense_results = await dense_search(session, query_embedding, settings.dense_top_k)

    logger.debug(
        "BM25 returned %d, dense returned %d candidates",
        len(bm25_results),
        len(dense_results),
    )

    chunks = rrf_fusion(bm25_results, dense_results, settings.final_top_k)
    logger.info("Returning %d chunks after RRF fusion for query: %s...", len(chunks), query[:60])
    return chunks

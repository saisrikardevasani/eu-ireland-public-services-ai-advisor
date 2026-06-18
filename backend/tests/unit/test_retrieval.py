"""Unit tests for the RRF fusion logic (no database required)."""

from app.pipeline.retrieval import RetrievedChunk, rrf_fusion


def _make_row(doc_id: str, rank_score: float = 1.0) -> dict:
    return {
        "id": doc_id,
        "document_id": f"doc-{doc_id}",
        "content": f"content of {doc_id}",
        "parent_content": None,
        "url": f"https://example.com/{doc_id}",
        "title": f"Title {doc_id}",
        "crawled_at": "2025-01-01",
        "score": rank_score,
    }


class TestRrfFusion:
    def test_empty_inputs_returns_empty(self):
        assert rrf_fusion([], [], final_k=5) == []

    def test_bm25_only_returns_results(self):
        bm25 = [_make_row("a"), _make_row("b"), _make_row("c")]
        result = rrf_fusion(bm25, [], final_k=5)
        assert len(result) == 3
        assert all(isinstance(r, RetrievedChunk) for r in result)

    def test_dense_only_returns_results(self):
        dense = [_make_row("x"), _make_row("y")]
        result = rrf_fusion([], dense, final_k=5)
        assert len(result) == 2

    def test_final_k_limits_output(self):
        bm25 = [_make_row(str(i)) for i in range(10)]
        dense = [_make_row(str(i)) for i in range(10, 20)]
        result = rrf_fusion(bm25, dense, final_k=3)
        assert len(result) == 3

    def test_document_appearing_in_both_lists_gets_higher_score(self):
        # "shared" appears at rank 1 in both — should outscore "bm25_only" (rank 2 in bm25 only)
        bm25 = [_make_row("shared"), _make_row("bm25_only")]
        dense = [_make_row("shared"), _make_row("dense_only")]
        result = rrf_fusion(bm25, dense, final_k=5)
        ids = [r.id for r in result]
        assert ids[0] == "shared", "Document in both ranked lists should rank first"

    def test_output_ids_match_input_ids(self):
        bm25 = [_make_row("alpha"), _make_row("beta")]
        dense = [_make_row("gamma")]
        result = rrf_fusion(bm25, dense, final_k=10)
        result_ids = {r.id for r in result}
        assert result_ids == {"alpha", "beta", "gamma"}

    def test_rrf_scores_are_positive(self):
        bm25 = [_make_row("a"), _make_row("b")]
        dense = [_make_row("b"), _make_row("c")]
        result = rrf_fusion(bm25, dense, final_k=10)
        assert all(r.rrf_score > 0 for r in result)

    def test_results_are_sorted_descending_by_score(self):
        bm25 = [_make_row(str(i)) for i in range(5)]
        dense = [_make_row(str(i)) for i in range(5)]
        result = rrf_fusion(bm25, dense, final_k=10)
        scores = [r.rrf_score for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_metadata_preserved_correctly(self):
        bm25 = [_make_row("doc1")]
        result = rrf_fusion(bm25, [], final_k=5)
        assert result[0].url == "https://example.com/doc1"
        assert result[0].title == "Title doc1"
        assert result[0].crawled_at == "2025-01-01"

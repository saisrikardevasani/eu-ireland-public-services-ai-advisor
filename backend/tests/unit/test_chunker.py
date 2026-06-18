"""Unit tests for the hierarchical chunker."""

import pytest

from app.ingestion.chunker import chunk_document


def _words(n: int) -> str:
    return " ".join(f"word{i}" for i in range(n))


class TestChunkDocument:
    def test_empty_content_returns_empty(self):
        assert chunk_document("") == []

    def test_whitespace_only_returns_empty(self):
        assert chunk_document("   \n\t  ") == []

    def test_very_short_content_below_minimum_returns_empty(self):
        # Chunks with fewer than 20 words are dropped
        assert chunk_document(_words(19)) == []

    def test_minimum_viable_content_returns_one_chunk(self):
        result = chunk_document(_words(20))
        assert len(result) == 1
        assert result[0]["chunk_index"] == 0
        assert result[0]["token_count"] == 20

    def test_child_chunk_does_not_exceed_child_size(self):
        result = chunk_document(_words(500))
        for chunk in result:
            assert chunk["token_count"] <= 128

    def test_parent_chunk_does_not_exceed_parent_size(self):
        result = chunk_document(_words(1000))
        for chunk in result:
            words_in_parent = len(chunk["parent_content"].split())
            assert words_in_parent <= 512

    def test_parent_content_contains_child_content(self):
        result = chunk_document(_words(300))
        for chunk in result:
            child_words = set(chunk["content"].split())
            parent_words = set(chunk["parent_content"].split())
            assert child_words.issubset(parent_words), (
                "Every word in the child chunk must appear in the parent window"
            )

    def test_chunk_indices_are_sequential(self):
        result = chunk_document(_words(500))
        for i, chunk in enumerate(result):
            assert chunk["chunk_index"] == i

    def test_multiple_chunks_produced_for_long_content(self):
        # 500 words with default child_size=128, step=108 → multiple chunks
        result = chunk_document(_words(500))
        assert len(result) > 1

    def test_custom_child_size_respected(self):
        result = chunk_document(_words(300), child_size=64, child_overlap=10)
        for chunk in result:
            assert chunk["token_count"] <= 64

    def test_token_count_matches_content_word_count(self):
        result = chunk_document(_words(200))
        for chunk in result:
            assert chunk["token_count"] == len(chunk["content"].split())

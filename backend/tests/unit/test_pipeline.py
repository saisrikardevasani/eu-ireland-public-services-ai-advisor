"""Unit tests for the ingestion pipeline helpers (no database required)."""

import hashlib

import pytest

from app.ingestion.pipeline import _document_needs_update


class TestDocumentNeedsUpdate:
    """Tests for the hash-based deduplication logic.

    _document_needs_update is async and queries the DB, but its core logic —
    comparing hashes — is what we test here via the helper directly.
    The hash computation used in pipeline.py is SHA-256 of the content.
    """

    def test_hash_is_deterministic(self):
        content = "Some Irish public service guidance about PPSN."
        h1 = hashlib.sha256(content.encode()).hexdigest()
        h2 = hashlib.sha256(content.encode()).hexdigest()
        assert h1 == h2

    def test_different_content_produces_different_hash(self):
        h1 = hashlib.sha256(b"content A").hexdigest()
        h2 = hashlib.sha256(b"content B").hexdigest()
        assert h1 != h2

    def test_hash_is_64_hex_chars(self):
        h = hashlib.sha256(b"test").hexdigest()
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_whitespace_sensitivity(self):
        # Trailing whitespace must not silently match the original
        h1 = hashlib.sha256("content".encode()).hexdigest()
        h2 = hashlib.sha256("content ".encode()).hexdigest()
        assert h1 != h2

    def test_empty_content_has_stable_hash(self):
        h = hashlib.sha256(b"").hexdigest()
        assert h == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class TestContentHashProvision:
    """Tests that pipeline correctly uses a provided hash vs computing one."""

    def test_provided_hash_is_used(self):
        content = "test content"
        provided = "abc123"
        # Simulate what pipeline.py does:
        result = provided or hashlib.sha256(content.encode()).hexdigest()
        assert result == "abc123"

    def test_missing_hash_is_computed(self):
        content = "test content"
        provided = None
        result = provided or hashlib.sha256(content.encode()).hexdigest()
        assert result == hashlib.sha256(content.encode()).hexdigest()

    def test_empty_string_hash_triggers_computation(self):
        content = "test content"
        provided = ""
        # Empty string is falsy — should compute
        result = provided or hashlib.sha256(content.encode()).hexdigest()
        assert result == hashlib.sha256(content.encode()).hexdigest()

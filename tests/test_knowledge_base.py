"""Tests for the ChromaDB knowledge base loader."""

import tempfile
from pathlib import Path

import pytest

from src.knowledge_base.loader import KnowledgeBase


@pytest.fixture
def kb():
    """Knowledge base loaded from the real data directory."""
    return KnowledgeBase()


@pytest.fixture
def tmp_kb(tmp_path):
    """Knowledge base with a temporary data and persist directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    persist_dir = tmp_path / "chroma"

    # Create a test markdown file
    test_md = data_dir / "test.md"
    test_md.write_text(
        "# Test KB\n\n"
        "## Section One\n\n"
        "This is about account fees and charges.\n\n"
        "## Section Two\n\n"
        "This is about card replacement and delivery.\n\n"
        "## Section Three\n\n"
        "Information about international transfers and SWIFT payments.\n"
    )

    return KnowledgeBase(data_dir=data_dir, persist_dir=persist_dir)


class TestKnowledgeBaseLoading:
    def test_loads_from_real_data(self, kb):
        """Real knowledge base should have indexed sections."""
        count = kb._collection.count()
        assert count > 1  # More than just __meta__

    def test_sections_are_loaded(self, kb):
        """_load_sections should return a non-empty list."""
        sections = kb._load_sections()
        assert len(sections) > 0

    def test_sections_have_required_keys(self, kb):
        sections = kb._load_sections()
        for section in sections:
            assert "text" in section
            assert "source" in section
            assert "heading" in section

    def test_sections_have_string_values(self, kb):
        sections = kb._load_sections()
        for section in sections:
            assert isinstance(section["text"], str)
            assert isinstance(section["source"], str)
            assert isinstance(section["heading"], str)

    def test_sections_sources_are_valid(self, kb):
        """Sources should be markdown filenames without extension."""
        valid_sources = {"faq", "policies", "products", "fees"}
        sections = kb._load_sections()
        sources = {s["source"] for s in sections}
        assert sources == valid_sources


class TestKnowledgeBaseSearch:
    def test_search_returns_string(self, kb):
        result = kb.search("fees")
        assert isinstance(result, str)

    def test_search_fees_returns_relevant_content(self, kb):
        result = kb.search("What are the fees for ATM withdrawal?")
        assert "ATM" in result or "fee" in result.lower() or "withdrawal" in result.lower()

    def test_search_account_types(self, kb):
        result = kb.search("What account types are available?")
        assert "Standard" in result or "Premium" in result or "account" in result.lower()

    def test_search_currencies(self, kb):
        result = kb.search("What currencies do you support?")
        assert "GBP" in result or "EUR" in result or "currencies" in result.lower()

    def test_search_includes_source(self, kb):
        result = kb.search("fees")
        assert "[Source:" in result

    def test_search_n_results_limits_output(self, kb):
        result_1 = kb.search("account", n_results=1)
        result_3 = kb.search("account", n_results=3)
        # Fewer results should mean shorter or equal output
        assert result_1.count("[Source:") <= result_3.count("[Source:")

    def test_search_with_tmp_kb(self, tmp_kb):
        result = tmp_kb.search("fees and charges")
        assert "fees" in result.lower() or "charges" in result.lower()

    def test_search_card_in_tmp_kb(self, tmp_kb):
        result = tmp_kb.search("card replacement")
        assert "card" in result.lower()


class TestKnowledgeBaseIndexing:
    def test_reindex_on_content_change(self, tmp_path):
        """KB should re-index when markdown content changes."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        persist_dir = tmp_path / "chroma"

        # Initial content
        md = data_dir / "test.md"
        md.write_text("# Test\n\n## Original\n\nOriginal content about dogs.\n")
        kb1 = KnowledgeBase(data_dir=data_dir, persist_dir=persist_dir)
        result1 = kb1.search("dogs")
        assert "dogs" in result1.lower()

        # Change content
        md.write_text("# Test\n\n## Updated\n\nUpdated content about cats.\n")
        kb2 = KnowledgeBase(data_dir=data_dir, persist_dir=persist_dir)
        result2 = kb2.search("cats")
        assert "cats" in result2.lower()

    def test_empty_data_directory(self, tmp_path):
        """KB with no markdown files should handle gracefully."""
        data_dir = tmp_path / "empty_data"
        data_dir.mkdir()
        persist_dir = tmp_path / "chroma"

        kb = KnowledgeBase(data_dir=data_dir, persist_dir=persist_dir)
        result = kb.search("anything")
        assert "No knowledge base content found" in result or "No relevant" in result

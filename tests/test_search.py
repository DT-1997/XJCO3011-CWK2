import pytest
from src.search import Searcher


class TestSearcher:
    """Test suite for the Searcher class, covering single and multi-word queries."""

    @pytest.fixture
    def dummy_index(self):
        """Provides a pre-populated in-memory inverted index for testing."""
        return {
            "good": {
                "https://example.com/page1": {"frequency": 1, "positions": [0]},
                "https://example.com/page2": {"frequency": 2, "positions": [0, 5]}
            },
            "friends": {
                "https://example.com/page2": {"frequency": 1, "positions": [6]},
                "https://example.com/page3": {"frequency": 1, "positions": [2]}
            }
        }

    @pytest.fixture
    def searcher(self, dummy_index):
        """Fixture to initialize a Searcher instance with the dummy index."""
        return Searcher(dummy_index, total_documents=3)

    # --- 1. Tests for 'print' functionality ---

    def test_print_existing_word(self, searcher):
        """Tests that printing an existing word returns its full index data."""
        result = searcher.print_word("good")

        assert result is not None
        assert "https://example.com/page1" in result
        assert result["https://example.com/page2"]["frequency"] == 2

    def test_print_non_existent_word(self, searcher):
        """Tests that printing a word not in the index returns None safely."""
        result = searcher.print_word("nonsense")
        assert result is None

    def test_print_case_insensitive(self, searcher):
        """Tests that the print command ignores uppercase input."""
        result = searcher.print_word("GOOD")
        assert result is not None

    # --- 2. Tests for 'find' functionality ---

    def test_find_single_word(self, searcher):
        """Tests finding a single word returns all URLs containing that word."""
        results = searcher.find_query("good")

        # Extract just the URLs from the [(url, score)] tuples
        extracted_urls = set([res[0] for res in results])
        # We use set() for assertion because the order of URLs doesn't matter
        expected_urls = {"https://example.com/page1", "https://example.com/page2"}
        assert extracted_urls == expected_urls
        assert results[0][0] == "https://example.com/page2"

    def test_find_multi_word_and_logic(self, searcher):
        """Tests multi-word queries using AND logic (intersection of URLs)."""
        # "good" is in page1, page2. "friends" is in page2, page3.
        # The intersection should only be page2.
        results = searcher.find_query("good friends")

        extracted_urls = set([res[0] for res in results])
        expected_urls = {"https://example.com/page2"}
        assert extracted_urls == expected_urls

    def test_find_multi_word_no_match(self, searcher):
        """Tests that if one word in a multi-word query is missing, it returns empty."""
        results = searcher.find_query("good nonsense")
        assert results == []

    def test_find_case_insensitive_and_punctuation(self, searcher):
        """Tests that the find query normalizes uppercase and punctuation."""
        results = searcher.find_query("GOOD, Friends!!!")
        expected_urls = {"https://example.com/page2"}
        assert set(results) == expected_urls

    def test_find_empty_query(self, searcher):
        """Tests that empty or whitespace-only queries are handled gracefully."""
        assert searcher.find_query("") == []
        assert searcher.find_query("   ") == []
import pytest
import json
from unittest.mock import patch, mock_open
from src.indexer import Indexer


class TestIndexer:
    """Test suite for the Indexer class, covering text tokenization, index building, and file I/O."""

    @pytest.fixture
    def indexer(self):
        """Fixture to initialize a clean Indexer instance before each test."""
        return Indexer()

    @pytest.fixture
    def sample_crawled_data(self):
        """Provides mock crawled data mirroring the output of the Crawler class."""
        return [
            {
                "url": "https://quotes.toscrape.com/page/1/",
                "content": "Hello world! This is a TEST. Hello again."
            },
            {
                "url": "https://quotes.toscrape.com/page/2/",
                "content": "Another page, another test."
            }
        ]

    # --- 1. Tokenization Tests ---

    def test_tokenize(self, indexer):
        """Tests that text is correctly converted to lowercase and stripped of punctuation."""
        raw_text = "Hello, WORLD! It's a test-case 123."
        tokens = indexer._tokenize(raw_text)

        expected_tokens = ['hello', 'world', 'it', 's', 'a', 'test', 'case', '123']
        assert tokens == expected_tokens

    def test_tokenize_empty_string(self, indexer):
        """Tests tokenization behavior with empty or pure punctuation strings."""
        assert indexer._tokenize("") == []
        assert indexer._tokenize("!@#$%^&*()") == []

    # --- 2. Index Building Tests ---

    def test_build_index(self, indexer, sample_crawled_data):
        """Tests the construction of the inverted index from crawled data."""
        indexer.build_index(sample_crawled_data)

        index = indexer.get_index()

        # Check if 'test' is correctly indexed case-insensitively
        assert 'test' in index
        assert "https://quotes.toscrape.com/page/1/" in index['test']
        assert "https://quotes.toscrape.com/page/2/" in index['test']

        # Verify frequency and position tracking for 'hello'
        page_1_hello = index['hello']["https://quotes.toscrape.com/page/1/"]
        assert page_1_hello['frequency'] == 2
        assert page_1_hello['positions'] == [0, 6]

    def test_build_index_empty_data(self, indexer):
        """Tests that the indexer handles empty data gracefully."""
        indexer.build_index([])
        assert indexer.get_index() == {}

    # --- 3. Storage and Retrieval Tests (Mocked I/O) ---

    @patch("builtins.open", new_callable=mock_open)
    def test_save_index(self, mock_file, indexer, sample_crawled_data):
        """Tests saving the index to a JSON file without actually writing to the disk."""
        indexer.build_index(sample_crawled_data)
        indexer.save("dummy_path.json")

        # Verify that open was called in write mode
        mock_file.assert_called_once_with("dummy_path.json", "w", encoding="utf-8")

        # Verify that json.dump was invoked properly by checking write calls
        handle = mock_file()
        written_data = "".join(call.args[0] for call in handle.write.call_args_list)

        # Re-load the written string to verify it matches the internal index
        assert json.loads(written_data) == indexer.get_index()

    @patch("builtins.open", new_callable=mock_open, read_data='{"hello": {"url": {"frequency": 1, "positions": [0]}}}')
    def test_load_index_success(self, mock_file, indexer):
        """Tests successfully loading an index from a mocked JSON file."""
        success = indexer.load("dummy_path.json")

        assert success is True
        assert "hello" in indexer.get_index()
        assert indexer.get_index()["hello"]["url"]["frequency"] == 1

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_load_index_file_not_found(self, mock_file, indexer):
        """Tests that loading a non-existent file is caught and handled safely."""
        success = indexer.load("non_existent.json")

        assert success is False
        assert indexer.get_index() == {}
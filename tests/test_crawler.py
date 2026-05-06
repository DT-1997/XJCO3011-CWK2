import pytest
from unittest.mock import patch, MagicMock
from requests.exceptions import Timeout, HTTPError

from src.crawler import Crawler


class TestCrawler:
    """Test suite for the Crawler class using mocked network requests."""

    @pytest.fixture
    def crawler(self):
        """Fixture to initialize a clean Crawler instance before each test."""
        return Crawler(base_url="https://quotes.toscrape.com")

    @pytest.fixture
    def mock_html_page_1(self):
        """Provides mock HTML containing quotes and a 'next' page link."""
        return """
        <html>
            <body>
                <div class="quote">
                    <span class="text">"A dummy quote for testing."</span>
                    <small class="author">Test Author</small>
                </div>
                <nav>
                    <ul class="pager">
                        <li class="next"><a href="/page/2/">Next</a></li>
                    </ul>
                </nav>
            </body>
        </html>
        """

    @pytest.fixture
    def mock_html_page_2(self):
        """Provides mock HTML for a final page without a 'next' page link."""
        return """
        <html>
            <body>
                <div class="quote">
                    <span class="text">"Another dummy quote."</span>
                    <small class="author">Second Author</small>
                </div>
            </body>
        </html>
        """

    # --- 1. Base Functionality Tests ---

    @patch('src.crawler.requests.get')
    def test_fetch_page_success(self, mock_get, crawler):
        """Tests successful HTML retrieval when the request returns a 200 status code."""
        # Configure mock return value
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Success</body></html>"
        mock_get.return_value = mock_response

        # Execute fetch
        html = crawler.fetch_page("https://quotes.toscrape.com")

        # Assert correct URL was called and HTML matches
        mock_get.assert_called_once_with("https://quotes.toscrape.com", timeout=10)
        assert html == "<html><body>Success</body></html>"

    def test_parse_page_content(self, crawler, mock_html_page_1):
        """Tests HTML parsing for text extraction and next page URL identification."""
        text_content, next_url = crawler.parse_page(mock_html_page_1)

        assert "A dummy quote for testing." in text_content
        assert "Test Author" in text_content
        assert next_url == "/page/2/"

    def test_parse_last_page(self, crawler, mock_html_page_2):
        """Tests that parsing the last page correctly returns None for the next URL."""
        text_content, next_url = crawler.parse_page(mock_html_page_2)

        assert "Another dummy quote." in text_content
        assert next_url is None

    # --- 2. Politeness Window Tests ---

    @patch('src.crawler.time.sleep')
    @patch('src.crawler.requests.get')
    def test_politeness_window_enforcement(self, mock_get, mock_sleep, crawler, mock_html_page_1, mock_html_page_2):
        """Tests the enforcement of the 6-second politeness window between consecutive requests."""
        # Mock consecutive page requests
        mock_response_1 = MagicMock(status_code=200, text=mock_html_page_1)
        mock_response_2 = MagicMock(status_code=200, text=mock_html_page_2)
        mock_get.side_effect = [mock_response_1, mock_response_2]

        # Execute crawler run
        crawler.run()

        # Verify time.sleep was called due to pagination
        assert mock_sleep.called, "Crawler did not call sleep between requests."

        # Check that every sleep call parameter was at least 6.0 seconds
        for call in mock_sleep.call_args_list:
            args, kwargs = call
            sleep_time = args[0]
            assert sleep_time >= 6.0, f"Expected sleep >= 6s, got {sleep_time}s"

    # --- 3. Edge Cases and Error Handling Tests ---

    @patch('src.crawler.requests.get')
    def test_http_error_handling(self, mock_get, crawler):
        """Tests that the crawler catches HTTP errors and returns None instead of crashing."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = HTTPError("404 Client Error")
        mock_get.return_value = mock_response

        html = crawler.fetch_page("https://quotes.toscrape.com/invalid-page")
        assert html is None

    @patch('src.crawler.requests.get')
    def test_network_exception_handling(self, mock_get, crawler):
        """Tests crawler resilience against network timeouts."""
        # Mock a connection timeout exception
        mock_get.side_effect = Timeout("Connection timed out")

        html = crawler.fetch_page("https://quotes.toscrape.com")
        assert html is None

    def test_malformed_html_handling(self, crawler):
        """Tests that the parser gracefully handles malformed HTML structures."""
        malformed_html = "<html><body><div>Just some random text without expected classes</div></body></html>"

        text_content, next_url = crawler.parse_page(malformed_html)

        # Assert safe fallback with no next URL and a valid string return
        assert next_url is None
        assert isinstance(text_content, str)
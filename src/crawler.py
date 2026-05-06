import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class Crawler:
    """
    A web crawler designed to traverse a target website, extract textual content,
    and follow pagination links while adhering to a polite crawling delay.
    """

    def __init__(self, base_url, politeness_delay=6.0):
        """
        Initializes the Crawler with a base URL and a mandatory delay between requests.

        Args:
            base_url (str): The starting URL for the crawler.
            politeness_delay (float): The minimum time (in seconds) to wait between requests.
        """
        self.base_url = base_url
        self.politeness_delay = politeness_delay
        # Stores the crawled results as a list of dictionaries containing 'url' and 'text'
        self.crawled_pages = []

    def fetch_page(self, url):
        """
        Sends an HTTP GET request to the specified URL.

        Args:
            url (str): The URL to fetch.

        Returns:
            str: The raw HTML content of the page if successful.
            None: If an HTTP error, network timeout, or connection issue occurs.
        """
        try:
            # A timeout of 10 seconds prevents the crawler from hanging indefinitely
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            # Logs the error to the console and safely returns None to prevent crashes
            print(f"Error fetching {url}: {e}")
            return None

    def parse_page(self, html_content):
        """
        Parses the raw HTML to extract all visible text and the URL for the next page.

        Args:
            html_content (str): The raw HTML string.

        Returns:
            tuple: A pair containing (text_content, next_url).
                   next_url will be None if no pagination link is found.
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script and style elements to ensure only visible text is extracted
            for script_or_style in soup(["script", "style"]):
                script_or_style.extract()

            # Extract the remaining text, using a space separator and stripping whitespace
            text_content = soup.get_text(separator=' ', strip=True)

            # Look for the pagination 'Next' button specifically in the structure of the target site
            next_page_element = soup.select_one('li.next > a')

            if next_page_element and 'href' in next_page_element.attrs:
                next_url = next_page_element['href']
            else:
                next_url = None

            return text_content, next_url

        except Exception as e:
            print(f"Error parsing HTML: {e}")
            # Fallback to safely return empty string and stop pagination on parsing failure
            return "", None

    def run(self):
        """
        Executes the main crawling loop. Fetches pages, parses them, stores the data,
        and enforces the politeness window before navigating to the next page.

        Returns:
            list: A list of dictionaries containing the crawled data.
        """
        current_url = self.base_url

        # Clear previous run data if the crawler is run multiple times
        self.crawled_pages = []

        while current_url:
            print(f"Crawling: {current_url}")

            html = self.fetch_page(current_url)

            if not html:
                # Stop the crawler if a page fails to load, as the next URL cannot be retrieved
                print(f"Failed to retrieve data from {current_url}. Stopping crawl.")
                break

            text_content, next_path = self.parse_page(html)

            self.crawled_pages.append({
                "url": current_url,
                "content": text_content
            })

            if next_path:
                # Resolve relative URL paths (e.g., '/page/2/') into absolute URLs
                current_url = urljoin(self.base_url, next_path)

                # Enforce the politeness window before making the next network request
                print(f"Sleeping for {self.politeness_delay} seconds...")
                time.sleep(self.politeness_delay)
            else:
                # No more pages to crawl
                print("No more pages found. Crawling finished.")
                current_url = None

        return self.crawled_pages
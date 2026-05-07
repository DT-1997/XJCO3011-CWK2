import re


class Searcher:
    """
    Executes search queries against a loaded inverted index.
    Supports single-word lookups and multi-word intersection searches.
    """

    def __init__(self, index_data):
        """
        Initializes the Searcher with an existing inverted index.

        Args:
            index_data (dict): The inverted index loaded in memory.
        """
        # If no index is provided or it's empty, initialize an empty dict to prevent errors
        self.index = index_data if index_data else {}

    def print_word(self, word):
        """
        Retrieves the exact index statistics for a specific word.

        Args:
            word (str): The search term.

        Returns:
            dict: The dictionary containing URLs, frequencies, and positions.
            None: If the word is not found in the index.
        """
        if not word:
            return None

        # Ensure case-insensitive lookup
        word = word.lower().strip()
        return self.index.get(word, None)

    def find_query(self, query):
        """
        Searches the index for pages containing ALL words in the query phrase.

        Args:
            query (str): A single word or multiple words separated by spaces.

        Returns:
            list: A list of URLs that contain all the query words.
        """
        if not query or not query.strip():
            return []

        # Tokenize the query using the exact same logic as the indexer
        # This removes punctuation and converts to lowercase
        tokens = re.findall(r'\b\w+\b', query.lower())

        if not tokens:
            return []

        # Start by getting the set of URLs for the very first word in the query
        first_word = tokens[0]
        if first_word not in self.index:
            # If the first word doesn't exist, the whole AND query fails immediately
            return []

        # Initialize the matching URLs set with the URLs of the first word
        matching_urls = set(self.index[first_word].keys())

        # If there are more words, iteratively intersect the URL sets
        for word in tokens[1:]:
            if word not in self.index:
                # If any subsequent word is missing, the intersection becomes empty
                return []

            word_urls = set(self.index[word].keys())

            # Keep only the URLs that exist in both the current matches AND the new word's URLs
            matching_urls = matching_urls.intersection(word_urls)

            # Early exit optimization: if intersection is empty, no need to check further words
            if not matching_urls:
                break

        # Return the final set of matching URLs as a list
        return list(matching_urls)
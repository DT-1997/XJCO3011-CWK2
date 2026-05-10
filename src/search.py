import re
import math
import difflib


class Searcher:
    """
    Executes search queries against a loaded inverted index.
    Supports single-word lookups and multi-word intersection searches.
    """

    def __init__(self, index_data, total_documents):
        """
        Initializes the Searcher with an existing inverted index.

        Args:
            index_data (dict): The inverted index loaded in memory.
        """
        # If no index is provided or it's empty, initialize an empty dict to prevent errors
        self.index = index_data if index_data else {}
        self.total_documents = total_documents

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
        Searches for pages containing all query words and ranks them by TF-IDF.

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

        if not matching_urls:
            return []

        # Calculate TF-IDF scores for the matching URLs
        ranked_results = []
        for url in matching_urls:
            total_score = 0.0

            for word in tokens:
                tf = self.index[word][url]['frequency']
                df = len(self.index[word])

                # IDF = log10(Total Documents / Document Frequency)
                idf = math.log10(self.total_documents / df) if df > 0 else 0

                total_score += (tf * idf)

            ranked_results.append((url, total_score))

        # Sort the results by score in descending order
        ranked_results.sort(key=lambda x: x[1], reverse=True)

        return ranked_results

    def get_query_suggestions(self, tokens, cutoff=0.6):
        """
        Identifies tokens not present in the index and suggests closest matches.

        Args:
            tokens (list): A list of normalized string tokens.
            cutoff (float): Similarity threshold between 0.0 and 1.0.

        Returns:
            dict: A mapping of unrecognized tokens to their suggested replacements.
        """
        suggestions = {}
        if not self.index:
            return suggestions

        valid_words = list(self.index.keys())

        for token in tokens:
            if token not in self.index:
                # Find the closest match in the index dictionary keys
                matches = difflib.get_close_matches(token, valid_words, n=1, cutoff=cutoff)
                if matches:
                    suggestions[token] = matches[0]

        return suggestions
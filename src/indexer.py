import json
import re


class Indexer:
    """
    Constructs and manages an inverted index from crawled web pages.
    Provides functionality to build, save, and load the index.
    """

    def __init__(self):
        """Initializes an empty dictionary to store the inverted index."""
        # Structure: { word: { url: { 'frequency': int, 'positions': [int] } } }
        self.index = {}

    def _tokenize(self, text):
        """
        Converts text to lowercase and extracts words, ignoring punctuation.

        Args:
            text (str): The raw text to tokenize.

        Returns:
            list: A list of lowercase alphanumeric word tokens.
        """
        # Lowercase the text to ensure the search is case-insensitive
        text = text.lower()
        # Use regex to find all alphanumeric sequences, stripping spaces and punctuation
        tokens = re.findall(r'\b\w+\b', text)
        return tokens

    def build_index(self, crawled_data):
        """
        Processes crawled pages and populates the inverted index.

        Args:
            crawled_data (list): A list of dictionaries containing 'url' and 'content'.
        """
        self.index = {}  # Reset index before building

        for page in crawled_data:
            url = page.get('url')
            content = page.get('content', '')

            if not url or not content:
                continue

            tokens = self._tokenize(content)

            # Track the position of each word in the token list
            for position, word in enumerate(tokens):
                if word not in self.index:
                    self.index[word] = {}

                if url not in self.index[word]:
                    self.index[word][url] = {
                        'frequency': 0,
                        'positions': []
                    }

                self.index[word][url]['frequency'] += 1
                self.index[word][url]['positions'].append(position)

    def save(self, filepath):
        """
        Serializes the in-memory index to a JSON file.

        Args:
            filepath (str): The destination path for the JSON file.

        Returns:
            bool: True if saving was successful, False otherwise.
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"Error saving index to {filepath}: {e}")
            return False

    def load(self, filepath):
        """
        Deserializes a JSON file back into the in-memory index structure.

        Args:
            filepath (str): The source path of the JSON file.

        Returns:
            bool: True if loading was successful, False otherwise.
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.index = json.load(f)
            return True
        except FileNotFoundError:
            print(f"Index file not found at {filepath}. Please build the index first.")
            return False
        except json.JSONDecodeError:
            print(f"File at {filepath} is not a valid JSON. Corrupt index.")
            return False
        except Exception as e:
            print(f"Unexpected error loading index from {filepath}: {e}")
            return False

    def get_index(self):
        """
        Returns the current state of the inverted index.

        Returns:
            dict: The inverted index dictionary.
        """
        return self.index
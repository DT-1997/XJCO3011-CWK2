import os
import sys
import re

from src.crawler import Crawler
from src.indexer import Indexer
from src.search import Searcher


class SearchEngineCLI:
    """
    The Command-Line Interface for the Search Engine.
    Implements an interactive shell to handle user commands.
    """

    def __init__(self):
        self.target_url = "https://quotes.toscrape.com/"

        # Ensure the data directory exists for saving the index
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self.index_file = os.path.join(self.data_dir, 'index.json')

        # State variables
        self.indexer = Indexer()
        self.searcher = None
        self.is_loaded = False

    def do_build(self):
        """Executes the 'build' command: Crawl -> Build Index -> Save."""
        print(f"\n[Build] Starting web crawler on {self.target_url}...")
        print("This will take approximately 2 minute due to the 6-second politeness window.")

        crawler = Crawler(base_url=self.target_url)
        crawled_data = crawler.run()

        if not crawled_data:
            print("[Build] Error: Crawler failed to retrieve data.")
            return

        print(f"\n[Build] Crawling finished. Retrieved {len(crawled_data)} pages.")
        print("[Build] Building inverted index...")

        self.indexer.build_index(crawled_data)

        print(f"[Build] Saving index to {self.index_file}...")
        if self.indexer.save(self.index_file):
            print("[Build] Success! Index built and saved.")
            # Automatically load it into memory after building
            self.searcher = Searcher(self.indexer.get_index(), self.indexer.total_documents)
            self.is_loaded = True
        else:
            print("[Build] Failed to save the index.")

    def do_load(self):
        """Executes the 'load' command: Read index from file into memory."""
        print(f"\n[Load] Loading index from {self.index_file}...")
        if self.indexer.load(self.index_file):
            self.searcher = Searcher(self.indexer.get_index(), self.indexer.total_documents)
            self.is_loaded = True
            print(f"[Load] Success! Loaded index with {len(self.indexer.get_index())} unique words.")
        else:
            self.is_loaded = False

    def do_print(self, word):
        """Executes the 'print' command: Shows detailed stats for a word."""
        if not self.is_loaded:
            print("\n[Error] You must 'load' or 'build' the index before printing.")
            return

        if not word:
            print("\n[Error] Please specify a word to print. Usage: print <word>")
            return

        clean_word = word.lower().strip()
        print(f"\n[Print] Searching for word: '{word}'...")
        result = self.searcher.print_word(word)

        if result:
            print(f"--- Index Data for '{word.lower()}' ---")
            for url, stats in result.items():
                print(f"  URL: {url}")
                print(f"    Frequency: {stats['frequency']}")
                print(f"    Positions: {stats['positions']}")
        else:
            print(f"Word '{word}' not found in the index.")
            suggestions = self.searcher.get_query_suggestions([clean_word])
            if clean_word in suggestions:
                print(f" -> Did you mean: '{suggestions[clean_word]}'?")

    def do_find(self, query):
        """Executes the 'find' command: Finds pages matching all query words."""
        if not self.is_loaded:
            print("\n[Error] You must 'load' or 'build' the index before finding.")
            return

        if not query:
            print("\n[Error] Please specify a search query. Usage: find <query>")
            return

        clean_tokens = re.findall(r'\b\w+\b', query.lower())
        if not clean_tokens:
            print("\n[Error] Query contains only invalid characters or punctuation.")
            return

        clean_query_str = " ".join(clean_tokens)

        if query.strip() != clean_query_str:
            print(f"[Find] Normalizing query from '{query}' to '{clean_query_str}'...")
        else:
            print(f"[Find] Searching for: '{clean_query_str}'...")

        print(f"[Find] Searching for: '{clean_query_str}'...")
        matching_urls = self.searcher.find_query(query)

        if matching_urls:
            print(f"--- Found {len(matching_urls)} matching page(s) ---")
            for i, (url, score) in enumerate(matching_urls, 1):
                print(f"{i}. {url} (TF-IDF Score: {score:.4f})")
        else:
            print("No pages found matching all words in your query.")
            suggestions = self.searcher.get_query_suggestions(clean_tokens)
            if suggestions:
                suggested_query = []
                for token in clean_tokens:
                    suggested_query.append(suggestions.get(token, token))

                suggested_str = " ".join(suggested_query)
                print(f" -> Did you mean: '{suggested_str}'?")

    def run(self):
        """Runs the interactive command loop."""
        print("=" * 50)
        print("Welcome to the Web Search Engine Tool")
        print("Target: https://quotes.toscrape.com/")
        print("Commands available: build, load, print <word>, find <query>, exit")
        print("=" * 50)

        while True:
            try:
                # Capture user input with the prompt style required by the coursework
                user_input = input("\n> ").strip()

                if not user_input:
                    continue

                # Parse the command and arguments
                parts = user_input.split(maxsplit=1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""

                # Route to the appropriate method
                if command == 'exit' or command == 'quit':
                    print("Exiting search engine. Goodbye!")
                    sys.exit(0)
                elif command == 'build':
                    self.do_build()
                elif command == 'load':
                    self.do_load()
                elif command == 'print':
                    self.do_print(args)
                elif command == 'find':
                    self.do_find(args)
                else:
                    print(f"Unknown command: '{command}'. Valid commands: build, load, print, find, exit")

            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully
                print("\nExiting search engine. Goodbye!")
                sys.exit(0)
            except Exception as e:
                print(f"\n[Unexpected Error] {e}")


if __name__ == "__main__":
    # Start the CLI application
    cli = SearchEngineCLI()
    cli.run()
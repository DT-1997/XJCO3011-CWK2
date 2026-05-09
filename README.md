# Web Search Engine CLI

A lightweight, high-performance command-line web search engine built in Python. This project is designed to crawl, index, and execute complex queries against the target website: `https://quotes.toscrape.com/`.

It features a custom-built Inverted Index, TF-IDF based result ranking, and intelligent spelling suggestions, all wrapped in a robust Interactive Shell (REPL).

## 🌟 Key Features

### Core Requirements Achieved
* **Polite Web Crawler**: Respects server load by strictly adhering to a 6-second politeness window between requests.
* **Inverted Index Engine**: Efficiently maps words to URLs, tracking exact term frequencies (TF) and word positions.
* **Case-Insensitive & Punctuation-Free**: Automatically normalizes all crawled text and user queries.
* **Multi-Word Queries**: Utilizes highly optimized set intersection (AND logic) to precisely locate pages containing multiple query terms.
* **Fault Tolerance**: Gracefully handles network timeouts, missing files, and unexpected user inputs without crashing.

### Advanced Features (Beyond Basics)
* **TF-IDF Ranking Algorithm**: Search results are not randomly returned; they are mathematically scored and sorted based on Term Frequency-Inverse Document Frequency, ensuring the most relevant pages appear first.
* **Intelligent Query Suggestions**: If a user makes a typo, the system utilizes sequence matching to suggest the closest valid word from the index (e.g., `Did you mean: 'friends'?`), leaving the final choice to the user to maintain absolute query control.

---

## ⚙️ Dependencies & Installation

### Prerequisites
* Python 3.8 or higher.
* Recommended to use a virtual environment.

### Setup Instructions

1. **Clone the repository (or extract the folder):**
   ```bash
   git clone https://github.com/DT-1997/XJCO3011-CWK2.git
   cd XJCO3011-CWK2
2. **Create and activate a virtual environment (Optional but recommended):**

* Windows:
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```
* Mac/Linux:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
* Install the dependencies:
  
    The project requires `requests` for crawling, `beautifulsoup4` for HTML parsing, and `pytest` with `pytest-cov` for testing.

    ```bash
    pip install -r requirements.txt
    ```
## 🚀 Usage Guide
Start the interactive Search Engine Shell by running the following command from the project root:
    python -m src.main

Once the shell `>` prompt appears, you can use the following 4 core commands:

1. **`build`**
    
    Initiates the web crawler, builds the inverted index from scratch, and saves it to disk (`data/index.json`).

    * Note: Due to the 6-second politeness delay, crawling the 10 pages will take approximately 2 minute.

    ```
    > build
    [Build] Starting web crawler on [https://quotes.toscrape.com/](https://quotes.toscrape.com/)...
    [Build] Crawling finished. Retrieved 10 pages.
    [Build] Success! Index built and saved.
2. **`load`**

    Instantly loads the pre-built index from the disk into memory. (Useful if you restart the program and want to skip the `build` phase).

    ```
    > load
    [Load] Loading index from .../data/index.json...
    [Load] Success! Loaded index with 3000 unique words.
3. **`print <word>`**

   Displays the detailed inverted index statistics (Frequency and Positions) for a specific word across all crawled URLs.

    ```
    > print indifference
    [Print] Searching for word: 'indifference'...
    --- Index Data for 'indifference' ---
      URL: [https://quotes.toscrape.com/page/3/](https://quotes.toscrape.com/page/3/)
        Frequency: 1
        Positions: [45]

4. **`find <query>`**

   Finds pages matching the query phrase. Supports single words, multiple words, and automatically ranks them using TF-IDF. It also provides spell-check suggestions for typos.

    ```
    > find good friends
    [Find] Searching for: 'good friends'...
    --- Found 2 matching page(s) ---
    1. [https://quotes.toscrape.com/page/5/](https://quotes.toscrape.com/page/5/) (TF-IDF Score: 1.2541)
    2. [https://quotes.toscrape.com/page/2/](https://quotes.toscrape.com/page/2/) (TF-IDF Score: 0.8412)
    
    > find goood frends
    No exact matches found for your query.
     -> Did you mean: 'good friends'?
   ```
    
    Type `exit` or press `Ctrl+C` to cleanly terminate the program.

## 🧪 Testing Instructions
The project is driven by Test-Driven Development (TDD) and includes a comprehensive automated test suite. The tests isolate components using advanced `unittest.mock` techniques, meaning **no actual network requests or disk writes are performed during testing.**

To run the entire test suite and view the code coverage report, execute:
    
```bash
python -m pytest tests/ -v --cov=src --cov-report=term-missing
```
    

**Test Coverage Highlights:**

* `test_crawler.py`: Validates HTML extraction and HTTP error handling.
* `test_indexer.py`: Validates tokenization, dictionary construction, and I/O mocking.
* `test_search.py`: Validates set-intersection logic, TF-IDF scoring math, and string matching suggestions.
* `test_main.py`: Validates CLI command routing, edge-case user inputs (empty spaces, invalid commands), and state management.
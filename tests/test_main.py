import pytest
from unittest.mock import patch, MagicMock
from src.main import SearchEngineCLI


class TestSearchEngineCLI:
    """Test suite for the Command-Line Interface, focusing on command routing and state management."""

    @pytest.fixture
    def cli(self):
        """Fixture to initialize a clean CLI instance."""
        return SearchEngineCLI()

    # --- 1. State Management Tests ---

    def test_initial_state(self, cli):
        """Tests that the CLI starts with correct default states."""
        assert cli.is_loaded is False
        assert cli.searcher is None

    # --- 2. Command Execution Tests (Mocking internal components) ---

    @patch('src.main.Crawler')
    def test_do_build_success(self, MockCrawler, cli):
        """Tests the 'build' command flow: crawls, builds index, and sets loaded state."""
        # Mock the crawler to return dummy data instantly
        mock_crawler_instance = MockCrawler.return_value
        mock_crawler_instance.run.return_value = [{'url': 'test.com', 'content': 'dummy'}]

        # Mock the indexer to prevent actual file writing
        cli.indexer = MagicMock()
        cli.indexer.save.return_value = True

        cli.do_build()

        # Assertions to verify the flow
        mock_crawler_instance.run.assert_called_once()
        cli.indexer.build_index.assert_called_once()
        cli.indexer.save.assert_called_once()
        assert cli.is_loaded is True
        assert cli.searcher is not None

    def test_do_load_success(self, cli):
        """Tests the 'load' command successfully updating the CLI state."""
        cli.indexer = MagicMock()
        cli.indexer.load.return_value = True

        cli.do_load()

        cli.indexer.load.assert_called_once()
        assert cli.is_loaded is True
        assert cli.searcher is not None

    # --- 3. Error Handling and Guardrails Tests ---

    @patch('builtins.print')
    def test_find_without_load(self, mock_print, cli):
        """Tests that 'find' is blocked if the index is not loaded."""
        cli.is_loaded = False
        cli.do_find("test")

        # Assert that an error message was printed
        mock_print.assert_called_with("\n[Error] You must 'load' or 'build' the index before finding.")

    @patch('builtins.print')
    def test_print_without_word(self, mock_print, cli):
        """Tests that 'print' command handles empty arguments gracefully."""
        cli.is_loaded = True
        cli.do_print("")

        mock_print.assert_called_with("\n[Error] Please specify a word to print. Usage: print <word>")

    # --- 4. Interactive Loop Tests (Mocking user input) ---

    @patch('builtins.input', side_effect=['load', 'exit'])
    @patch('sys.exit', side_effect=SystemExit)
    def test_run_loop_routing(self, mock_exit, mock_input, cli):
        """
        Tests the REPL loop. Mocks user typing 'load' and then 'exit'.
        """
        # Mock do_load so it doesn't actually do anything
        cli.do_load = MagicMock()

        # Run the CLI loop
        try:
            cli.run()
        except SystemExit:
            pass

        # Verify the commands were routed correctly based on the mock inputs
        cli.do_load.assert_called_once()
        mock_exit.assert_called_once_with(0)

    # --- 5. Edge Cases in CLI Loop ---

    @patch('builtins.print')
    @patch('builtins.input', side_effect=['fly', 'exit'])
    @patch('sys.exit', side_effect=SystemExit)
    def test_unknown_command(self, mock_exit, mock_input, mock_print, cli):
        """Tests handling of an unknown command input."""
        try:
            cli.run()
        except SystemExit:
            pass

        # Assert that an error message is printed without crashing
        mock_print.assert_any_call("Unknown command: 'fly'. Valid commands: build, load, print, find, exit")
        # Assert that the program exits normally upon receiving the 'exit' command
        mock_exit.assert_called_once_with(0)

    @patch('builtins.input', side_effect=['   ', 'exit'])
    @patch('sys.exit', side_effect=SystemExit)
    def test_empty_command(self, mock_exit, mock_input, cli):
        """Tests handling of empty or whitespace-only inputs."""
        try:
            cli.run()
        except SystemExit:
            pass

        # Ensure the program continues the loop without raising an IndexError
        # and successfully reaches the mock exit command
        mock_exit.assert_called_once_with(0)

    @patch('builtins.print')
    @patch('builtins.input', side_effect=KeyboardInterrupt)
    @patch('sys.exit', side_effect=SystemExit)
    def test_keyboard_interrupt(self, mock_exit, mock_input, mock_print, cli):
        """Tests graceful exit upon a KeyboardInterrupt (Ctrl+C)."""
        try:
            cli.run()
        except SystemExit:
            pass

        # Assert the interrupt is caught, a farewell message is printed, and the program exits cleanly
        mock_print.assert_any_call("\nExiting search engine. Goodbye!")
        mock_exit.assert_called_once_with(0)

    @patch('builtins.input', side_effect=['bUiLd', 'LOAD', 'pRiNt test', 'fInD query', 'eXiT'])
    @patch('sys.exit', side_effect=SystemExit)
    def test_command_case_insensitivity(self, mock_exit, mock_input, cli):
        """Tests that commands are processed correctly regardless of their case."""
        # Mock internal methods to isolate routing logic and avoid actual execution
        cli.do_build = MagicMock()
        cli.do_load = MagicMock()
        cli.do_print = MagicMock()
        cli.do_find = MagicMock()

        try:
            cli.run()
        except SystemExit:
            pass

        # Verify that mixed-case inputs successfully route to the correct methods
        cli.do_build.assert_called_once()
        cli.do_load.assert_called_once()
        # Verify that the command argument (e.g., 'test', 'query') is passed as-is
        cli.do_print.assert_called_once_with('test')
        cli.do_find.assert_called_once_with('query')

        # Verify successful exit
        mock_exit.assert_called_once_with(0)

    # --- 6. Tests for Advanced Features (TF-IDF & Spell Check) ---

    @patch('builtins.print')
    def test_do_print_with_suggestion(self, mock_print, cli):
        """Tests that the print command suggests a correction when a word is not found."""
        cli.is_loaded = True
        cli.searcher = MagicMock()

        # Simulate a scenario where the word is not in the index
        cli.searcher.print_word.return_value = None
        # Provide a mock suggestion dictionary
        cli.searcher.get_query_suggestions.return_value = {"frends": "friends"}

        cli.do_print("frends")

        # Verify internal method calls
        cli.searcher.print_word.assert_called_once_with("frends")
        cli.searcher.get_query_suggestions.assert_called_once_with(["frends"])

        # Verify the exact output format
        mock_print.assert_any_call("Word 'frends' not found in the index.")
        mock_print.assert_any_call(" -> Did you mean: 'friends'?")

    @patch('builtins.print')
    def test_do_find_with_tfidf_formatting(self, mock_print, cli):
        """Tests that the find command correctly formats and prints TF-IDF scores."""
        cli.is_loaded = True
        cli.searcher = MagicMock()

        # Simulate a successful search returning a tuple of (URL, Score)
        cli.searcher.find_query.return_value = [("https://quotes.toscrape.com/page/1/", 1.23456)]

        cli.do_find("good")

        # Verify that the float score is correctly formatted to 4 decimal places
        mock_print.assert_any_call("1. https://quotes.toscrape.com/page/1/ (TF-IDF Score: 1.2346)")

    @patch('builtins.print')
    def test_do_find_with_multiple_suggestions(self, mock_print, cli):
        """Tests that the find command reconstructs and suggests a corrected multi-word query."""
        cli.is_loaded = True
        cli.searcher = MagicMock()

        # Simulate a scenario where no exact matches are found
        cli.searcher.find_query.return_value = []
        # Provide mock suggestions for multiple misspelled tokens
        cli.searcher.get_query_suggestions.return_value = {"goood": "good", "frends": "friends"}

        cli.do_find("goood frends")

        # Verify that suggestions were requested for the parsed tokens
        cli.searcher.get_query_suggestions.assert_called_once_with(["goood", "frends"])

        # Verify that the final suggested string is correctly assembled
        mock_print.assert_any_call(" -> Did you mean: 'good friends'?")
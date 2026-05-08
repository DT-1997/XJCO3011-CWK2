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
    @patch('sys.exit')
    def test_run_loop_routing(self, mock_exit, mock_input, cli):
        """
        Tests the REPL loop. Mocks user typing 'load' and then 'exit'.
        """
        # Mock do_load so it doesn't actually do anything
        cli.do_load = MagicMock()

        # Run the CLI loop
        cli.run()

        # Verify the commands were routed correctly based on the mock inputs
        cli.do_load.assert_called_once()
        mock_exit.assert_called_once_with(0)

    # --- 5. Edge Cases in CLI Loop ---

    @patch('builtins.print')
    @patch('builtins.input', side_effect=['fly', 'exit'])
    @patch('sys.exit')
    def test_unknown_command(self, mock_exit, mock_input, mock_print, cli):
        """Tests handling of an unknown command input."""
        cli.run()

        # Assert that an error message is printed without crashing
        mock_print.assert_any_call("Unknown command: 'fly'. Valid commands: build, load, print, find, exit")
        # Assert that the program exits normally upon receiving the 'exit' command
        mock_exit.assert_called_once_with(0)

    @patch('builtins.input', side_effect=['   ', 'exit'])
    @patch('sys.exit')
    def test_empty_command(self, mock_exit, mock_input, cli):
        """Tests handling of empty or whitespace-only inputs."""
        cli.run()

        # Ensure the program continues the loop without raising an IndexError
        # and successfully reaches the mock exit command
        mock_exit.assert_called_once_with(0)

    @patch('builtins.print')
    @patch('builtins.input', side_effect=KeyboardInterrupt)
    @patch('sys.exit')
    def test_keyboard_interrupt(self, mock_exit, mock_input, mock_print, cli):
        """Tests graceful exit upon a KeyboardInterrupt (Ctrl+C)."""
        cli.run()

        # Assert the interrupt is caught, a farewell message is printed, and the program exits cleanly
        mock_print.assert_any_call("\nExiting search engine. Goodbye!")
        mock_exit.assert_called_once_with(0)

    @patch('builtins.input', side_effect=['bUiLd', 'LOAD', 'pRiNt test', 'fInD query', 'eXiT'])
    @patch('sys.exit')
    def test_command_case_insensitivity(self, mock_exit, mock_input, cli):
        """Tests that commands are processed correctly regardless of their case."""
        # Mock internal methods to isolate routing logic and avoid actual execution
        cli.do_build = MagicMock()
        cli.do_load = MagicMock()
        cli.do_print = MagicMock()
        cli.do_find = MagicMock()

        cli.run()

        # Verify that mixed-case inputs successfully route to the correct methods
        cli.do_build.assert_called_once()
        cli.do_load.assert_called_once()
        # Verify that the command argument (e.g., 'test', 'query') is passed as-is
        cli.do_print.assert_called_once_with('test')
        cli.do_find.assert_called_once_with('query')

        # Verify successful exit
        mock_exit.assert_called_once_with(0)
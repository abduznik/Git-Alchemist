import json
import subprocess
from unittest.mock import patch, MagicMock

from src.utils import run_shell, parse_json_response, check_gh_auth, get_user_email


class TestRunShell:
    def test_returns_stdout(self):
        result = run_shell("echo hello")
        assert result == "hello"

    def test_returns_stripped_output(self):
        result = run_shell("echo '  spaced  '")
        assert "spaced" in result

    def test_returns_none_on_failure(self):
        result = run_shell("false")
        assert result is not None  # "false" exits 1 but still returns stdout (empty)

    def test_suppress_errors(self, capsys):
        run_shell("echo err >&2", suppress_errors=True)
        captured = capsys.readouterr()
        assert "Shell Error" not in captured.err

    def test_use_shell_flag(self):
        result = run_shell("echo foo | cat", use_shell=True)
        assert result == "foo"

    def test_invalid_command_returns_none(self):
        result = run_shell("nonexistent_command_xyz_123")
        assert result is None


class TestParseJsonResponse:
    def test_clean_json(self):
        assert parse_json_response('{"key": "value"}') == {"key": "value"}

    def test_markdown_json_block(self):
        text = '```json\n{"key": "value"}\n```'
        assert parse_json_response(text) == {"key": "value"}

    def test_bare_code_block(self):
        text = '```\n{"key": "value"}\n```'
        assert parse_json_response(text) == {"key": "value"}

    def test_surrounding_text(self):
        text = 'Here is the result:\n```json\n{"a": 1}\n```\nDone.'
        assert parse_json_response(text) == {"a": 1}

    def test_invalid_json_returns_none(self):
        assert parse_json_response("not json") is None

    def test_none_input(self):
        assert parse_json_response(None) is None

    def test_empty_string(self):
        assert parse_json_response("") is None

    def test_json_array(self):
        assert parse_json_response("[1, 2, 3]") == [1, 2, 3]

    def test_nested_json(self):
        data = {"a": {"b": [1, 2]}}
        assert parse_json_response(json.dumps(data)) == data


class TestCheckGhAuth:
    @patch("src.utils.run_shell")
    def test_authenticated(self, mock_run):
        mock_run.return_value = "testuser"
        assert check_gh_auth() == "testuser"

    @patch("src.utils.run_shell")
    def test_not_authenticated(self, mock_run):
        mock_run.return_value = None
        assert check_gh_auth() is None


class TestGetUserEmail:
    @patch("src.utils.run_shell")
    def test_returns_email(self, mock_run):
        mock_run.return_value = "user@example.com"
        assert get_user_email() == "user@example.com"

    @patch("src.utils.run_shell")
    def test_returns_none_when_empty(self, mock_run):
        mock_run.return_value = ""
        assert get_user_email() is None

    @patch("src.utils.run_shell")
    def test_returns_none_on_failure(self, mock_run):
        mock_run.return_value = None
        assert get_user_email() is None

import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from src.env import validate_environment, validate_gh_auth, ensure_ready

def test_validate_environment_success():
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
        assert validate_environment() == "test_key"

def test_validate_environment_failure():
    with patch.dict(os.environ, {}, clear=True):
        with patch("sys.exit") as mock_exit:
            validate_environment()
            mock_exit.assert_called_once_with(1)

def test_validate_gh_auth_success():
    with patch("src.env.run_shell", return_value="test_user"):
        assert validate_gh_auth() == "test_user"

def test_validate_gh_auth_failure_no_user():
    with patch("src.env.run_shell", return_value=None):
        with patch("sys.exit") as mock_exit:
            validate_gh_auth()
            mock_exit.assert_called_once_with(1)

def test_validate_gh_auth_failure_exception():
    with patch("src.env.run_shell", side_effect=Exception("error")):
        with patch("sys.exit") as mock_exit:
            validate_gh_auth()
            mock_exit.assert_called_once_with(1)

def test_ensure_ready():
    with patch("src.env.validate_environment", return_value="test_key"):
        with patch("src.env.validate_gh_auth", return_value="test_user"):
            info = ensure_ready(require_gh=True)
            assert info["gemini_api_key"] == "test_key"
            assert info["gh_user"] == "test_user"

            info_no_gh = ensure_ready(require_gh=False)
            assert info_no_gh["gemini_api_key"] == "test_key"
            assert "gh_user" not in info_no_gh

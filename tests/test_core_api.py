import pytest
import requests
from unittest.mock import patch, MagicMock
from src.core import generate_with_fallback, GenerationConfig, validate_prompt

def test_validate_prompt():
    with pytest.raises(ValueError, match="Prompt cannot be empty"):
        validate_prompt("")
    with pytest.raises(ValueError, match="Prompt cannot be empty"):
        validate_prompt("   ")
    validate_prompt("Valid prompt")

@patch("src.core.requests.post")
def test_generate_with_fallback_success(mock_post):
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "AI response"}]}}]
    }
    mock_post.return_value = mock_response

    api_key = "test_key"
    prompt = "Hello AI"
    models = ["model-1"]
    
    result = generate_with_fallback(api_key, prompt, models)
    
    assert result == "AI response"
    # Verify headers
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs["headers"]["x-goog-api-key"] == api_key
    assert "key=" not in args[0] # Key should NOT be in URL

@patch("src.core.requests.post")
def test_generate_with_fallback_retry_on_429(mock_post):
    # First call failed with 429, second succeeds
    mock_429 = MagicMock()
    mock_429.status_code = 429
    mock_429.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_429)
    
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Success after retry"}]}}]
    }
    
    mock_post.side_effect = [mock_429, mock_200]

    api_key = "test_key"
    prompt = "Retry test"
    models = ["model-1", "model-2"]
    
    result = generate_with_fallback(api_key, prompt, models)
    
    assert result == "Success after retry"
    assert mock_post.call_count == 2

@patch("src.core.requests.post")
def test_generate_with_fallback_timeout(mock_post):
    mock_post.side_effect = requests.exceptions.Timeout()
    
    api_key = "test_key"
    prompt = "Timeout test"
    models = ["model-1"]
    
    result = generate_with_fallback(api_key, prompt, models, silent=True)
    
    assert result is None
    assert mock_post.call_count == 1

@patch("src.core.requests.post")
def test_generate_with_fallback_exhausted(mock_post):
    mock_500 = MagicMock()
    mock_500.status_code = 500
    mock_500.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_500)
    mock_post.return_value = mock_500
    
    api_key = "test_key"
    prompt = "Exhaust test"
    models = ["model-1", "model-2"]
    
    result = generate_with_fallback(api_key, prompt, models, silent=True)
    
    assert result is None
    assert mock_post.call_count == 2

def test_generation_config():
    config = GenerationConfig(timeout=30)
    assert config.timeout == 30
    assert config.api_version == "v1beta"

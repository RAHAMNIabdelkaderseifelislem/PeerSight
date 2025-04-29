import pytest
import requests
import sys
from pathlib import Path
import json

# Add src directory to sys.path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from peersight import llm_client
from peersight import config # To check default URL/model if needed

# Test constants
TEST_PROMPT = "What is the airspeed velocity of an unladen swallow?"
EXPECTED_RESPONSE = "African or European swallow?"
TEST_MODEL = "test-model"
TEST_API_URL = "http://fake-ollama:11434/api/generate"

# --- Tests for query_ollama ---

# Use pytest-mock's 'mocker' fixture
def test_query_ollama_success(mocker):
    """Test successful query to Ollama."""
    # Configure the mock response
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    # Ollama returns JSON, so mock the .json() method
    mock_response.json.return_value = {"response": EXPECTED_RESPONSE, "done": True}
    # Mock raise_for_status to do nothing on success
    mock_response.raise_for_status.return_value = None

    # Patch requests.post to return our mock response
    mock_post = mocker.patch("requests.post", return_value=mock_response)

    # Call the function under test
    result = llm_client.query_ollama(TEST_PROMPT, model=TEST_MODEL, api_url=TEST_API_URL)

    # Assertions
    assert result == EXPECTED_RESPONSE
    # Check if requests.post was called correctly
    mock_post.assert_called_once()
    # Inspect the call arguments (optional but good)
    call_args, call_kwargs = mock_post.call_args
    assert call_args[0] == TEST_API_URL
    assert "headers" in call_kwargs
    assert "json" not in call_kwargs # We are sending raw data=json.dumps(...)
    assert "data" in call_kwargs
    payload = json.loads(call_kwargs["data"])
    assert payload["model"] == TEST_MODEL
    assert payload["prompt"] == TEST_PROMPT
    assert payload["stream"] is False

def test_query_ollama_connection_error(mocker):
    """Test handling of requests.exceptions.ConnectionError."""
    # Patch requests.post to raise ConnectionError
    mock_post = mocker.patch("requests.post", side_effect=requests.exceptions.ConnectionError("Failed to connect"))

    result = llm_client.query_ollama(TEST_PROMPT, api_url=TEST_API_URL)

    assert result is None
    mock_post.assert_called_once_with(
        TEST_API_URL,
        headers=mocker.ANY, # Or specify exact headers if needed
        data=mocker.ANY,    # Or specify exact data if needed
        timeout=mocker.ANY  # Or specify exact timeout
    )

def test_query_ollama_timeout_error(mocker):
    """Test handling of requests.exceptions.Timeout."""
    mock_post = mocker.patch("requests.post", side_effect=requests.exceptions.Timeout("Request timed out"))

    result = llm_client.query_ollama(TEST_PROMPT, api_url=TEST_API_URL)

    assert result is None
    mock_post.assert_called_once()

def test_query_ollama_http_error(mocker):
    """Test handling of HTTP errors (e.g., 404 Not Found)."""
    mock_response = mocker.Mock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
    # Mock response text for logging
    mock_response.text = "Model not found"

    mock_post = mocker.patch("requests.post", return_value=mock_response)

    result = llm_client.query_ollama(TEST_PROMPT, api_url=TEST_API_URL)

    assert result is None
    mock_post.assert_called_once()
    mock_response.raise_for_status.assert_called_once() # Ensure raise_for_status was hit

def test_query_ollama_missing_response_key(mocker):
    """Test handling when the response JSON lacks the 'response' key."""
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    # Missing 'response' key
    mock_response.json.return_value = {"done": True, "model": TEST_MODEL}
    mock_response.raise_for_status.return_value = None

    mock_post = mocker.patch("requests.post", return_value=mock_response)

    result = llm_client.query_ollama(TEST_PROMPT, api_url=TEST_API_URL)

    assert result is None
    mock_post.assert_called_once()

def test_query_ollama_json_decode_error(mocker):
    """Test handling of invalid JSON response."""
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    # Simulate invalid JSON by making .json() raise an error
    mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "invalid json text", 0)
    # Provide text attribute for logging
    mock_response.text = "invalid json text"


    mock_post = mocker.patch("requests.post", return_value=mock_response)

    result = llm_client.query_ollama(TEST_PROMPT, api_url=TEST_API_URL)

    assert result is None
    mock_post.assert_called_once()
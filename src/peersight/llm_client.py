import requests
import json
import logging # Use logging for better error reporting

from . import config # Import configuration

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def query_ollama(prompt: str, model: str = None, api_url: str = None) -> str | None:
    """
    Sends a prompt to the configured Ollama API endpoint and returns the response.

    Args:
        prompt: The input prompt for the LLM.
        model: The Ollama model to use (overrides config if provided).
        api_url: The Ollama API URL to use (overrides config if provided).

    Returns:
        The LLM's response content as a string, or None if an error occurs.
    """
    resolved_model = model if model else config.OLLAMA_MODEL
    resolved_api_url = api_url if api_url else config.OLLAMA_API_URL

    logging.info(f"Querying Ollama model '{resolved_model}' at {resolved_api_url}...")

    payload = {
        "model": resolved_model,
        "prompt": prompt,
        "stream": False  # We want the full response at once
        # Optional: Add other parameters like temperature, top_p etc. here
        # "options": {
        #     "temperature": 0.7
        # }
    }

    try:
        response = requests.post(
            resolved_api_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=120 # Add a timeout (e.g., 120 seconds)
        )
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        response_data = response.json()

        # Check if the expected 'response' key exists
        if "response" in response_data:
            logging.info("Received successful response from Ollama.")
            # --- Key Objective: Strip Internal Logic ---
            # The goal is to simulate the *output* of reasoning.
            # Here, we directly return the final 'response' field.
            # No intermediate thoughts, confidence scores, etc., are exposed from this client.
            return response_data["response"].strip()
        else:
            logging.error(f"Ollama response missing 'response' key. Full response: {response_data}")
            return None

    except requests.exceptions.ConnectionError as e:
        logging.error(f"Connection Error: Could not connect to Ollama API at {resolved_api_url}. Ensure Ollama is running. Details: {e}")
        return None
    except requests.exceptions.Timeout as e:
        logging.error(f"Timeout Error: Request to Ollama timed out. Details: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Request Error: An error occurred during the request to Ollama. Status Code: {e.response.status_code if e.response else 'N/A'}. Details: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"JSON Decode Error: Failed to parse response from Ollama. Response text: {response.text}. Details: {e}")
        return None
    except Exception as e: # Catch any other unexpected errors
         logging.error(f"An unexpected error occurred: {e}", exc_info=True) # Log traceback
         return None
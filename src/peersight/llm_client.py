import requests
import json
import logging
from typing import Optional, Dict, Any

from . import config

logger = logging.getLogger(__name__)

# Modify function signature and payload logic
def query_ollama(
    prompt: str,
    model: Optional[str] = None,
    api_url: Optional[str] = None,
    temperature: Optional[float] = None,
    top_k: Optional[int] = None, # Add top_k
    top_p: Optional[float] = None, # Add top_p
) -> Optional[str]:
    """
    Sends a prompt to the configured Ollama API endpoint. Includes options.

    Args:
        prompt: The input prompt for the LLM.
        model: Ollama model override.
        api_url: Ollama API URL override.
        temperature: Temperature override.
        top_k: Top-K sampling override.
        top_p: Top-P (nucleus) sampling override.

    Returns:
        The LLM's response content string, or None on error.
    """
    resolved_model = model if model is not None else config.OLLAMA_MODEL
    resolved_api_url = api_url if api_url is not None else config.OLLAMA_API_URL
    # Resolve parameters: CLI/Arg > Config > Default (-1 means unset)
    resolved_temperature = temperature if temperature is not None else config.OLLAMA_TEMPERATURE
    resolved_top_k = top_k if top_k is not None else config.OLLAMA_TOP_K
    resolved_top_p = top_p if top_p is not None else config.OLLAMA_TOP_P


    logger.info(f"Querying Ollama model '{resolved_model}' at {resolved_api_url}...")
    # Log effective parameters being sent (or default if not sent)
    options_log = {}
    if resolved_temperature is not None and 0.0 <= resolved_temperature <= 2.0:
        options_log["temperature"] = resolved_temperature
    if resolved_top_k is not None and resolved_top_k > 0:
        options_log["top_k"] = resolved_top_k
    if resolved_top_p is not None and 0.0 < resolved_top_p <= 1.0:
        options_log["top_p"] = resolved_top_p
    logger.debug(f"Using LLM options: {options_log if options_log else 'Ollama Defaults'}")


    # --- Build Payload with Options ---
    payload: Dict[str, Any] = {
        "model": resolved_model,
        "prompt": prompt,
        "stream": False,
        "options": {}, # Initialize options dictionary
    }

    # Add valid options to the payload's options dict
    if "temperature" in options_log:
        payload["options"]["temperature"] = options_log["temperature"]
    if "top_k" in options_log:
         payload["options"]["top_k"] = options_log["top_k"]
    if "top_p" in options_log:
         payload["options"]["top_p"] = options_log["top_p"]

    # Remove options key entirely if empty, Ollama might prefer this
    if not payload["options"]:
         del payload["options"]


    # --- Make API Request ---
    try:
        response = requests.post(
            resolved_api_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=120,
        )
        # ... (error handling and response processing) ...
        response.raise_for_status()
        response_data = response.json()
        if "response" in response_data:
            logger.info("Received successful response from Ollama.")
            return response_data["response"].strip()
        else: #...
             logger.error(f"Ollama response missing 'response' key. Full response: {response_data}")
             return None

    # ... (exception handling) ...
    except requests.exceptions.ConnectionError as e: 
        logger.error(f"Connection Error: Could not connect to Ollama API at {resolved_api_url}. Details: {e}")
        return None
    except requests.exceptions.Timeout as e: 
        logger.error(f"Timeout Error: Request to Ollama timed out. Details: {e}")
        return None
    except requests.exceptions.RequestException as e: 
        logger.error(f"Request Error: Status Code: {e.response.status_code if e.response else 'N/A'}. Details: {e}")
        return None
    except json.JSONDecodeError as e: 
        logger.error(f"JSON Decode Error: Failed to parse response. Response text: {response.text}. Details: {e}")
        return None
    except Exception as e: 
        logger.error(f"An unexpected error occurred in LLM client: {e}", exc_info=True)
        return None
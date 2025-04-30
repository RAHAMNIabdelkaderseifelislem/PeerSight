import json
import logging
from typing import Any, Dict, Optional  # Add Dict, Any

import requests

from . import config

logger = logging.getLogger(__name__)  # Use module-specific logger


# Modify function signature and payload
def query_ollama(
    prompt: str,
    model: Optional[str] = None,
    api_url: Optional[str] = None,
    temperature: Optional[float] = None,
) -> Optional[str]:
    """
    Sends a prompt to the configured Ollama API endpoint and returns the response.

    Args:
        prompt: The input prompt for the LLM.
        model: The Ollama model to use (overrides config).
        api_url: The Ollama API URL to use (overrides config).
        temperature: The temperature setting for the LLM (overrides config).

    Returns:
        The LLM's response content as a string, or None if an error occurs.
    """
    resolved_model = model if model is not None else config.OLLAMA_MODEL
    resolved_api_url = api_url if api_url is not None else config.OLLAMA_API_URL
    # Prioritize CLI/arg temp > config temp
    resolved_temperature = (
        temperature if temperature is not None else config.OLLAMA_TEMPERATURE
    )

    logger.info(f"Querying Ollama model '{resolved_model}' at {resolved_api_url}...")
    logger.debug(f"Using temperature: {resolved_temperature}")  # Log the effective temp

    # --- Build Payload with Options ---
    payload: Dict[str, Any] = {
        "model": resolved_model,
        "prompt": prompt,
        "stream": False,
        "options": {},  # Initialize options dictionary
    }
    # Add temperature to options if it's valid
    if resolved_temperature is not None:
        # Basic validation (Ollama typically expects 0 to 1 or higher)
        if 0.0 <= resolved_temperature <= 2.0:  # Reasonable range check
            payload["options"]["temperature"] = resolved_temperature
        else:
            logger.warning(
                f"Provided temperature ({resolved_temperature}) is outside typical range (0.0-2.0). Using default."
            )
            # Optionally fall back to config default if override is invalid?
            # payload["options"]["temperature"] = config.OLLAMA_TEMPERATURE
            # Or just don't send it if invalid? Let's not send it.
            pass  # Don't add invalid temp to payload

    # --- Make API Request ---
    try:
        response = requests.post(
            resolved_api_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),  # Send the full payload including options
            timeout=120,
        )
        # ... (rest of error handling and response processing remains the same) ...
        response.raise_for_status()
        response_data = response.json()
        if "response" in response_data:
            logger.info("Received successful response from Ollama.")
            return response_data["response"].strip()
        else:
            logger.error(
                f"Ollama response missing 'response' key. Full response: {response_data}"
            )
            return None

    except requests.exceptions.ConnectionError as e:
        logger.error(
            f"Connection Error: Could not connect to Ollama API at {resolved_api_url}. Details: {e}"
        )
        return None
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout Error: Request to Ollama timed out. Details: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(
            f"Request Error: Status Code: {e.response.status_code if e.response else 'N/A'}. Details: {e}"
        )
        return None
    except json.JSONDecodeError as e:
        logger.error(
            f"JSON Decode Error: Failed to parse response. Response text: {response.text}. Details: {e}"
        )
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred in LLM client: {e}", exc_info=True)
        return None

import logging
import sys
import json
from typing import Tuple, Union, Dict, Optional  # For type hints

from . import utils
from . import prompts
from . import llm_client
from . import parser
from . import config

logger = logging.getLogger(__name__)


# Modify return type hint
# Add temperature parameter
def generate_review(
    paper_path: str,
    model_override: Optional[str] = None,
    api_url_override: Optional[str] = None,
    temperature_override: Optional[float] = None,  # Add temp override
) -> Tuple[bool, Optional[Union[Dict, str]]]:
    """
    Orchestrates the academic paper review generation process.
    Accepts optional overrides for model, API URL, and temperature.
    """
    logger.info(f"Starting review generation for: {paper_path}")
    # ... (log model/URL overrides) ...
    if model_override:
        logger.debug(f"Using CLI model override: {model_override}")
    if api_url_override:
        logger.debug(f"Using CLI API URL override: {api_url_override}")
    # Log temp override if present
    if temperature_override is not None:
        logger.debug(f"Using CLI temperature override: {temperature_override}")

    # 1. Read Paper Content
    paper_content = utils.read_text_file(paper_path)
    paper_length = 0
    if paper_content is not None:
        paper_length = len(paper_content)
    else:
        logger.error(
            f"Failed to read paper content from '{paper_path}'. Aborting review."
        )
        return False, None  # Return failure, no data

    logger.info(f"Successfully loaded paper content ({paper_length} characters).")
    if paper_length > config.MAX_PAPER_LENGTH_WARN_THRESHOLD:
        # ... (warning log) ...
        logger.warning(
            f"Input paper length ({paper_length} chars) exceeds threshold ({config.MAX_PAPER_LENGTH_WARN_THRESHOLD} chars). Processing may be slow or fail."
        )

    # 2. Generate Review Prompt
    review_prompt = prompts.format_review_prompt(paper_content)
    logger.info("Generated review prompt for LLM.")
    logger.debug(f"Prompt length: {len(review_prompt)} characters.")

    # 3. Query LLM for Review
    logger.info("Sending request to LLM for paper review...")
    raw_review_output = llm_client.query_ollama(
        prompt=review_prompt,
        model=model_override,
        api_url=api_url_override,
        temperature=temperature_override,  # Pass temperature override
    )

    # 4. Clean LLM Output
    cleaned_review_text = utils.clean_llm_output(raw_review_output)
    if not cleaned_review_text:
        logger.error("Review text is empty after cleaning process.")
        return False, None  # Return failure, no data
    logger.info("Cleaned LLM response successfully.")

    # 5. Parse Cleaned Text
    parsed_review = parser.parse_review_text(cleaned_review_text)

    if parsed_review is None:
        # Log clarified
        logger.error(
            "Failed to parse cleaned review text into structured data. Returning raw cleaned text instead."
        )
        # Return success=True (review generated/cleaned) but data is the raw text
        return True, cleaned_review_text
    else:
        logger.info("Successfully parsed review into structured data.")
        logger.debug(f"Parsed Review Data:\n{json.dumps(parsed_review, indent=2)}")
        # Return success=True and the parsed dictionary
        return True, parsed_review

    # Note: Output handling is now done in main.py

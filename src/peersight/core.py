# src/peersight/core.py
import logging
import sys
import json

from . import utils
from . import prompts
from . import llm_client
from . import parser
from . import config # Import config to access the threshold

logger = logging.getLogger(__name__)

def generate_review(paper_path: str,
                    output_path: str = None,
                    model_override: str = None,
                    api_url_override: str = None) -> bool:

    logger.info(f"Starting review generation for: {paper_path}")
    # ... (logging overrides) ...
    if model_override: logger.debug(f"Using CLI model override: {model_override}")
    if api_url_override: logger.debug(f"Using CLI API URL override: {api_url_override}")


    # 1. Read Paper Content
    paper_content = utils.read_text_file(paper_path)
    if paper_content is None:
         logger.error(f"Failed to read paper content from '{paper_path}'. Aborting review.")
         return False

    # --- Check Paper Length ---
    paper_length = len(paper_content)
    logger.info(f"Successfully loaded paper content ({paper_length} characters).")
    if paper_length > config.MAX_PAPER_LENGTH_WARN_THRESHOLD:
        logger.warning(
            f"Input paper length ({paper_length} chars) exceeds threshold "
            f"({config.MAX_PAPER_LENGTH_WARN_THRESHOLD} chars). "
            "Processing may be slow or fail due to LLM context limits."
        )
        # Consider adding a prompt to confirm continuation for very long papers in interactive mode later?

    # 2. Generate Review Prompt
    review_prompt = prompts.format_review_prompt(paper_content)
    # Limit logging of the full prompt, especially if long
    logger.info("Generated review prompt for LLM.")
    logger.debug(f"Prompt length: {len(review_prompt)} characters.") # Log prompt length too


    # 3. Query LLM for Review
    # ... (LLM query logic) ...
    logger.info("Sending request to LLM for paper review...")
    raw_review_output = llm_client.query_ollama(prompt=review_prompt, model=model_override, api_url=api_url_override)
    if not raw_review_output: # ... Error handling ...
         logger.error("Failed to get valid response from LLM. Aborting review.")
         return False
    logger.info("Received raw response from LLM.")


    # 4. Clean LLM Output
    # ... (Cleaning logic) ...
    cleaned_review_text = utils.clean_llm_output(raw_review_output)
    if not cleaned_review_text: # Check if empty after cleaning
         logger.error("Review text is empty after cleaning process.")
         print("Error: Failed to produce review content after cleaning.", file=sys.stderr)
         return False


    # 5. Parse Cleaned Text
    # ... (Parsing logic) ...
    parsed_review = parser.parse_review_text(cleaned_review_text)
    if parsed_review is None:
         logger.error("Failed to parse the cleaned review text. Outputting raw cleaned text as fallback.")
         # Outputting raw text is handled below
    else:
         logger.info("Successfully parsed review into structured data.")
         logger.debug(f"Parsed Review Data:\n{json.dumps(parsed_review, indent=2)}")


    # 6. Output Review
    # ... (Output logic using cleaned_review_text) ...
    output_successful = False
    review_to_output = cleaned_review_text # Still outputting the text version

    # ... (Rest of function) ...
    if output_path:
        logger.info(f"Attempting to save review text to file: {output_path}")
        success = utils.write_text_file(output_path, review_to_output)
        if success: print(f"Review successfully saved to: {output_path}"); output_successful = True
        else: logger.error(f"Failed to save review to file: {output_path}"); print(f"Error: Failed to save review to {output_path}. Check logs.", file=sys.stderr)
    else:
        print("\n--- Generated Peer Review ---")
        print(review_to_output)
        print("--- End of Review ---\n")
        output_successful = True

    if output_successful: logger.info(f"Review generation and output for '{paper_path}' completed successfully.")
    else: logger.error(f"Review generation completed but output failed for '{paper_path}'.")

    return output_successful
import logging
import sys
import json # Import json for potential future use/logging

from . import utils
from . import prompts
from . import llm_client
from . import parser # Import the new parser module

logger = logging.getLogger(__name__)

def generate_review(paper_path: str,
                    output_path: str = None,
                    model_override: str = None,
                    api_url_override: str = None) -> bool:
    # ... (beginning of function remains the same) ...
    logger.info(f"Starting review generation for: {paper_path}")
    if model_override: logger.debug(f"Using CLI model override: {model_override}")
    if api_url_override: logger.debug(f"Using CLI API URL override: {api_url_override}")

    # 1. Read Paper Content
    paper_content = utils.read_text_file(paper_path)
    if paper_content is None: # ... Error handling ...
         logger.error(f"Failed to read paper content from '{paper_path}'. Aborting review.")
         return False
    logger.info(f"Successfully loaded paper content ({len(paper_content)} characters).")

    # 2. Generate Review Prompt
    review_prompt = prompts.format_review_prompt(paper_content)
    logger.info("Generated review prompt for LLM.")

    # 3. Query LLM for Review
    logger.info("Sending request to LLM for paper review...")
    raw_review_output = llm_client.query_ollama(prompt=review_prompt, model=model_override, api_url=api_url_override)
    if not raw_review_output: # ... Error handling ...
         logger.error("Failed to get valid response from LLM. Aborting review.")
         return False
    logger.info("Received raw response from LLM.")

    # 4. Clean LLM Output
    cleaned_review_text = utils.clean_llm_output(raw_review_output)
    if not cleaned_review_text or not cleaned_review_text.startswith(prompts.REVIEW_SECTION_SUMMARY):
        # ... Error handling ...
        logger.warning(f"Cleaned review seems invalid or empty after processing.")
        print("Error: Failed to produce a valid structured review after cleaning.", file=sys.stderr)
        return False
    logger.info("Cleaned LLM response successfully.")

    # --- 5. Parse Cleaned Text into Structured Data ---
    parsed_review = parser.parse_review_text(cleaned_review_text)

    if parsed_review is None:
        logger.error("Failed to parse the cleaned review text into a structured format. Outputting raw text.")
        # Decide how to proceed: output raw text or fail? Let's output raw text as fallback.
    else:
        logger.info("Successfully parsed review into structured data.")
        # Log the parsed structure at DEBUG level for verification
        # Use json.dumps for pretty printing the dict in logs
        logger.debug(f"Parsed Review Data:\n{json.dumps(parsed_review, indent=2)}")


    # --- 6. Output Review (Save or Print) ---
    # For now, we still output the original cleaned_review_text.
    # The parsed_review dict is available for future enhancements (e.g., JSON output).
    output_successful = False
    review_to_output = cleaned_review_text # Output the raw cleaned text for now

    if output_path:
        logger.info(f"Attempting to save review text to file: {output_path}")
        success = utils.write_text_file(output_path, review_to_output)
        if success:
            print(f"Review successfully saved to: {output_path}")
            output_successful = True
        else: # ... Error handling ...
            logger.error(f"Failed to save review to file: {output_path}")
            print(f"Error: Failed to save review to {output_path}. Check logs.", file=sys.stderr)
    else:
        print("\n--- Generated Peer Review ---")
        print(review_to_output)
        print("--- End of Review ---\n")
        output_successful = True

    # ... (rest of function remains the same) ...
    if output_successful:
        logger.info(f"Review generation and output for '{paper_path}' completed successfully.")
    else:
         logger.error(f"Review generation completed but output failed for '{paper_path}'.")

    return output_successful
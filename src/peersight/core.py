import logging
import sys

from . import utils
from . import prompts
from . import llm_client
# Import config to log default if override not used (optional)
# from . import config

logger = logging.getLogger(__name__)

# Add parameters to accept overrides
def generate_review(paper_path: str,
                    output_path: str = None,
                    model_override: str = None,
                    api_url_override: str = None) -> bool:
    """
    Orchestrates the academic paper review generation process.
    Accepts optional overrides for model and API URL.
    """
    logger.info(f"Starting review generation for: {paper_path}")
    # Log which model/URL will be attempted (override or default via llm_client)
    # llm_client handles the logic of using override vs config default
    # We could log here too for clarity in core logs
    if model_override: logger.debug(f"Using CLI model override: {model_override}")
    if api_url_override: logger.debug(f"Using CLI API URL override: {api_url_override}")

    # 1. Read Paper Content
    paper_content = utils.read_text_file(paper_path)
    if paper_content is None:
        logger.error(f"Failed to read paper content from '{paper_path}'. Aborting review.")
        return False
    logger.info(f"Successfully loaded paper content ({len(paper_content)} characters).")

    # 2. Generate Review Prompt
    review_prompt = prompts.format_review_prompt(paper_content)
    logger.info("Generated review prompt for LLM.")

    # 3. Query LLM for Review
    logger.info("Sending request to LLM for paper review...")
    # Pass overrides to the client function
    raw_review_output = llm_client.query_ollama(
        prompt=review_prompt,
        model=model_override,       # Pass override value
        api_url=api_url_override    # Pass override value
    )

    if not raw_review_output:
        logger.error("Failed to get valid response from LLM. Aborting review.")
        return False

    logger.info("Received raw response from LLM.")

    # 4. Clean LLM Output
    # ... (cleaning logic remains the same) ...
    cleaned_review = utils.clean_llm_output(raw_review_output)
    if not cleaned_review or not cleaned_review.startswith(prompts.REVIEW_SECTION_SUMMARY):
         logger.warning(f"Cleaned review seems invalid or empty after processing. Check LLM output and cleaning logic.")
         print("Error: Failed to produce a valid structured review after cleaning.", file=sys.stderr)
         return False
    logger.info("Cleaned LLM response successfully.")

    # 5. Output Review (Save or Print)
    # ... (output logic remains the same) ...
    output_successful = False
    if output_path:
        logger.info(f"Attempting to save review to file: {output_path}")
        success = utils.write_text_file(output_path, cleaned_review)
        if success:
            print(f"Review successfully saved to: {output_path}")
            output_successful = True
        else:
            logger.error(f"Failed to save review to file: {output_path}")
            print(f"Error: Failed to save review to {output_path}. Check logs.", file=sys.stderr)
    else:
        print("\n--- Generated Peer Review ---")
        print(cleaned_review)
        print("--- End of Review ---\n")
        output_successful = True

    if output_successful:
        logger.info(f"Review generation and output for '{paper_path}' completed successfully.")
    else:
         logger.error(f"Review generation completed but output failed for '{paper_path}'.")

    return output_successful
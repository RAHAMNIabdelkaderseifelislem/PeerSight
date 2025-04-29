import logging
import sys

# Import necessary components from other modules within the package
from . import utils
from . import prompts
from . import llm_client
# No need to import config directly if llm_client and utils use it internally

# Configure logging for this module (or rely on root configuration)
# logger = logging.getLogger(__name__) # Alternative: specific logger per module

def generate_review(paper_path: str, output_path: str = None) -> bool:
    """
    Orchestrates the academic paper review generation process.

    Reads the paper, generates a prompt, queries the LLM, cleans the output,
    and saves or prints the result.

    Args:
        paper_path: Path to the input paper text file.
        output_path: Optional path to save the review output file.
                     If None, prints to console.

    Returns:
        True if the review was generated and output successfully, False otherwise.
    """
    logging.info(f"Starting review generation for: {paper_path}")

    # 1. Read Paper Content
    paper_content = utils.read_text_file(paper_path)
    if paper_content is None:
        logging.error(f"Failed to read paper content from '{paper_path}'. Aborting review.")
        return False # Indicate failure
    logging.info(f"Successfully loaded paper content ({len(paper_content)} characters).")

    # 2. Generate Review Prompt
    review_prompt = prompts.format_review_prompt(paper_content)
    logging.info("Generated review prompt for LLM.")

    # 3. Query LLM for Review
    logging.info("Sending request to LLM for paper review...")
    raw_review_output = llm_client.query_ollama(review_prompt)

    if not raw_review_output:
        logging.error("Failed to get valid response from LLM. Aborting review.")
        return False # Indicate failure

    logging.info("Received raw response from LLM.")

    # 4. Clean LLM Output
    cleaned_review = utils.clean_llm_output(raw_review_output)
    if not cleaned_review or not cleaned_review.startswith(prompts.REVIEW_SECTION_SUMMARY):
         logging.warning(f"Cleaned review seems invalid or empty after processing. Check LLM output and cleaning logic.")
         # Decide if this is a critical failure or if we should output the potentially broken review.
         # For now, let's treat it as a failure for generating a *valid* review.
         print("Error: Failed to produce a valid structured review after cleaning.", file=sys.stderr)
         return False # Indicate failure

    logging.info("Cleaned LLM response successfully.")

    # 5. Output Review (Save or Print)
    output_successful = False
    if output_path:
        logging.info(f"Attempting to save review to file: {output_path}")
        success = utils.write_text_file(output_path, cleaned_review)
        if success:
            print(f"Review successfully saved to: {output_path}") # User confirmation
            output_successful = True
        else:
            logging.error(f"Failed to save review to file: {output_path}")
            print(f"Error: Failed to save review to {output_path}. Check logs.", file=sys.stderr)
            # Still return False as the intended output action failed
    else:
        # Print to console if no output file specified
        print("\n--- Generated Peer Review ---") # Add newline for spacing
        print(cleaned_review)
        print("--- End of Review ---\n") # Add newline for spacing
        output_successful = True # Printing to console is considered success here

    if output_successful:
        logging.info(f"Review generation and output for '{paper_path}' completed successfully.")
    else:
         logging.error(f"Review generation completed but output failed for '{paper_path}'.")

    return output_successful
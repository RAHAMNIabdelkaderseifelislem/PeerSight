"""
PeerSight: AI Academic Paper Reviewer
"""
import argparse
import sys
import logging

from . import config
from . import llm_client
from . import utils # utils now contains the cleaner
from . import prompts

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# To see debug messages from the cleaner, change level to DEBUG:
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def setup_arg_parser():
    # ... (keep existing setup_arg_parser function) ...
    """Sets up the command-line argument parser."""
    parser = argparse.ArgumentParser(description="PeerSight: AI Academic Paper Reviewer")
    parser.add_argument("paper_path", help="Path to the academic paper plain text file.")
    return parser

def run():
    logging.info("--- PeerSight Process Starting ---")
    parser = setup_arg_parser()
    args = parser.parse_args()

    logging.info(f"Review request for paper: {args.paper_path}")
    logging.info(f"Using Ollama model: {config.OLLAMA_MODEL}")
    logging.info(f"Ollama API URL: {config.OLLAMA_API_URL}")
    print("-" * 30)

    # --- Read Paper Content ---
    paper_content = utils.read_text_file(args.paper_path)
    if paper_content is None:
        logging.error(f"Fatal: Could not read the paper file at '{args.paper_path}'. Exiting.")
        sys.exit(1)
    logging.info(f"Successfully loaded paper content ({len(paper_content)} characters).")
    print("-" * 30)

    # --- Generate Review Prompt ---
    review_prompt = prompts.format_review_prompt(paper_content)
    logging.info("Generated review prompt for LLM.")
    print("-" * 30)

    # --- Query LLM for Review ---
    logging.info("Sending request to LLM for paper review...")
    raw_review_output = llm_client.query_ollama(review_prompt)
    print("-" * 30)

    # --- Process and Display Review Output ---
    if raw_review_output:
        logging.info("Received raw response from LLM.")
        # !! Clean the output before displaying !!
        cleaned_review = utils.clean_llm_output(raw_review_output)
        logging.info("Cleaned LLM response.")

        print("--- Generated Peer Review ---")
        print(cleaned_review) # Print the cleaned version
        print("--- End of Review ---")
    else:
        logging.error("Failed to get review response from Ollama. Check previous logs.")
        print("Error: Failed to generate review. Please check Ollama connection and logs.")
        sys.exit(1)

    print("-" * 30)
    logging.info("--- PeerSight Process Finished ---")


if __name__ == "__main__":
    run()
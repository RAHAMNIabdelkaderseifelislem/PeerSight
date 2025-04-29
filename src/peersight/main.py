"""
PeerSight: AI Academic Paper Reviewer
"""
import argparse
import sys
import logging # Make sure logging is imported

from . import config
from . import llm_client
from . import utils
from . import prompts # Import the prompts module

# Setup basic logging (if not already configured elsewhere e.g. llm_client)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def setup_arg_parser():
    """Sets up the command-line argument parser."""
    parser = argparse.ArgumentParser(description="PeerSight: AI Academic Paper Reviewer")
    parser.add_argument("paper_path", help="Path to the academic paper plain text file.")
    # parser.add_argument("-o", "--output", help="Path to save the review output file.") # Keep for later
    return parser

def run():
    logging.info("--- PeerSight Process Starting ---")
    parser = setup_arg_parser()
    args = parser.parse_args()

    logging.info(f"Review request for paper: {args.paper_path}")
    logging.info(f"Using Ollama model: {config.OLLAMA_MODEL}")
    logging.info(f"Ollama API URL: {config.OLLAMA_API_URL}")
    print("-" * 30) # Keep some print separators for clarity

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
    # Optional: Print the prompt for debugging (can be very long)
    # print("--- PROMPT START ---")
    # print(review_prompt)
    # print("--- PROMPT END ---")
    # print("-" * 30)


    # --- Query LLM for Review ---
    logging.info("Sending request to LLM for paper review...")
    review_output = llm_client.query_ollama(review_prompt)

    print("-" * 30)
    # --- Display Review Output ---
    if review_output:
        logging.info("Received review from LLM.")
        print("--- Generated Peer Review ---")
        # The output should ideally conform to the requested structure
        print(review_output)
        print("--- End of Review ---")
    else:
        logging.error("Failed to get review response from Ollama. Check previous logs.")
        print("Error: Failed to generate review. Please check Ollama connection and logs.")
        sys.exit(1) # Exit if review generation fails

    print("-" * 30)
    logging.info("--- PeerSight Process Finished ---")


if __name__ == "__main__":
    run()
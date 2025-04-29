"""
PeerSight: AI Academic Paper Reviewer
"""
import argparse
import sys
import logging

from . import config
from . import llm_client
from . import utils
from . import prompts

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_arg_parser():
    """Sets up the command-line argument parser."""
    parser = argparse.ArgumentParser(description="PeerSight: AI Academic Paper Reviewer")
    parser.add_argument("paper_path", help="Path to the academic paper plain text file.")
    # Add the optional output file argument
    parser.add_argument(
        "-o", "--output",
        help="Path to save the generated review text file. If not provided, prints to console."
    )
    return parser

def run():
    logging.info("--- PeerSight Process Starting ---")
    parser = setup_arg_parser()
    args = parser.parse_args() # Parse arguments, including the new optional one

    logging.info(f"Review request for paper: {args.paper_path}")
    # Log the output path if provided
    if args.output:
        logging.info(f"Review will be saved to: {args.output}")
    else:
        logging.info("Review will be printed to console.")

    logging.info(f"Using Ollama model: {config.OLLAMA_MODEL}")
    logging.info(f"Ollama API URL: {config.OLLAMA_API_URL}")
    print("-" * 30) # Use print for visual separation

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

    # --- Process and Output Review ---
    if raw_review_output:
        logging.info("Received raw response from LLM.")
        cleaned_review = utils.clean_llm_output(raw_review_output)
        logging.info("Cleaned LLM response.")

        # Decide whether to save to file or print to console
        if args.output:
            logging.info(f"Attempting to save review to file: {args.output}")
            success = utils.write_text_file(args.output, cleaned_review)
            if success:
                print(f"Review successfully saved to: {args.output}") # User confirmation
            else:
                logging.error(f"Failed to save review to file: {args.output}")
                print(f"Error: Failed to save review to {args.output}. Check logs.")
                # Optionally print to console as fallback? For now, just report error.
                # print("\n--- Generated Peer Review (Console Fallback) ---")
                # print(cleaned_review)
                # print("--- End of Review ---")
        else:
            # Print to console if no output file specified
            print("--- Generated Peer Review ---")
            print(cleaned_review)
            print("--- End of Review ---")

    else:
        logging.error("Failed to get review response from Ollama. Check previous logs.")
        print("Error: Failed to generate review. Please check Ollama connection and logs.")
        sys.exit(1)

    print("-" * 30)
    logging.info("--- PeerSight Process Finished ---")


if __name__ == "__main__":
    run()
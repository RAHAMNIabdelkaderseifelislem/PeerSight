"""
PeerSight: AI Academic Paper Reviewer
"""
import argparse # Import argparse
import sys # To exit cleanly on error

from . import config
from . import llm_client
from . import utils # Import the utils module

def setup_arg_parser():
    """Sets up the command-line argument parser."""
    parser = argparse.ArgumentParser(description="PeerSight: AI Academic Paper Reviewer")
    parser.add_argument("paper_path", help="Path to the academic paper plain text file.")
    # Add more arguments later (e.g., output format, specific review sections)
    # parser.add_argument("-o", "--output", help="Path to save the review output file.")
    return parser

def run():
    print(f"--- PeerSight Initializing ---")
    parser = setup_arg_parser()
    args = parser.parse_args() # Parse arguments from the command line

    print(f"Received request to review paper: {args.paper_path}")
    print(f"Using Ollama model: {config.OLLAMA_MODEL}")
    print(f"Connecting to Ollama API at: {config.OLLAMA_API_URL}")
    print("-" * 30)

    # --- Read Paper Content ---
    paper_content = utils.read_text_file(args.paper_path)

    if paper_content is None:
        print(f"Error: Could not read the paper file at '{args.paper_path}'. Exiting.")
        sys.exit(1) # Exit the script with an error code

    print(f"Successfully loaded paper content ({len(paper_content)} characters).")
    print("-" * 30)

    # --- Placeholder for Analysis ---
    # Replace the simple test query with something using the paper content (later)
    print("Next steps: Send paper content (or parts) to LLM for analysis.")
    # For now, let's just run the test query again to ensure the flow works
    test_prompt = "Briefly summarize the concept of Rayleigh scattering."
    print(f"Sending test prompt: '{test_prompt}'")
    response = llm_client.query_ollama(test_prompt)

    print("-" * 30)
    if response:
        print("Received response from Ollama:")
        # Just print the first 500 chars for brevity in this test
        print(response[:500] + "..." if len(response) > 500 else response)
    else:
        print("Failed to get response from Ollama. Check logs for details.")
    print("-" * 30)
    print("--- PeerSight Task Complete (for now) ---")


if __name__ == "__main__":
    run()
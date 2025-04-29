"""
PeerSight: AI Academic Paper Reviewer Command-Line Interface.
Handles argument parsing and invokes the core review generation logic.
"""
import argparse
import sys
import logging

# Import the core review generation function
from . import core
# Import config only if needed directly in main (e.g., display version info),
# otherwise core.py handles necessary config through its imports.
from . import config # Keep for displaying config info

# Configure root logger (best practice)
# This configuration will apply to loggers in core.py, utils.py etc. unless they override it
logging.basicConfig(
    level=logging.INFO, # Set default level (can be overridden by env var later)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
# Example: Get logger for this specific module
logger = logging.getLogger(__name__) # Use __name__ for module-specific logger

def setup_arg_parser():
    """Sets up the command-line argument parser."""
    parser = argparse.ArgumentParser(description="PeerSight: AI Academic Paper Reviewer")
    parser.add_argument("paper_path", help="Path to the academic paper plain text file.")
    parser.add_argument(
        "-o", "--output",
        help="Path to save the generated review text file. If not provided, prints to console."
    )
    # Example: Add a verbosity flag later
    # parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity (DEBUG level)")
    return parser

def run():
    """Main entry point for the CLI application."""
    parser = setup_arg_parser()
    args = parser.parse_args()

    # --- Optional: Setup logging level based on args ---
    # if args.verbose:
    #     logging.getLogger().setLevel(logging.DEBUG) # Set root logger level
    #     logger.debug("Verbose mode enabled.")

    logger.info("--- PeerSight CLI Initializing ---")
    logger.info(f"Configuration: Using Ollama model '{config.OLLAMA_MODEL}' at '{config.OLLAMA_API_URL}'")
    logger.info(f"Processing request for paper: {args.paper_path}")
    if args.output:
        logger.info(f"Output target: File '{args.output}'")
    else:
        logger.info("Output target: Console")
    print("-" * 30) # Keep visual separator

    # --- Invoke Core Logic ---
    # Pass the arguments to the core function
    success = core.generate_review(args.paper_path, args.output)

    print("-" * 30) # Keep visual separator
    if success:
        logger.info("--- PeerSight CLI Finished Successfully ---")
        sys.exit(0) # Exit with success code
    else:
        logger.error("--- PeerSight CLI Finished with Errors ---")
        # Specific error messages should have been printed by core.py or utils.py
        print("Review generation failed. Please check the log messages above for details.", file=sys.stderr)
        sys.exit(1) # Exit with error code

if __name__ == "__main__":
    # This structure allows calling run() if the script is executed directly
    # while also allowing importing main.py without automatically running.
    run()
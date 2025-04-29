"""
PeerSight: AI Academic Paper Reviewer Command-Line Interface.
Handles argument parsing and invokes the core review generation logic.
"""
import argparse
import sys
import logging

from . import core
from . import config
# Import version from package __init__
from . import __version__

# Configure root logger
# We set a default level here, but it can be overridden by command-line args
logging.basicConfig(
    level=logging.INFO, # Default level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def setup_arg_parser():
    """Sets up the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="PeerSight: AI Academic Paper Reviewer",
        # Add epilog for usage examples if desired later
        # epilog="Example: python -m src.peersight.main sample_papers/my_paper.txt -o reviews/my_review.md"
    )
    parser.add_argument("paper_path", help="Path to the academic paper plain text file.")
    parser.add_argument(
        "-o", "--output",
        help="Path to save the generated review text file. If not provided, prints to console."
    )
    # Add verbosity flag (-v for INFO, -vv for DEBUG - typical pattern)
    parser.add_argument(
        '-v', '--verbose',
        action='count', # 'count' increases level each time flag is present
        default=0,
        help="Increase output verbosity (-v for DEBUG, default is INFO)"
    )
    # Add version flag
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}' # Display program name and version
    )
    return parser

def set_logging_level(verbosity_level):
    """Sets the root logging level based on verbosity count."""
    if verbosity_level == 1:
        level = logging.DEBUG
        logger.info("Verbose mode enabled (DEBUG level).")
    elif verbosity_level >= 2: # Allow -vv or more, treat as DEBUG
         level = logging.DEBUG
         logger.info("Verbose mode enabled (DEBUG level).")
    else: # Default (verbosity_level == 0)
        level = logging.INFO

    # Set the level on the root logger
    logging.getLogger().setLevel(level)
    # Log the final effective level
    logger.info(f"Effective logging level set to: {logging.getLevelName(level)}")


def run():
    """Main entry point for the CLI application."""
    parser = setup_arg_parser()
    args = parser.parse_args()

    # --- Setup logging level based on verbosity ---
    set_logging_level(args.verbose) # Call before extensive logging

    logger.info("--- PeerSight CLI Initializing ---")
    logger.debug(f"PeerSight Version: {__version__}") # Log version in debug
    logger.info(f"Configuration: Using Ollama model '{config.OLLAMA_MODEL}' at '{config.OLLAMA_API_URL}'")
    logger.info(f"Processing request for paper: {args.paper_path}")
    if args.output:
        logger.info(f"Output target: File '{args.output}'")
    else:
        logger.info("Output target: Console")
    print("-" * 30) # Keep visual separator

    # --- Invoke Core Logic ---
    success = core.generate_review(args.paper_path, args.output)

    print("-" * 30) # Keep visual separator
    if success:
        logger.info("--- PeerSight CLI Finished Successfully ---")
        sys.exit(0)
    else:
        logger.error("--- PeerSight CLI Finished with Errors ---")
        print("Review generation failed. Please check the log messages above for details.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run()
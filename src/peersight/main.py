"""
PeerSight: AI Academic Paper Reviewer Command-Line Interface.
Handles argument parsing and invokes the core review generation logic.
"""
import argparse
import sys
import logging

from . import core
from . import config
from . import __version__

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def setup_arg_parser():
    """Sets up the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="PeerSight: AI Academic Paper Reviewer"
    )
    # --- Input/Output Arguments ---
    parser.add_argument("paper_path", help="Path to the academic paper plain text file.")
    parser.add_argument(
        "-o", "--output",
        help="Path to save the generated review text file. If not provided, prints to console."
    )

    # --- Configuration Overrides ---
    parser.add_argument(
        "--model",
        help=f"Override the Ollama model to use (default from env/config: {config.OLLAMA_MODEL})"
    )
    parser.add_argument(
        "--api-url",
        help=f"Override the Ollama API URL (default from env/config: {config.OLLAMA_API_URL})"
    )

    # --- Control/Meta Arguments ---
    parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=0,
        help="Increase output verbosity (-v for DEBUG, default is INFO)"
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    return parser

def set_logging_level(verbosity_level):
    """Sets the root logging level based on verbosity count."""
    # ... (keep existing function) ...
    if verbosity_level >= 1: level = logging.DEBUG
    else: level = logging.INFO
    logging.getLogger().setLevel(level)
    # Log only after level is set
    logger.log(level, f"Effective logging level set to: {logging.getLevelName(level)}")


def run():
    """Main entry point for the CLI application."""
    parser = setup_arg_parser()
    args = parser.parse_args()

    set_logging_level(args.verbose)

    logger.info("--- PeerSight CLI Initializing ---")
    logger.debug(f"PeerSight Version: {__version__}")

    # Determine effective model and URL (CLI override or config default)
    effective_model = args.model if args.model else config.OLLAMA_MODEL
    effective_api_url = args.api_url if args.api_url else config.OLLAMA_API_URL

    logger.info(f"Effective Ollama Model: '{effective_model}' "
                f"{'(CLI override)' if args.model else '(from config/env)'}")
    logger.info(f"Effective Ollama API URL: '{effective_api_url}' "
                f"{'(CLI override)' if args.api_url else '(from config/env)'}")

    logger.info(f"Processing request for paper: {args.paper_path}")
    if args.output:
        logger.info(f"Output target: File '{args.output}'")
    else:
        logger.info("Output target: Console")
    print("-" * 30)

    # --- Invoke Core Logic ---
    # Pass the *effective* model and URL (which might be None if not overridden)
    success = core.generate_review(
        paper_path=args.paper_path,
        output_path=args.output,
        model_override=args.model,     # Pass CLI value directly
        api_url_override=args.api_url  # Pass CLI value directly
    )

    print("-" * 30)
    if success:
        logger.info("--- PeerSight CLI Finished Successfully ---")
        sys.exit(0)
    else:
        logger.error("--- PeerSight CLI Finished with Errors ---")
        print("Review generation failed. Please check the log messages above for details.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run()
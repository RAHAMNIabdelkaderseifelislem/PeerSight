"""
PeerSight: AI Academic Paper Reviewer Command-Line Interface.
Handles argument parsing and invokes the core review generation logic.
"""
import argparse
import sys
import logging
import json # Import json for printing JSON output

from . import core
from . import config
from . import __version__
from . import utils

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
        help="Path to save the generated review. Output format depends on --json flag."
    )
    # Add JSON flag
    parser.add_argument(
        "--json",
        action="store_true", # Makes it a boolean flag
        help="Output the review in JSON format instead of plain text."
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
    # ... (keep existing function) ...
    if verbosity_level >= 1: level = logging.DEBUG
    else: level = logging.INFO
    logging.getLogger().setLevel(level)
    logger.log(level, f"Effective logging level set to: {logging.getLevelName(level)}")

def run():
    """Main entry point for the CLI application."""
    parser = setup_arg_parser()
    args = parser.parse_args()

    set_logging_level(args.verbose)

    logger.info("--- PeerSight CLI Initializing ---")
    # ... (log config, paper path etc.) ...
    logger.debug(f"PeerSight Version: {__version__}")
    effective_model = args.model if args.model else config.OLLAMA_MODEL
    effective_api_url = args.api_url if args.api_url else config.OLLAMA_API_URL
    logger.info(f"Effective Ollama Model: '{effective_model}' {'(CLI override)' if args.model else '(from config/env)'}")
    logger.info(f"Effective Ollama API URL: '{effective_api_url}' {'(CLI override)' if args.api_url else '(from config/env)'}")
    logger.info(f"Processing request for paper: {args.paper_path}")
    output_format = "JSON" if args.json else "Text"
    if args.output:
        logger.info(f"Output target: File '{args.output}' (Format: {output_format})")
    else:
        logger.info(f"Output target: Console (Format: {output_format})")

    print("-" * 30)

    # --- Invoke Core Logic ---
    # Pass the JSON flag preference to the core function
    success, result_data = core.generate_review( # Modified to return data
        paper_path=args.paper_path,
        model_override=args.model,
        api_url_override=args.api_url,
        # No need to pass output path or json flag if handled here
    )

    print("-" * 30)

    # --- Handle Output Based on Success and Format ---
    if success:
        logger.info("Review generation successful.")
        output_content = None
        is_json_output = args.json

        if is_json_output:
            if isinstance(result_data, dict):
                try:
                    # Pretty print JSON
                    output_content = json.dumps(result_data, indent=4)
                except TypeError as e:
                     logger.error(f"Failed to serialize review data to JSON: {e}")
                     success = False # Mark as failure if serialization fails
            else:
                logger.error("JSON output requested, but review data is not a dictionary (parsing likely failed). Cannot generate JSON.")
                success = False # Mark as failure
        else: # Text output
            if isinstance(result_data, str):
                output_content = result_data # Use the raw cleaned text
            else:
                logger.error("Text output requested, but review data is not a string. Cannot generate Text.")
                success = False # Mark as failure

        # Proceed with writing/printing if content was generated successfully
        if success and output_content is not None:
            output_successful = False
            if args.output:
                logger.info(f"Attempting to save {output_format} review to file: {args.output}")
                write_success = utils.write_text_file(args.output, output_content)
                if write_success:
                    print(f"Review successfully saved to: {args.output}")
                    output_successful = True
                else:
                    logger.error(f"Failed to save review to file: {args.output}")
                    print(f"Error: Failed to save review to {args.output}. Check logs.", file=sys.stderr)
            else:
                # Print to console
                print(f"\n--- Generated Peer Review ({output_format}) ---")
                print(output_content)
                print(f"--- End of Review ({output_format}) ---\n")
                output_successful = True

            if output_successful:
                 logger.info("--- PeerSight CLI Finished Successfully ---")
                 sys.exit(0)
            else: # File writing failed
                 logger.error("--- PeerSight CLI Finished with Output Errors ---")
                 sys.exit(1)
        else: # Content generation failed (JSON serialization or wrong type)
             logger.error("--- PeerSight CLI Finished with Content Generation Errors ---")
             print("Failed to generate output content in the requested format.", file=sys.stderr)
             sys.exit(1)

    else: # core.generate_review returned success=False
        logger.error("--- PeerSight CLI Finished with Generation Errors ---")
        print("Review generation failed during core processing. Please check the log messages above for details.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
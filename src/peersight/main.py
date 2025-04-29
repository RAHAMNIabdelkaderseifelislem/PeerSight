"""
PeerSight: AI Academic Paper Reviewer Command-Line Interface.
Handles argument parsing and invokes the core review generation logic.
"""
import argparse
import sys
import logging
import json

# It's good practice to have utils imported if needed, e.g., for write_text_file
from . import core, config, __version__, utils

# Configure root logger - moved configuration inside main guard
# This allows testing imports without configuring logging immediately
# logger = logging.getLogger(__name__) # Define logger globally

def setup_logging(level=logging.INFO):
    """Configures root logger."""
    # Make sure handlers are not added multiple times if run() is called again
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
         root_logger.handlers.clear() # Clear existing handlers

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.StreamHandler(sys.stderr)] # Log to stderr by default
    )
    # Get logger for this module specifically AFTER basicConfig
    logger = logging.getLogger(__name__)
    logger.debug("Root logger configured.")
    return logger # Return the module-specific logger if needed elsewhere


def setup_arg_parser():
    """Sets up the command-line argument parser."""
    # ... (parser setup remains the same) ...
    parser = argparse.ArgumentParser(description="PeerSight: AI Academic Paper Reviewer")
    parser.add_argument("paper_path", help="Path to the academic paper plain text file.")
    parser.add_argument("-o", "--output", help="Path to save the generated review. Output format depends on --json flag.")
    parser.add_argument("--json", action="store_true", help="Output the review in JSON format instead of plain text.")
    parser.add_argument("--model", help=f"Override the Ollama model to use (default from env/config: {config.OLLAMA_MODEL})")
    parser.add_argument("--api-url", help=f"Override the Ollama API URL (default from env/config: {config.OLLAMA_API_URL})")
    parser.add_argument('-v', '--verbose', action='count', default=0, help="Increase output verbosity (-v for DEBUG, default is INFO)")
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    return parser


def set_logging_level(verbosity_level):
    """Sets the root logging level based on verbosity count."""
    if verbosity_level >= 1: level = logging.DEBUG
    else: level = logging.INFO
    current_level_name = logging.getLevelName(logging.getLogger().getEffectiveLevel())
    new_level_name = logging.getLevelName(level)
    if current_level_name != new_level_name:
        logging.getLogger().setLevel(level)
        # Logger might not be configured yet here, use print for bootstrap phase if needed
        # print(f"Effective logging level set to: {new_level_name}")
        logging.log(level, f"Effective logging level set to: {new_level_name}") # Log after level is set

def run():
    """Main entry point for the CLI application."""
    # Move logger setup here, after potential level change by args
    # Default to INFO, will be adjusted by set_logging_level if needed
    logger = setup_logging()

    try:
        parser = setup_arg_parser()
        args = parser.parse_args()

        # Adjust logging level based on args AFTER initial setup
        set_logging_level(args.verbose)

        logger.info("--- PeerSight CLI Initializing ---")
        logger.debug(f"PeerSight Version: {__version__}")
        # ... (log config, paper path etc.) ...
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

        print("-" * 30, file=sys.stderr) # Print separators to stderr to not interfere with stdout json


        # --- Invoke Core Logic ---
        # This is the main part to wrap
        success, result_data = core.generate_review(
            paper_path=args.paper_path,
            model_override=args.model,
            api_url_override=args.api_url,
        )

        print("-" * 30, file=sys.stderr) # Separator to stderr

        # --- Handle Output Based on Success and Format ---
        if success:
            logger.info("Review generation successful.")
            output_content = None
            is_json_output = args.json
            # ... (JSON/Text formatting logic remains the same) ...
            if is_json_output:
                if isinstance(result_data, dict):
                    try: output_content = json.dumps(result_data, indent=4)
                    except TypeError as e: logger.error(f"Failed to serialize review data to JSON: {e}"); success = False
                else: logger.error("JSON output requested, but review data is not a dictionary."); success = False
            else: # Text output
                if isinstance(result_data, str): output_content = result_data
                else: logger.error("Text output requested, but review data is not a string."); success = False

            if success and output_content is not None:
                output_successful = False
                if args.output:
                    # ... (File writing logic) ...
                    logger.info(f"Attempting to save {output_format} review to file: {args.output}")
                    write_success = utils.write_text_file(args.output, output_content)
                    if write_success: print(f"Review successfully saved to: {args.output}", file=sys.stderr); output_successful = True # Print confirmation to stderr
                    else: logger.error(f"Failed to save review to file: {args.output}"); print(f"Error: Failed to save review to {args.output}. Check logs.", file=sys.stderr)
                else:
                    # Print to console (stdout)
                    print(output_content) # Print the actual review content to stdout
                    output_successful = True # Assume printing to stdout is successful

                if output_successful:
                     logger.info("--- PeerSight CLI Finished Successfully ---")
                     sys.exit(0)
                else: # File writing failed
                     logger.error("--- PeerSight CLI Finished with Output Errors ---")
                     sys.exit(1)
            else: # Content generation failed
                 logger.error("--- PeerSight CLI Finished with Content Generation Errors ---")
                 print("Failed to generate output content in the requested format.", file=sys.stderr)
                 sys.exit(1)

        else: # core.generate_review returned success=False
            logger.error("--- PeerSight CLI Finished with Generation Errors ---")
            # Core function should have logged specifics
            print("Review generation failed during core processing. Check logs.", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        # Catch any unexpected exception from the whole process
        logger.critical(f"An unexpected critical error occurred: {e}", exc_info=True) # Log traceback
        print(f"\nAn unexpected error occurred. Please check the logs for details.", file=sys.stderr)
        sys.exit(2) # Use a different exit code for unexpected errors

if __name__ == "__main__":
    run()
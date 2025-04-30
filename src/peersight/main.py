"""
PeerSight: AI Academic Paper Reviewer Command-Line Interface.
Handles argument parsing and invokes the core review generation logic.
"""

import argparse
import json
import logging
import sys

# It's good practice to have utils imported if needed, e.g., for write_text_file
from . import __version__, config, core, prompts, utils  # Import prompts for headers

# Define logger at module level, configure it in setup_logging
logger = logging.getLogger(__name__)


def setup_logging(level=logging.INFO):
    """Configures root logger."""
    # Make sure handlers are not added multiple times if run() is called again
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()  # Clear existing handlers

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stderr)],  # Log to stderr by default
    )
    # Get logger for this module specifically AFTER basicConfig
    # Re-assign to the module-level logger variable
    global logger
    logger = logging.getLogger(__name__)
    logger.debug("Root logger configured.")
    # Return logger if needed, but module-level var is now set
    # return logger


def setup_arg_parser():
    """Sets up the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="PeerSight: AI Academic Paper Reviewer"
    )
    # --- Input/Output Arguments ---
    parser.add_argument(
        "paper_path", help="Path to the academic paper plain text file."
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Path to save the generated review. Output format depends on --json flag.",
    )
    parser.add_argument(
        "--json",
        action="store_true",  # Makes it a boolean flag
        help="Output the review in JSON format instead of plain text.",
    )

    # --- Configuration Overrides ---
    parser.add_argument(
        "--model",
        help=f"Override the Ollama model to use (default: {config.OLLAMA_MODEL})",
    )
    parser.add_argument(
        "--api-url",
        help=f"Override the Ollama API URL (default: {config.OLLAMA_API_URL})",
    )
    parser.add_argument(
        "-t",
        "--temperature",
        type=float,  # Expect a float value
        default=None,  # Default is None, so config value is used unless overridden
        help=f"Set the LLM temperature (default: {config.OLLAMA_TEMPERATURE})",
    )

    # Add top_k and top_p arguments
    parser.add_argument(
        "--top-k", type=int, default=None,
        help=f"Set LLM top-k sampling (e.g., 40; default: Ollama internal)"
    )
    parser.add_argument(
        "--top-p", type=float, default=None,
        help=f"Set LLM top-p nucleus sampling (e.g., 0.9; default: Ollama internal)"
    )
    # --- Control/Meta Arguments ---
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase output verbosity (-v for DEBUG, default is INFO)",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser


def set_logging_level(verbosity_level):
    """Sets the root logging level based on verbosity count."""
    if verbosity_level >= 1:
        level = logging.DEBUG
    else:
        level = logging.INFO
    # Check current level *before* setting to avoid redundant messages if already set
    current_level_name = logging.getLevelName(logging.getLogger().getEffectiveLevel())
    new_level_name = logging.getLevelName(level)
    if current_level_name != new_level_name:
        logging.getLogger().setLevel(level)
        # Use the module-level logger here
        logger.log(level, f"Effective logging level set to: {new_level_name}")


def format_review_dict_to_text(review_dict: dict) -> str:
    """Formats the parsed review dictionary back into text."""
    # Ensure order matches standard output
    parts = [
        prompts.REVIEW_SECTION_SUMMARY,
        review_dict.get("summary", ""),  # Use .get for safety
        prompts.REVIEW_SECTION_STRENGTHS,
        review_dict.get("strengths", ""),
        prompts.REVIEW_SECTION_WEAKNESSES,
        review_dict.get("weaknesses", ""),
        prompts.REVIEW_SECTION_RECOMMENDATION,
        review_dict.get("recommendation", ""),
    ]
    # Join parts with double newlines between sections for readability
    # Strip each part and filter out None before joining
    return "\n\n".join(p.strip() for p in parts if p is not None)


def run():
    """Main entry point for the CLI application."""
    # Setup logger with default level first
    setup_logging()

    try:
        parser = setup_arg_parser()
        args = parser.parse_args()

        # Adjust logging level based on args AFTER initial setup
        set_logging_level(args.verbose)

        logger.info("--- PeerSight CLI Initializing ---")
        logger.debug(f"PeerSight Version: {__version__}")

        # Determine effective config values
        effective_model = args.model if args.model else config.OLLAMA_MODEL
        effective_api_url = args.api_url if args.api_url else config.OLLAMA_API_URL
        effective_temperature = (
            args.temperature
            if args.temperature is not None
            else config.OLLAMA_TEMPERATURE
        )
        # Determine effective top_k/top_p (None if not set via CLI)
        effective_top_k = (
            args.top_k 
            if args.top_k is not None 
            else config.OLLAMA_TOP_K
        )
        effective_top_p = (
            args.top_p
            if args.top_p is not None 
            else config.OLLAMA_TOP_P
        )

        logger.info(
            f"Effective Ollama Model: '{effective_model}' "
            f"{'(CLI override)' if args.model else '(from config/env)'}"
        )
        logger.info(
            f"Effective Ollama API URL: '{effective_api_url}' "
            f"{'(CLI override)' if args.api_url else '(from config/env)'}"
        )
        logger.info(
            f"Effective LLM Temperature: {effective_temperature} "
            f"{'(CLI override)' if args.temperature is not None else '(from config/env)'}"
        )
        # Log effective top_k/top_p, indicating if default is used
        logger.info(f"Effective LLM Top-K: "
                    f"{effective_top_k if effective_top_k is not None else 'Ollama Default'} "
                    f"{'(CLI override)' if effective_top_k is not None else ''}")
        logger.info(f"Effective LLM Top-P: "
                    f"{effective_top_p if effective_top_p is not None else 'Ollama Default'} "
                    f"{'(CLI override)' if effective_top_p is not None else ''}")

        logger.info(f"Processing request for paper: {args.paper_path}")
        output_format = "JSON" if args.json else "Text"
        if args.output:
            logger.info(
                f"Output target: File '{args.output}' (Format: {output_format})"
            )
        else:
            logger.info(f"Output target: Console (Format: {output_format})")

        print("-" * 30, file=sys.stderr)  # Print separators to stderr

        # --- Invoke Core Logic ---
        success, result_data = core.generate_review(
            paper_path=args.paper_path,
            model_override=args.model,
            api_url_override=args.api_url,
            temperature_override=args.temperature,
            top_k_override=args.top_k,
            top_p_override=args.top_p,
        )

        print("-" * 30, file=sys.stderr)  # Separator to stderr

        # --- Handle Output Based on Success and Format ---
        if success:
            logger.info("Review generation successful.")
            output_content = None
            is_json_output = args.json

            if is_json_output:
                # --- JSON Output ---
                if isinstance(result_data, dict):
                    try:
                        # Pretty print JSON
                        output_content = json.dumps(result_data, indent=4)
                    except TypeError as e:
                        logger.error(f"Failed to serialize review data to JSON: {e}")
                        success = False  # Mark as failure if serialization fails
                else:
                    logger.error(
                        f"JSON output requested, but review data is not a dictionary (Parsing likely failed: {type(result_data)}). Cannot generate JSON."
                    )
                    success = False  # Mark as failure
            else:
                # --- Text Output ---
                if isinstance(result_data, dict):
                    # Parsing succeeded, reconstruct text from dict
                    logger.info(
                        "Parsing succeeded. Reconstructing text output from parsed data."
                    )
                    output_content = format_review_dict_to_text(result_data)
                elif isinstance(result_data, str):
                    # Parsing failed, use the raw cleaned text provided by core
                    logger.info("Parsing failed. Using raw cleaned text for output.")
                    output_content = result_data
                else:
                    # Should not happen if core returns correctly, but handle anyway
                    logger.error(
                        f"Text output requested, but review data is neither dict nor string ({type(result_data)}). Cannot generate Text."
                    )
                    success = False

            # Proceed with writing/printing if content was generated successfully
            if success and output_content is not None:
                output_successful = False
                if args.output:
                    logger.info(
                        f"Attempting to save {output_format} review to file: {args.output}"
                    )
                    write_success = utils.write_text_file(args.output, output_content)
                    if write_success:
                        print(
                            f"Review successfully saved to: {args.output}",
                            file=sys.stderr,
                        )  # Print confirmation to stderr
                        output_successful = True
                    else:
                        logger.error(f"Failed to save review to file: {args.output}")
                        print(
                            f"Error: Failed to save review to {args.output}. Check logs.",
                            file=sys.stderr,
                        )
                else:
                    # Print to console (stdout)
                    print(output_content)  # Print the actual review content to stdout
                    output_successful = True  # Assume printing to stdout is successful

                if output_successful:
                    logger.info("--- PeerSight CLI Finished Successfully ---")
                    sys.exit(0)
                else:  # File writing failed
                    logger.error("--- PeerSight CLI Finished with Output Errors ---")
                    sys.exit(1)
            else:  # Content generation failed (JSON error or unexpected data type)
                logger.error(
                    "--- PeerSight CLI Finished with Content Generation Errors ---"
                )
                print(
                    "Failed to generate output content in the requested format.",
                    file=sys.stderr,
                )
                sys.exit(1)

        else:  # core.generate_review returned success=False
            logger.error("--- PeerSight CLI Finished with Generation Errors ---")
            # Core function should have logged specifics
            print(
                "Review generation failed during core processing. Check logs.",
                file=sys.stderr,
            )
            sys.exit(1)

    except Exception as e:
        # Catch any unexpected exception from the whole process
        # Use module-level logger; assumes setup_logging ran or has default config
        logger.critical(
            f"An unexpected critical error occurred: {e}", exc_info=True
        )  # Log traceback
        print(
            "\nAn unexpected error occurred. Please check the logs for details.",
            file=sys.stderr,
        )
        sys.exit(2)  # Use a different exit code for unexpected errors


if __name__ == "__main__":
    run()

"""
PeerSight: AI Academic Paper Reviewer Command-Line Interface.
Handles argument parsing and invokes the core review generation logic.
"""

import argparse
import json
import logging
import sys
from typing import Any, Dict, Optional, Union  # Added Any

from . import __version__, config, core, prompts, utils

# Define logger at module level, configure it in setup_logging
logger = logging.getLogger(__name__)


def setup_logging(level=logging.INFO):
    """Configures root logger."""
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()  # Moved clear to own line

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stderr)],
    )
    global logger
    logger = logging.getLogger(__name__)  # Separate line
    logger.debug("Root logger configured.")  # Separate line


def setup_arg_parser():
    parser = argparse.ArgumentParser(
        description="PeerSight: AI Academic Paper Reviewer"
    )
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
        action="store_true",
        help="Output the review in JSON format instead of plain text.",
    )
    parser.add_argument(
        "--model", help=f"Override the Ollama model (default: {config.OLLAMA_MODEL})"
    )
    parser.add_argument(
        "--api-url",
        help=f"Override the Ollama API URL (default: {config.OLLAMA_API_URL})",
    )
    parser.add_argument(
        "-t",
        "--temperature",
        type=float,
        default=None,
        help=f"Set LLM temperature (default: {config.OLLAMA_TEMPERATURE})",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Set LLM top-k sampling (e.g., 40; default: Ollama internal)",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=None,
        help="Set LLM top-p nucleus sampling (e.g., 0.9; default: Ollama internal)",
    )
    # --- Add Web Search Flags ---
    search_engines = ["google_scholar", "pubmed", "semantic_scholar", "arxiv", "google"]
    parser.add_argument(
        "--search",
        action="store_true",
        help="Perform a web search for the paper title (opens browser).",
    )
    parser.add_argument(
        "--search-engine",
        choices=search_engines,
        default="google_scholar",
        help=f"Search engine to use with --search (default: google_scholar). Choices: {', '.join(search_engines)}",
    )
    parser.add_argument(
        "--check-references",
        action="store_true",
        help="Attempt to extract references and (in future) check their existence. (Experimental)",
    )
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
    if verbosity_level >= 1:
        level = logging.DEBUG
    else:
        level = logging.INFO
    current_level_name = logging.getLevelName(logging.getLogger().getEffectiveLevel())
    new_level_name = logging.getLevelName(level)
    if current_level_name != new_level_name:
        logging.getLogger().setLevel(level)
        logger.log(level, f"Effective logging level set to: {new_level_name}")


def format_review_dict_to_text(review_dict: Dict[str, Any]) -> str:
    """Formats the parsed review dictionary back into text."""
    # ... (Keep this helper function as is) ...
    parts = [
        prompts.REVIEW_SECTION_SUMMARY,
        review_dict.get("summary", ""),
        prompts.REVIEW_SECTION_STRENGTHS,
        review_dict.get("strengths", ""),
        prompts.REVIEW_SECTION_WEAKNESSES,
        review_dict.get("weaknesses", ""),
        prompts.REVIEW_SECTION_RECOMMENDATION,
        review_dict.get("recommendation", ""),
    ]
    return "\n\n".join(p.strip() for p in parts if p is not None)


def handle_output(
    result_data: Optional[Union[Dict, str]],
    output_path: Optional[str],
    is_json_output: bool,
) -> bool:
    """Handles formatting and writing/printing the output."""
    output_content: Optional[str] = None
    output_format = "JSON" if is_json_output else "Text"
    success = True  # Assume success unless formatting fails

    if is_json_output:
        # --- JSON Output ---
        if isinstance(result_data, dict):
            try:
                output_content = json.dumps(result_data, indent=4)
            except TypeError as e:
                logger.error(f"Failed to serialize review data to JSON: {e}")
                success = False
        else:
            logger.error(
                f"JSON output requested, but review data is {type(result_data)}. Cannot generate JSON."
            )
            success = False
    else:
        # --- Text Output ---
        if isinstance(result_data, dict):
            logger.debug("Reconstructing text output from parsed data.")
            output_content = format_review_dict_to_text(result_data)
        elif isinstance(result_data, str):
            logger.debug("Using raw cleaned text for output.")
            output_content = result_data
        else:
            logger.error(
                f"Text output requested, but review data is {type(result_data)}. Cannot generate Text."
            )
            success = False

    # Proceed with writing/printing only if formatting succeeded
    if success and output_content is not None:
        if output_path:
            logger.info(
                f"Attempting to save {output_format} review to file: {output_path}"
            )
            write_success = utils.write_text_file(output_path, output_content)
            if write_success:
                print(f"Review successfully saved to: {output_path}", file=sys.stderr)
                return True  # Overall output success
            else:
                logger.error(f"Failed to save review to file: {output_path}")
                print(
                    f"Error: Failed to save review to {output_path}. Check logs.",
                    file=sys.stderr,
                )
                return False  # Output failed
        else:
            # Print to console (stdout)
            print(output_content)  # Print the actual review content to stdout
            return True  # Overall output success
    else:
        # Formatting failed or content was None
        logger.error("Failed to generate output content in the requested format.")
        print(
            "Failed to generate output content in the requested format.",
            file=sys.stderr,
        )
        return False  # Output failed


def run():
    """Main entry point for the CLI application."""
    setup_logging()  # Configure logging first
    exit_code = 0  # Default success exit code
    try:
        parser = setup_arg_parser()
        args = parser.parse_args()
        set_logging_level(args.verbose)  # Set level based on args

        # --- Log Initial Config ---
        logger.info("--- PeerSight CLI Initializing ---")
        # ... (logging version, effective config, paths - keep this part) ...
        logger.debug(f"PeerSight Version: {__version__}")
        effective_model = args.model if args.model else config.OLLAMA_MODEL
        effective_api_url = args.api_url if args.api_url else config.OLLAMA_API_URL
        effective_temperature = (
            args.temperature
            if args.temperature is not None
            else config.OLLAMA_TEMPERATURE
        )
        effective_top_k = args.top_k
        effective_top_p = args.top_p
        logger.info(
            f"Effective Ollama Model: '{effective_model}' {'(CLI override)' if args.model else '(from config/env)'}"
        )
        logger.info(
            f"Effective Ollama API URL: '{effective_api_url}' {'(CLI override)' if args.api_url else '(from config/env)'}"
        )
        logger.info(
            f"Effective LLM Temperature: {effective_temperature} {'(CLI override)' if args.temperature is not None else '(from config/env)'}"
        )
        logger.info(
            f"Effective LLM Top-K: {effective_top_k if effective_top_k is not None else 'Ollama Default'} {'(CLI override)' if effective_top_k is not None else ''}"
        )
        logger.info(
            f"Effective LLM Top-P: {effective_top_p if effective_top_p is not None else 'Ollama Default'} {'(CLI override)' if effective_top_p is not None else ''}"
        )
        logger.info(f"Processing request for paper: {args.paper_path}")
        output_format = "JSON" if args.json else "Text"
        if args.output:
            logger.info(
                f"Output target: File '{args.output}' (Format: {output_format})"
            )
        else:
            logger.info(f"Output target: Console (Format: {output_format})")

        print("-" * 30, file=sys.stderr)

        # --- Invoke Core Logic ---
        core_success, result_data = core.generate_review(
            paper_path=args.paper_path,
            model_override=args.model,
            api_url_override=args.api_url,
            temperature_override=args.temperature,
            top_k_override=args.top_k,
            top_p_override=args.top_p,
            perform_web_search=args.search,  # Pass search flag
            search_engine=args.search_engine,  # Pass search engine
            check_references=args.check_references,  # Pass check references flag
        )

        print("-" * 30, file=sys.stderr)

        # --- Handle Output ---
        if core_success:
            logger.info("Core review generation successful.")
            output_success = handle_output(result_data, args.output, args.json)
            if output_success:
                logger.info("--- PeerSight CLI Finished Successfully ---")
                exit_code = 0
            else:
                logger.error("--- PeerSight CLI Finished with Output Errors ---")
                exit_code = 1  # Specific exit code for output failure
        else:
            logger.error("--- PeerSight CLI Finished with Generation Errors ---")
            print(
                "Review generation failed during core processing. Check logs.",
                file=sys.stderr,
            )
            exit_code = 1  # Same code for core or output failure? Maybe distinguish? Let's use 1 for now.

    except Exception as e:
        logger.critical(f"An unexpected critical error occurred: {e}", exc_info=True)
        print(
            "\nAn unexpected error occurred. Please check the logs for details.",
            file=sys.stderr,
        )
        exit_code = 2  # Unexpected error code

    finally:
        # Ensure sys.exit is called outside the main try block if needed
        # Although calling it inside is also common practice.
        sys.exit(exit_code)


if __name__ == "__main__":
    run()

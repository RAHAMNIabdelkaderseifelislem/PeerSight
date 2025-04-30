"""
PeerSight: AI Academic Paper Reviewer Command-Line Interface.
Handles argument parsing and invokes the core review generation logic.
"""
import argparse
import sys
import logging
import json

from . import core, config, __version__, utils, prompts # Import prompts for headers

# ... (setup_logging, setup_arg_parser, set_logging_level remain the same) ...
def setup_logging(level=logging.INFO):
    root_logger = logging.getLogger();
    if root_logger.hasHandlers(): root_logger.handlers.clear()
    logging.basicConfig(level=level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S', handlers=[logging.StreamHandler(sys.stderr)])
    logger = logging.getLogger(__name__); logger.debug("Root logger configured.")
    return logger

def setup_arg_parser():
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
    if verbosity_level >= 1: level = logging.DEBUG
    else: level = logging.INFO
    current_level_name = logging.getLevelName(logging.getLogger().getEffectiveLevel())
    new_level_name = logging.getLevelName(level)
    if current_level_name != new_level_name:
        logging.getLogger().setLevel(level)
        logging.log(level, f"Effective logging level set to: {new_level_name}")


def format_review_dict_to_text(review_dict: dict) -> str:
    """Formats the parsed review dictionary back into text."""
    # Ensure order matches standard output
    parts = [
        prompts.REVIEW_SECTION_SUMMARY,
        review_dict.get('summary', ''), # Use .get for safety
        prompts.REVIEW_SECTION_STRENGTHS,
        review_dict.get('strengths', ''),
        prompts.REVIEW_SECTION_WEAKNESSES,
        review_dict.get('weaknesses', ''),
        prompts.REVIEW_SECTION_RECOMMENDATION,
        review_dict.get('recommendation', '')
    ]
    # Join parts with double newlines between sections for readability
    return "\n\n".join(p.strip() for p in parts if p is not None) # Strip each part

def run():
    """Main entry point for the CLI application."""
    logger = setup_logging()
    try:
        parser = setup_arg_parser()
        args = parser.parse_args()
        set_logging_level(args.verbose)

        logger.info("--- PeerSight CLI Initializing ---")
        # ... (log config, etc.) ...
        logger.info(f"Processing request for paper: {args.paper_path}")
        output_format = "JSON" if args.json else "Text"
        # ... (log output target) ...
        print("-" * 30, file=sys.stderr)

        # --- Invoke Core Logic ---
        success, result_data = core.generate_review(
            paper_path=args.paper_path,
            model_override=args.model,
            api_url_override=args.api_url,
        )

        print("-" * 30, file=sys.stderr)

        # --- Handle Output Based on Success and Format ---
        if success:
            logger.info("Review generation successful.")
            output_content = None
            is_json_output = args.json

            if is_json_output:
                # --- JSON Output ---
                if isinstance(result_data, dict):
                    try: output_content = json.dumps(result_data, indent=4)
                    except TypeError as e: logger.error(f"Failed to serialize review data to JSON: {e}"); success = False
                else:
                     logger.error(f"JSON output requested, but review data is not a dictionary (Parsing likely failed: {type(result_data)}). Cannot generate JSON.")
                     success = False
            else:
                # --- Text Output ---
                if isinstance(result_data, dict):
                    # Parsing succeeded, reconstruct text from dict
                    logger.info("Parsing succeeded. Reconstructing text output from parsed data.")
                    output_content = format_review_dict_to_text(result_data)
                elif isinstance(result_data, str):
                    # Parsing failed, use the raw cleaned text provided by core
                    logger.info("Parsing failed. Using raw cleaned text for output.")
                    output_content = result_data
                else:
                    # Should not happen if core returns correctly, but handle anyway
                    logger.error(f"Text output requested, but review data is neither dict nor string ({type(result_data)}). Cannot generate Text.")
                    success = False

            # Proceed with writing/printing if content was generated successfully
            if success and output_content is not None:
                # ... (output writing/printing logic remains the same) ...
                output_successful = False
                if args.output:
                    logger.info(f"Attempting to save {output_format} review to file: {args.output}")
                    write_success = utils.write_text_file(args.output, output_content)
                    if write_success: print(f"Review successfully saved to: {args.output}", file=sys.stderr); output_successful = True
                    else: logger.error(f"Failed to save review to file: {args.output}"); print(f"Error: Failed to save review to {args.output}. Check logs.", file=sys.stderr)
                else:
                    print(output_content) # Print the actual review content to stdout
                    output_successful = True

                if output_successful: logger.info("--- PeerSight CLI Finished Successfully ---"); sys.exit(0)
                else: logger.error("--- PeerSight CLI Finished with Output Errors ---"); sys.exit(1) # File writing failed
            else: # Content generation failed (JSON error or unexpected data type)
                 logger.error("--- PeerSight CLI Finished with Content Generation Errors ---")
                 print("Failed to generate output content in the requested format.", file=sys.stderr); sys.exit(1)

        else: # core.generate_review returned success=False
            # ... (handle core failure) ...
             logger.error("--- PeerSight CLI Finished with Generation Errors ---")
             print("Review generation failed during core processing. Check logs.", file=sys.stderr); sys.exit(1)

    except Exception as e:
        # ... (handle unexpected exceptions) ...
        logger.critical(f"An unexpected critical error occurred: {e}", exc_info=True)
        print(f"\nAn unexpected error occurred. Please check the logs for details.", file=sys.stderr); sys.exit(2)

if __name__ == "__main__":
    run()
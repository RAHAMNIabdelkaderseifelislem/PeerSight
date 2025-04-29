import logging
import re
import os
from . import config
from . import prompts

# Adjust logging level as needed for debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

# --- File Reading ---
def read_text_file(file_path: str, encoding: str = None) -> str | None:
    # ... (keep existing read_text_file function) ...
    resolved_encoding = encoding if encoding else config.DEFAULT_ENCODING
    logger.info(f"Attempting to read file: {file_path} with encoding {resolved_encoding}")
    try:
        with open(file_path, 'r', encoding=resolved_encoding) as f:
            content = f.read()
        logger.info(f"Successfully read {len(content)} characters from {file_path}")
        return content
    except FileNotFoundError:
        logger.error(f"File Not Found Error: The file '{file_path}' was not found.")
        return None
    except IOError as e:
        logger.error(f"IO Error: An error occurred while reading the file '{file_path}'. Details: {e}")
        return None
    except UnicodeDecodeError as e:
         logger.error(f"Encoding Error: Failed to decode file '{file_path}' with encoding '{resolved_encoding}'. Try specifying a different encoding. Details: {e}")
         return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while reading file '{file_path}': {e}", exc_info=True)
        return None


# --- File Writing ---
def write_text_file(file_path: str, content: str, encoding: str = None) -> bool:
    # ... (keep existing write_text_file function) ...
    resolved_encoding = encoding if encoding else config.DEFAULT_ENCODING
    logger.info(f"Attempting to write {len(content)} characters to file: {file_path} with encoding {resolved_encoding}")
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding=resolved_encoding) as f:
            f.write(content)
        logger.info(f"Successfully wrote content to {file_path}")
        return True
    except IOError as e:
        logger.error(f"IO Error: An error occurred while writing to the file '{file_path}'. Details: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while writing file '{file_path}': {e}", exc_info=True)
        return False

# --- LLM Output Cleaning ---
def clean_llm_output(raw_output: str) -> str:
    """
    Cleans the raw LLM output to extract the structured review.
    Finds start (## Summary), finds recommendation header, then finds
    the next boundary (e.g., ## header, <think>, etc.) to mark the end.
    """
    logger.debug(f"Raw LLM output received for cleaning:\n---\n{raw_output}\n---")

    # 1. Find the start of the structured review
    start_marker = prompts.REVIEW_SECTION_SUMMARY
    start_index = raw_output.find(start_marker)

    if start_index == -1:
        logger.warning(f"Could not find the start marker '{start_marker}' in LLM output. Returning raw output.")
        return raw_output.strip()

    # Extract text from the start marker onwards
    review_potential = raw_output[start_index:]
    logger.debug(f"Text potentially containing review (from start marker):\n---\n{review_potential}\n---")

    # 2. Find the start of the Recommendation section within the potential review text
    recommendation_marker = prompts.REVIEW_SECTION_RECOMMENDATION
    # Find relative to the start of review_potential
    recommendation_start_index_rel = review_potential.find(recommendation_marker)

    if recommendation_start_index_rel == -1:
        logger.warning(f"Could not find recommendation marker '{recommendation_marker}' after start marker. Using regex fallback on original text.")
        # Fallback to regex method on the *original* raw_output if structure is broken
        return _clean_with_regex_fallback(raw_output)

    # 3. Define markers that indicate the END of the review content
    # These should appear *after* the recommendation header text
    next_section_marker = r'^\s*## ' # Start of any *new* section after Recommendation
    # Re-use the fallback markers that indicate meta-commentary etc.
    fallback_end_markers = [
         r'<\/?think>', r'alright, let me', r'okay, so I need', r'okay, so I\'ve got',
         r'here\'s my thought process', r'\bstep-by-step\b', r'thinking process:',
         r'internal thoughts:', r'my reasoning:', r'please note that',
         r'--- END REVIEW ---', r'^\s*Note:',
         # Avoid matching the ## Summary marker here as it's handled by start_index
    ]
    # Combine patterns. Search starts AFTER the recommendation header text ends.
    search_start_pos = recommendation_start_index_rel + len(recommendation_marker)
    end_pattern = re.compile(r'(' + next_section_marker + '|' + '|'.join(fallback_end_markers) + r')', re.IGNORECASE | re.MULTILINE)

    # 4. Search for the first end marker *after* the recommendation header in review_potential
    match = end_pattern.search(review_potential, pos=search_start_pos)

    end_index = -1 # Default to end of string if no marker found
    if match:
        # Found a marker indicating the end of the desired content
        end_index = match.start() # Slice up to the start of the marker
        logger.info(f"Found end boundary '{match.group(0).strip()}' after recommendation at index {end_index} relative to start marker. Truncating.")
    else:
        # No end marker found, assume review goes to the end of the string
        end_index = len(review_potential)
        logger.info("No end boundary found after recommendation marker. Assuming review ends here.")

    # 5. Extract the cleaned review by slicing review_potential
    cleaned_output = review_potential[:end_index].strip()

    # Final sanity check (ensure ## Summary and ## Recommendation are still present)
    if not cleaned_output.startswith(start_marker):
         logger.warning(f"Cleaned output invalid: does not start with '{start_marker}'. Output:\n{cleaned_output}")
         # Consider returning original or fallback result? For now, return broken output.
    elif recommendation_marker not in cleaned_output:
         logger.warning(f"Cleaned output invalid: recommendation marker '{recommendation_marker}' missing. Output:\n{cleaned_output}")
         # This shouldn't happen if recommendation_start_index_rel was found, unless end_index was wrong.

    logger.debug(f"Corrected structure-based cleaned LLM output:\n---\n{cleaned_output}\n---")
    return cleaned_output

# Helper function for fallback cleaning (remains unchanged)
def _clean_with_regex_fallback(raw_output: str) -> str:
    """Fallback cleaning using regex end markers if primary structure fails."""
    logger.warning("Executing regex-based fallback cleaning.")
    start_marker = prompts.REVIEW_SECTION_SUMMARY
    start_index = raw_output.find(start_marker)
    if start_index == -1: return raw_output.strip()

    review_text = raw_output[start_index:]
    # Keep the original comprehensive list for fallback
    end_markers = [
         r'<\/?think>', r'alright, let me', r'okay, so I need', r'okay, so I\'ve got',
         r'here\'s my thought process', r'\bstep-by-step\b', r'thinking process:',
         r'internal thoughts:', r'my reasoning:', r'please note that',
         r'--- END REVIEW ---', r'^\s*## ' + re.escape(prompts.REVIEW_SECTION_SUMMARY.strip('# ')), # Match repeated Summary
         r'^\s*Note:', r'^\s*Summary:',
    ]
    end_pattern = re.compile(r'(' + '|'.join(end_markers) + r')', re.IGNORECASE | re.MULTILINE)
    search_start_pos = len(start_marker) # Search after the initial Summary marker
    match = end_pattern.search(review_text, pos=search_start_pos)

    cleaned_output = review_text
    if match:
        end_index = match.start()
        logger.info(f"[Fallback] Found end marker '{match.group(0).strip()}' at index {end_index}. Truncating.")
        cleaned_output = review_text[:end_index].strip()
    else:
        logger.info("[Fallback] No specific end marker found. Assuming remainder is the review.")
        cleaned_output = review_text.strip()

    if not cleaned_output.strip().startswith(start_marker):
         logger.warning(f"[Fallback] Cleaned output invalid: does not start with '{start_marker}'.")

    return cleaned_output
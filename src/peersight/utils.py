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
    Cleans the raw LLM output to extract only the structured review.
    Finds the start (## Summary) and the end of the recommendation line.
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
    recommendation_start_index = review_potential.find(recommendation_marker)

    if recommendation_start_index == -1:
        logger.warning(f"Could not find recommendation marker '{recommendation_marker}' after start marker. Trying less strict cleaning.")
        # Fallback: Use the previous regex method if strict structure fails
        return _clean_with_regex_fallback(raw_output) # Call a helper for fallback

    # 3. Find the end of the recommendation line (first newline after the recommendation marker)
    # Start searching for newline AFTER the marker text itself
    newline_search_start = recommendation_start_index + len(recommendation_marker)
    end_of_recommendation_line = review_potential.find('\n', newline_search_start)

    # Define the end index for slicing
    end_index = -1

    if end_of_recommendation_line != -1:
        # Found a newline, slice up to and including it
        end_index = end_of_recommendation_line + 1 # Include the newline itself? Maybe just up to it. Let's test slicing up *to* it.
        end_index = end_of_recommendation_line
        logger.info(f"Found end of recommendation line at index {end_index} relative to start marker.")
    else:
        # No newline found after recommendation (means recommendation is the very last thing)
        # Slice until the end of the string
        end_index = len(review_potential)
        logger.info("No newline found after recommendation marker. Assuming recommendation is the end of the review.")

    # 4. Extract the cleaned review
    cleaned_output = review_potential[:end_index].strip() # Slice from start marker to determined end index

    # Final sanity check
    if not cleaned_output.startswith(start_marker) or recommendation_marker not in cleaned_output:
        logger.warning(f"Cleaned output appears invalid (missing start or recommendation marker). Check logic. Output:\n{cleaned_output}")
        # Optionally return original or fallback result here? For now, return potentially broken output.

    logger.debug(f"Structure-based cleaned LLM output:\n---\n{cleaned_output}\n---")
    return cleaned_output

# Helper function for fallback cleaning (previous regex method)
# This is kept in case the strict structure cleaning fails unexpectedly
def _clean_with_regex_fallback(raw_output: str) -> str:
    """Fallback cleaning using regex end markers."""
    logger.warning("Executing regex-based fallback cleaning.")
    start_marker = prompts.REVIEW_SECTION_SUMMARY
    start_index = raw_output.find(start_marker)
    if start_index == -1: return raw_output.strip()

    review_text = raw_output[start_index:]
    end_markers = [ # Keep the list from previous attempts
         r'<\/?think>', r'alright, let me', r'okay, so I need', r'okay, so I\'ve got',
         r'here\'s my thought process', r'\bstep-by-step\b', r'thinking process:',
         r'internal thoughts:', r'my reasoning:', r'please note that',
         r'--- END REVIEW ---', r'^\s*## ' + re.escape(prompts.REVIEW_SECTION_SUMMARY.strip('# ')),
         r'^\s*Note:', r'^\s*Summary:',
    ]
    end_pattern = re.compile(r'(' + '|'.join(end_markers) + r')', re.IGNORECASE | re.MULTILINE)
    search_start_pos = len(start_marker)
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
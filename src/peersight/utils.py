import logging
import re
import os
from . import config
from . import prompts

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# For debugging cleaning: logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# --- File Reading ---
def read_text_file(file_path: str, encoding: str = None) -> str | None:
    # ... (keep existing read_text_file function) ...
    resolved_encoding = encoding if encoding else config.DEFAULT_ENCODING
    logging.info(f"Attempting to read file: {file_path} with encoding {resolved_encoding}")
    try:
        with open(file_path, 'r', encoding=resolved_encoding) as f:
            content = f.read()
        logging.info(f"Successfully read {len(content)} characters from {file_path}")
        return content
    except FileNotFoundError:
        logging.error(f"File Not Found Error: The file '{file_path}' was not found.")
        return None
    except IOError as e:
        logging.error(f"IO Error: An error occurred while reading the file '{file_path}'. Details: {e}")
        return None
    except UnicodeDecodeError as e:
         logging.error(f"Encoding Error: Failed to decode file '{file_path}' with encoding '{resolved_encoding}'. Try specifying a different encoding. Details: {e}")
         return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while reading file '{file_path}': {e}", exc_info=True)
        return None

# --- File Writing ---
def write_text_file(file_path: str, content: str, encoding: str = None) -> bool:
    resolved_encoding = encoding if encoding else config.DEFAULT_ENCODING
    logging.info(f"Attempting to write {len(content)} characters to file: {file_path} with encoding {resolved_encoding}")
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding=resolved_encoding) as f:
            f.write(content)
        logging.info(f"Successfully wrote content to {file_path}")
        return True
    except IOError as e:
        logging.error(f"IO Error: An error occurred while writing to the file '{file_path}'. Details: {e}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred while writing file '{file_path}': {e}", exc_info=True)
        return False

# --- LLM Output Cleaning ---
def clean_llm_output(raw_output: str) -> str:
    """
    Cleans the raw LLM output to extract only the structured review.
    Improved robustness with more end markers.
    """
    logging.debug(f"Raw LLM output received for cleaning:\n---\n{raw_output}\n---")

    # Define potential markers that indicate the end of the desired output
    # or the start of unwanted meta-commentary. Case-insensitive matching.
    # Expanded list based on observed outputs.
    # Using word boundaries (\b) where appropriate to avoid partial matches.
    end_markers = [
         r'<\/?think>', r'alright, let me', r'okay, so I need', r'okay, so I\'ve got',
         r'here\'s my thought process', r'\bstep-by-step\b', r'thinking process:',
         r'internal thoughts:', r'my reasoning:', r'please note that',
         r'--- END REVIEW ---', r'^\s*## ' + re.escape(prompts.REVIEW_SECTION_SUMMARY.strip('# ')), # Match repeated Summary header more precisely
         r'^\s*Note:', r'^\s*Summary:', # Less specific markers that might indicate deviation
    ]
    # Combine markers into a single regex pattern for searching
    # We want to find the *first* occurrence of any of these markers *after* the initial Summary.
    # Using MULTILINE and IGNORECASE flags.
    end_pattern = re.compile(r'(' + '|'.join(end_markers) + r')', re.IGNORECASE | re.MULTILINE)

    # 1. Find the start of the structured review
    start_marker = prompts.REVIEW_SECTION_SUMMARY
    start_index = raw_output.find(start_marker)

    if start_index == -1:
        logging.warning(f"Could not find the start marker '{start_marker}' in LLM output. Returning raw output.")
        return raw_output.strip()

    # 2. Extract the text starting from the marker
    # We potentially include a bit before the marker if it helps context for end marker search? No, stick to starting exactly at the marker.
    review_text = raw_output[start_index:]
    logging.debug(f"Text after finding start marker:\n---\n{review_text}\n---")

    # 3. Find the *first* end marker *within* the extracted review_text
    # Start search *after* the initial start_marker text itself to avoid self-match if start marker is also an end marker (like ## Summary)
    search_start_pos = len(start_marker)
    match = end_pattern.search(review_text, pos=search_start_pos)

    cleaned_output = review_text # Default to the whole text if no end marker found

    if match:
        end_index = match.start()
        # Add a small check: if the found marker is very close to the start, it might be a false positive?
        # For now, trust the marker.
        logging.info(f"Found end marker '{match.group(0).strip()}' at index {end_index} relative to start marker. Truncating output.")
        cleaned_output = review_text[:end_index].strip()
    else:
        # If no end marker is found, assume the rest of the text is the valid review
        logging.info("No specific end marker found after start marker. Assuming remainder is the review.")
        cleaned_output = review_text.strip() # Already assigned, but strip just in case

    # Final sanity check: ensure it still starts correctly
    # Allow for potential leading whitespace removal by strip()
    if not cleaned_output.strip().startswith(start_marker):
         logging.warning(f"Cleaned output unexpectedly does not start with '{start_marker}'. Output:\n{cleaned_output}")
         # Fallback strategy: maybe return the original text from start_marker onwards?
         # return review_text.strip() # Option: return pre-truncation text
         # For now, return the potentially broken cleaned output for diagnosis.

    logging.debug(f"Cleaned LLM output:\n---\n{cleaned_output}\n---")
    return cleaned_output
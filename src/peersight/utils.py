import logging
import re # Import regular expressions module
from . import config
from . import prompts # Import prompts to access section headers

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_text_file(file_path: str, encoding: str = None) -> str | None:
    # ... (keep existing read_text_file function as is) ...
    """
    Reads the content of a text file.

    Args:
        file_path: The path to the text file.
        encoding: The file encoding to use (defaults to config.DEFAULT_ENCODING).

    Returns:
        The content of the file as a string, or None if an error occurs.
    """
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
         # Optionally, try other common encodings here if needed
         return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while reading file '{file_path}': {e}", exc_info=True)
        return None

def clean_llm_output(raw_output: str) -> str:
    """
    Cleans the raw LLM output to extract only the structured review.

    Attempts to find the start of the review (## Summary) and remove
    any preamble before it and any meta-commentary/thinking after it.

    Args:
        raw_output: The raw string response from the LLM.

    Returns:
        The cleaned string containing hopefully just the structured review,
        or the original string if cleaning fails.
    """
    logging.debug(f"Raw LLM output received for cleaning:\n---\n{raw_output}\n---")

    # Define potential markers that indicate the end of the desired output
    # or the start of unwanted meta-commentary. Case-insensitive matching.
    # Added common patterns observed.
    end_markers = [
         r'<\/?think>', r'alright, let me', r'here\'s my thought process',
         r'step-by-step', r'thinking process:', r'internal thoughts:',
         r'my reasoning:', r'^## summary' # Match repeated sections
    ]
    # Combine markers into a single regex pattern for searching
    # We want to find the *first* occurrence of any of these markers *after* the initial Summary.
    end_pattern = re.compile(r'(' + '|'.join(end_markers) + r')', re.IGNORECASE | re.MULTILINE)


    # 1. Find the start of the structured review (using the constant from prompts)
    start_marker = prompts.REVIEW_SECTION_SUMMARY
    start_index = raw_output.find(start_marker)

    if start_index == -1:
        logging.warning("Could not find the start marker '{start_marker}' in LLM output. Returning raw output.")
        return raw_output.strip() # Return stripped original if marker not found

    # 2. Extract the text starting from the marker
    review_text = raw_output[start_index:]
    logging.debug(f"Text after finding start marker:\n---\n{review_text}\n---")


    # 3. Find the *first* end marker *within* the extracted review_text
    match = end_pattern.search(review_text, pos=len(start_marker)) # Start search *after* the initial start_marker

    if match:
        end_index = match.start()
        logging.info(f"Found end marker '{match.group(0)}' at index {end_index}. Truncating output.")
        cleaned_output = review_text[:end_index].strip()
    else:
        # If no end marker is found, assume the rest of the text is the valid review
        logging.info("No specific end marker found after start marker. Assuming remainder is the review.")
        cleaned_output = review_text.strip()

    # Final sanity check: ensure it still starts correctly (should unless empty)
    if not cleaned_output.startswith(start_marker):
         logging.warning("Cleaned output unexpectedly does not start with '{start_marker}'. There might be an issue.")
         # Decide return strategy: return cleaned_output or original raw_output maybe?
         # For now, return the potentially broken cleaned output for diagnosis.

    logging.debug(f"Cleaned LLM output:\n---\n{cleaned_output}\n---")
    return cleaned_output
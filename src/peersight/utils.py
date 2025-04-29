import logging
import re
import os # Import os for path manipulation
from . import config
from . import prompts

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- File Reading ---
def read_text_file(file_path: str, encoding: str = None) -> str | None:
    # ... (keep existing read_text_file function) ...
    """
    Reads the content of a text file.
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
         return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while reading file '{file_path}': {e}", exc_info=True)
        return None

# --- File Writing ---
def write_text_file(file_path: str, content: str, encoding: str = None) -> bool:
    """
    Writes content to a text file. Creates directories if they don't exist.

    Args:
        file_path: The path to the text file to write.
        content: The string content to write.
        encoding: The file encoding to use (defaults to config.DEFAULT_ENCODING).

    Returns:
        True if writing was successful, False otherwise.
    """
    resolved_encoding = encoding if encoding else config.DEFAULT_ENCODING
    logging.info(f"Attempting to write {len(content)} characters to file: {file_path} with encoding {resolved_encoding}")
    try:
        # Ensure the directory exists
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
    # ... (keep existing clean_llm_output function) ...
    """
    Cleans the raw LLM output to extract only the structured review.
    """
    logging.debug(f"Raw LLM output received for cleaning:\n---\n{raw_output}\n---")
    start_marker = prompts.REVIEW_SECTION_SUMMARY
    end_markers = [
         r'<\/?think>', r'alright, let me', r'here\'s my thought process',
         r'step-by-step', r'thinking process:', r'internal thoughts:',
         r'my reasoning:', r'^## summary'
    ]
    end_pattern = re.compile(r'(' + '|'.join(end_markers) + r')', re.IGNORECASE | re.MULTILINE)
    start_index = raw_output.find(start_marker)
    if start_index == -1:
        logging.warning(f"Could not find the start marker '{start_marker}' in LLM output. Returning raw output.")
        return raw_output.strip()
    review_text = raw_output[start_index:]
    logging.debug(f"Text after finding start marker:\n---\n{review_text}\n---")
    match = end_pattern.search(review_text, pos=len(start_marker))
    if match:
        end_index = match.start()
        logging.info(f"Found end marker '{match.group(0)}' at index {end_index}. Truncating output.")
        cleaned_output = review_text[:end_index].strip()
    else:
        logging.info("No specific end marker found after start marker. Assuming remainder is the review.")
        cleaned_output = review_text.strip()
    if not cleaned_output.startswith(start_marker):
         logging.warning(f"Cleaned output unexpectedly does not start with '{start_marker}'.")
    logging.debug(f"Cleaned LLM output:\n---\n{cleaned_output}\n---")
    return cleaned_output
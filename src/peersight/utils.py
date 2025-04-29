import logging
from . import config # Import config for default encoding

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_text_file(file_path: str, encoding: str = None) -> str | None:
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
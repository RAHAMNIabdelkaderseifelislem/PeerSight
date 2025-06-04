import logging
import os
import re
import urllib.parse  # For URL encoding
import webbrowser  # Import webbrowser
from pathlib import Path
from typing import Optional  # Import Optional

from . import config, prompts

# Import pypdf
try:
    from pypdf import PdfReader

    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    PdfReader = None  # Placeholder

# Adjust logging level as needed for debugging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# --- File Reading ---
# --- File Reading (Unified) ---
def read_paper_file(file_path_str: str) -> Optional[str]:
    """
    Reads content from a text file or extracts text from a PDF file.

    Args:
        file_path_str: The path to the input file (.txt or .pdf).

    Returns:
        The content/extracted text as a string, or None if an error occurs.
    """
    file_path = Path(file_path_str)  # Convert to Path object for convenience
    file_extension = file_path.suffix.lower()

    if not file_path.is_file():
        logger.error(f"File Not Found Error: The file '{file_path_str}' was not found.")
        return None

    if file_extension == ".txt":
        return _read_text_file_content(str(file_path))
    elif file_extension == ".pdf":
        if not PYPDF_AVAILABLE:
            logger.error(
                "PDF processing requires the 'pypdf' library. Please install it: pip install pypdf"
            )
            return None
        return _read_pdf_file_content(str(file_path))
    else:
        logger.error(
            f"Unsupported file type: '{file_extension}'. Please provide a .txt or .pdf file."
        )
        return None


def _read_text_file_content(file_path: str, encoding: str = None) -> Optional[str]:
    """Reads the content of a text file (Helper)."""
    resolved_encoding = encoding if encoding else config.DEFAULT_ENCODING
    logger.info(
        f"Attempting to read text file: {file_path} with encoding {resolved_encoding}"
    )
    try:
        with open(file_path, "r", encoding=resolved_encoding) as f:
            content = f.read()
        logger.info(
            f"Successfully read {len(content)} characters from text file {file_path}"
        )
        return content
    except IOError as e:  # Catches FileNotFoundError, PermissionError, etc.
        logger.error(f"IO Error reading text file '{file_path}'. Details: {e}")
        return None
    except UnicodeDecodeError as e:
        logger.error(
            f"Encoding Error: Failed to decode text file '{file_path}' with encoding '{resolved_encoding}'. Details: {e}"
        )
        return None
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while reading text file '{file_path}': {e}",
            exc_info=True,
        )
        return None


def _read_pdf_file_content(file_path: str) -> Optional[str]:
    """Extracts text content from a PDF file (Helper)."""
    logger.info(f"Attempting to read PDF file: {file_path}")
    if not PYPDF_AVAILABLE or PdfReader is None:  # Double check
        logger.critical(
            "pypdf.PdfReader not available for PDF processing. This should not happen if PYPDF_AVAILABLE is True."
        )
        return None
    try:
        reader = PdfReader(file_path)
        text_parts = []
        for page_num, page in enumerate(reader.pages):
            try:
                text_parts.append(page.extract_text())
            except Exception as page_e:
                logger.warning(
                    f"Could not extract text from page {page_num + 1} of PDF '{file_path}'. Skipping. Error: {page_e}"
                )

        full_text = "\n".join(filter(None, text_parts))  # Join non-empty page texts
        if not full_text.strip():
            logger.warning(
                f"Extracted text from PDF '{file_path}' is empty or only whitespace."
            )
            # Return empty string instead of None, to distinguish from file read error
            return ""
        logger.info(
            f"Successfully extracted {len(full_text)} characters from PDF file {file_path}"
        )
        return full_text
    except Exception as e:
        logger.error(
            f"An error occurred while reading PDF file '{file_path}': {e}",
            exc_info=True,
        )
        return None


# --- File Writing ---
def write_text_file(file_path: str, content: str, encoding: str = None) -> bool:
    # ... (keep existing write_text_file function) ...
    resolved_encoding = encoding if encoding else config.DEFAULT_ENCODING
    logger.info(
        f"Attempting to write {len(content)} characters to file: {file_path} with encoding {resolved_encoding}"
    )
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding=resolved_encoding) as f:
            f.write(content)
        logger.info(f"Successfully wrote content to {file_path}")
        return True
    except IOError as e:
        logger.error(
            f"IO Error: An error occurred while writing to the file '{file_path}'. Details: {e}"
        )
        return False
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while writing file '{file_path}': {e}",
            exc_info=True,
        )
        return False


# --- LLM Output Cleaning ---
def clean_llm_output(raw_output: str) -> str:
    """
    Cleans the raw LLM output to extract the structured review.
    Finds start (## Summary), finds recommendation header, then finds
    the next boundary (e.g., ## header, <think>, etc.) to mark the end.
    """
    logger.debug(f"Raw LLM output received for cleaning:\n---\n{raw_output}\n---")

    start_marker = prompts.REVIEW_SECTION_SUMMARY
    start_index = raw_output.find(start_marker)
    if start_index == -1:
        logger.warning(
            f"Could not find the start marker '{start_marker}' in LLM output. Returning raw output."
        )
        return raw_output.strip()

    review_potential = raw_output[start_index:]
    logger.debug(
        f"Text potentially containing review (from start marker):\n---\n{review_potential}\n---"
    )

    recommendation_marker = prompts.REVIEW_SECTION_RECOMMENDATION
    recommendation_start_index_rel = review_potential.find(recommendation_marker)
    if recommendation_start_index_rel == -1:
        logger.warning(
            f"Could not find recommendation marker '{recommendation_marker}' after start marker. Using regex fallback on original text."
        )
        return _clean_with_regex_fallback(raw_output)

    # Define markers that indicate the END of the review content
    next_section_marker = r"^\s*## "
    # Add more general conversational markers observed
    meta_commentary_markers = [
        r"<\/?think>",
        r"alright, let me",
        r"okay, so I need",
        r"okay, so I\'ve got",
        r"^\s*Okay, so",  # Added this general pattern (start of line, optional space)
        r"here\'s my thought process",
        r"\bstep-by-step\b",
        r"thinking process:",
        r"internal thoughts:",
        r"my reasoning:",
        r"please note that",
        r"--- END REVIEW ---",
        r"^\s*Note:",
    ]
    search_start_pos = recommendation_start_index_rel + len(recommendation_marker)
    # Combine patterns. Search starts AFTER the recommendation header text ends.
    end_pattern = re.compile(
        r"(" + next_section_marker + "|" + "|".join(meta_commentary_markers) + r")",
        re.IGNORECASE | re.MULTILINE,
    )

    match = end_pattern.search(review_potential, pos=search_start_pos)
    end_index = len(review_potential)  # Default to end of string
    if match:
        end_index = match.start()
        logger.info(
            f"Found end boundary '{match.group(0).strip()}' after recommendation at index {end_index} relative to start marker. Truncating."
        )
    else:
        logger.info(
            "No end boundary found after recommendation marker. Assuming review ends here."
        )

    cleaned_output = review_potential[:end_index].strip()

    if not cleaned_output.startswith(start_marker):
        logger.warning(
            f"Cleaned output invalid: does not start with '{start_marker}'. Output:\n{cleaned_output}"
        )
    elif recommendation_marker not in cleaned_output:
        logger.warning(
            f"Cleaned output invalid: recommendation marker '{recommendation_marker}' missing. Output:\n{cleaned_output}"
        )

    logger.debug(
        f"Final cleaned LLM output:\n---\n{cleaned_output}\n---"
    )  # Changed log message slightly
    return cleaned_output


# Helper function for fallback cleaning (remains unchanged)
def _clean_with_regex_fallback(raw_output: str) -> str:
    """Fallback cleaning using regex end markers if primary structure fails."""
    logger.warning("Executing regex-based fallback cleaning.")
    start_marker = prompts.REVIEW_SECTION_SUMMARY
    start_index = raw_output.find(start_marker)
    if start_index == -1:
        return raw_output.strip()

    review_text = raw_output[start_index:]
    # Keep the original comprehensive list for fallback
    end_markers = [
        r"<\/?think>",
        r"alright, let me",
        r"okay, so I need",
        r"okay, so I\'ve got",
        r"here\'s my thought process",
        r"\bstep-by-step\b",
        r"thinking process:",
        r"internal thoughts:",
        r"my reasoning:",
        r"please note that",
        r"--- END REVIEW ---",
        r"^\s*## "
        + re.escape(
            prompts.REVIEW_SECTION_SUMMARY.strip("# ")
        ),  # Match repeated Summary
        r"^\s*Note:",
        r"^\s*Summary:",
    ]
    end_pattern = re.compile(
        r"(" + "|".join(end_markers) + r")", re.IGNORECASE | re.MULTILINE
    )
    search_start_pos = len(start_marker)  # Search after the initial Summary marker
    match = end_pattern.search(review_text, pos=search_start_pos)

    cleaned_output = review_text
    if match:
        end_index = match.start()
        logger.info(
            f"[Fallback] Found end marker '{match.group(0).strip()}' at index {end_index}. Truncating."
        )
        cleaned_output = review_text[:end_index].strip()
    else:
        logger.info(
            "[Fallback] No specific end marker found. Assuming remainder is the review."
        )
        cleaned_output = review_text.strip()

    if not cleaned_output.strip().startswith(start_marker):
        logger.warning(
            f"[Fallback] Cleaned output invalid: does not start with '{start_marker}'."
        )

    return cleaned_output


def open_search_for_paper(title: str, search_engine: str = "google_scholar") -> bool:
    """
    Opens a web browser to search for a paper title on a specified search engine.

    Args:
        title: The title of the paper to search for.
        search_engine: The search engine to use. Currently supports:
                       'google_scholar', 'pubmed', 'semantic_scholar', 'google'.

    Returns:
        True if the browser was successfully opened, False otherwise.
    """
    if not title:
        logger.warning("Cannot open search: No title provided.")
        return False

    query = urllib.parse.quote_plus(title)  # URL-encode the title

    base_urls = {
        "google_scholar": "https://scholar.google.com/scholar?q=",
        "pubmed": "https://pubmed.ncbi.nlm.nih.gov/?term=",
        "semantic_scholar": "https://www.semanticscholar.org/search?q=",
        "google": "https://www.google.com/search?q=",
        "arxiv": "https://arxiv.org/search/?query=",  # Added arXiv
    }

    if search_engine.lower() not in base_urls:
        logger.error(
            f"Unsupported search engine: {search_engine}. Supported: {list(base_urls.keys())}"
        )
        return False

    url = base_urls[search_engine.lower()] + query
    logger.info(f"Opening browser to search for '{title}' on {search_engine}: {url}")

    try:
        success = webbrowser.open_new_tab(url)
        if not success:
            logger.warning(
                f"webbrowser.open_new_tab may have failed for URL: {url}. Trying webbrowser.open."
            )
            success = webbrowser.open(url)  # Try fallback
        if not success:
            logger.error(f"Failed to open web browser for search. URL: {url}")
        return success
    except Exception as e:
        logger.error(f"Error opening web browser for search: {e}", exc_info=True)
        return False

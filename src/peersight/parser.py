import re
import logging
from typing import Dict, Optional, List

from . import prompts

logger = logging.getLogger(__name__)

def parse_review_text(review_text: str) -> Optional[Dict[str, str]]:
    """
    Parses the cleaned review text into a structured dictionary.
    Handles unexpected headers by associating content only up to the next known header.

    Args:
        review_text: The cleaned review text string.

    Returns:
        A dictionary with keys 'summary', 'strengths', 'weaknesses',
        and 'recommendation', or None if parsing fails.
    """
    logger.debug("Attempting to parse review text.")
    if not review_text or not review_text.strip():
        logger.error("Parsing failed: Input review text is empty or whitespace.")
        return None

    # Headers must be in the order they appear in the text
    known_headers_ordered = [
        prompts.REVIEW_SECTION_SUMMARY,
        prompts.REVIEW_SECTION_STRENGTHS,
        prompts.REVIEW_SECTION_WEAKNESSES,
        prompts.REVIEW_SECTION_RECOMMENDATION,
    ]
    known_headers_set = set(known_headers_ordered) # For quick lookup

    # Create a pattern that matches *any* '## Header' style line
    any_header_pattern = r"^\s*(##\s+.*)" # Capture the full header line

    # Split the text by *any* header
    # Parts will be ['', '## Header1', 'Content1', '## Header2', 'Content2', ...]
    # Or ['Content0', '## Header1', 'Content1', ...]
    try:
        parts = re.split(any_header_pattern, review_text, flags=re.MULTILINE)
        logger.debug(f"Regex split (any header) produced {len(parts)} parts.")
    except Exception as e:
         logger.error(f"Regex splitting (any header) failed during parsing: {e}", exc_info=True)
         return None

    parsed_data = {}
    # Initialize keys to ensure they exist even if section is empty/missing later
    for header in known_headers_ordered:
        key = _header_to_key(header) # Helper to get 'summary', 'strengths' etc.
        if key:
            parsed_data[key] = "" # Initialize with empty string

    current_known_header_key = None

    # Process parts: ['', 'Header', 'Content', 'Header', 'Content', ...]
    start_index = 0
    if parts and parts[0].strip() == "":
        start_index = 1 # Skip leading empty part if present

    for i in range(start_index, len(parts)):
        part = parts[i]
        is_header_line = re.match(any_header_pattern, part.strip()) is not None
        header_text = part.strip() if is_header_line else None

        if is_header_line and header_text in known_headers_set:
            # Found a known header, switch context
            current_known_header_key = _header_to_key(header_text)
            logger.debug(f"Switched context to known header: '{header_text}' (key: {current_known_header_key})")
        elif is_header_line:
            # Found an *unknown* header, clear current context so its content is ignored
            logger.warning(f"Ignoring unexpected header and its content: '{header_text}'")
            current_known_header_key = None # Ignore content until next known header
        elif current_known_header_key is not None:
            # This part is content belonging to the last known header
            # Append content (strip() removes leading/trailing whitespace between parts)
            parsed_data[current_known_header_key] += part.strip() + "\n" # Add newline back for multi-line content
            # Alternative: Append to a list and join later? Appending string is simpler for now.

    # Post-process: Trim final newline from each value and handle recommendation validation
    expected_keys = set(parsed_data.keys()) # All keys should be present due to initialization
    final_parsed_data = {}
    for key, content in parsed_data.items():
        trimmed_content = content.strip()
        if key == 'recommendation':
            # Validate recommendation
            recommendation = trimmed_content
            valid_recommendations = [opt.lower() for opt in prompts.REVIEW_RECOMMENDATION_OPTIONS]
            processed_recommendation = recommendation.lower().strip('.?! ')

            if processed_recommendation in valid_recommendations:
                final_parsed_data[key] = recommendation # Store original case
            else:
                logger.warning(f"Parsing warning: Invalid recommendation found: '{recommendation}'. Expected one of {prompts.REVIEW_RECOMMENDATION_OPTIONS}. Storing raw value.")
                final_parsed_data[key] = recommendation # Store raw
        else:
            final_parsed_data[key] = trimmed_content

    # Final check: ensure all expected sections were processed (check content is not empty if needed)
    # Check if essential sections like recommendation were actually populated
    if not final_parsed_data.get('recommendation'):
         logger.error("Parsing failed: Recommendation section content seems missing after processing.")
         return None
    # Add similar checks for other sections if they are strictly required to have content

    logger.info("Successfully parsed review text into structured dictionary (handling unexpected headers).")
    return final_parsed_data


def _header_to_key(header: str) -> Optional[str]:
    """Maps known header text to dictionary keys."""
    if header == prompts.REVIEW_SECTION_SUMMARY: return 'summary'
    if header == prompts.REVIEW_SECTION_STRENGTHS: return 'strengths'
    if header == prompts.REVIEW_SECTION_WEAKNESSES: return 'weaknesses'
    if header == prompts.REVIEW_SECTION_RECOMMENDATION: return 'recommendation'
    return None
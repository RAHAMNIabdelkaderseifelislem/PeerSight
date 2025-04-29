import re
import logging
from typing import Dict, Optional, List # Use typing for clarity

# Import constants from prompts needed for parsing
from . import prompts

logger = logging.getLogger(__name__)

def parse_review_text(review_text: str) -> Optional[Dict[str, str]]:
    """
    Parses the cleaned review text into a structured dictionary.

    Args:
        review_text: The cleaned review text string, expected to start
                     with REVIEW_SECTION_SUMMARY and contain all sections.

    Returns:
        A dictionary with keys 'summary', 'strengths', 'weaknesses',
        and 'recommendation', or None if parsing fails.
    """
    logger.debug("Attempting to parse review text.")
    if not review_text or not review_text.strip():
        logger.error("Parsing failed: Input review text is empty or whitespace.")
        return None

    # Define the headers to look for in order
    headers = [
        prompts.REVIEW_SECTION_SUMMARY,
        prompts.REVIEW_SECTION_STRENGTHS,
        prompts.REVIEW_SECTION_WEAKNESSES,
        prompts.REVIEW_SECTION_RECOMMENDATION,
    ]

    # Use regex to split the text by the headers
    # Pattern looks for '## HeaderName' at the start of a line (possibly indented)
    # Using positive lookahead (?=...) to keep the headers as delimiters
    # Need to escape markdown characters in headers for regex
    escaped_headers = [re.escape(h) for h in headers]
    # Pattern explanation: Match start of line (^), optional whitespace (\s*),
    # then one of the escaped headers. Wrap in () for capturing/splitting.
    # Need MULTILINE flag.
    pattern = r"^\s*(" + "|".join(escaped_headers) + r")"
    try:
        parts = re.split(pattern, review_text, flags=re.MULTILINE)
        logger.debug(f"Regex split produced {len(parts)} parts.")
    except Exception as e:
         logger.error(f"Regex splitting failed during parsing: {e}", exc_info=True)
         return None

    # Process the split parts
    # Expected structure after split: ['', '## Header1', 'Content1', '## Header2', 'Content2', ...]
    # Or possibly: ['Content0 (if text before first header)', '## Header1', 'Content1', ...]
    parsed_data = {}
    current_header = None

    # Adjust loop based on whether the first part is empty or content before first expected header
    start_index = 0
    if parts and parts[0].strip() == "" and len(parts) > 1 and parts[1] == headers[0]:
        # Typical case: Starts with '', then the first header
        start_index = 1
        logger.debug("First part is empty, starting processing from index 1.")
    elif parts and parts[0].strip() != "" and len(parts) > 1 and parts[1] == headers[0]:
         # Text before the first expected header - should not happen with cleaned text
         logger.warning("Found unexpected text before the first review header during parsing.")
         start_index = 1 # Skip the unexpected prefix
    elif parts and parts[0] == headers[0]:
        # Case where split might not leave leading empty string
        start_index = 0
        logger.debug("First part is the first header, starting processing from index 0.")
    else:
        logger.error(f"Parsing failed: Unexpected structure after regex split. First part: '{parts[0] if parts else 'N/A'}'")
        return None

    for i in range(start_index, len(parts), 2): # Step by 2: Header, Content
        header = parts[i]
        content = parts[i+1].strip() if (i+1) < len(parts) else ""

        logger.debug(f"Processing parsed part: Header='{header}', Content='{content[:50]}...'")

        if header == prompts.REVIEW_SECTION_SUMMARY:
            parsed_data['summary'] = content
        elif header == prompts.REVIEW_SECTION_STRENGTHS:
            parsed_data['strengths'] = content
        elif header == prompts.REVIEW_SECTION_WEAKNESSES:
            parsed_data['weaknesses'] = content
        elif header == prompts.REVIEW_SECTION_RECOMMENDATION:
            # Validate recommendation
            recommendation = content.strip()
            # Handle potential trailing punctuation or whitespace if LLM adds it
            # Be slightly lenient
            valid_recommendations = [opt.lower() for opt in prompts.REVIEW_RECOMMENDATION_OPTIONS]
            processed_recommendation = recommendation.lower().strip('.?! ')

            if processed_recommendation in valid_recommendations:
                 # Store the original (but stripped) version for consistency
                parsed_data['recommendation'] = recommendation
            else:
                logger.warning(f"Parsing warning: Invalid recommendation found: '{recommendation}'. Expected one of {prompts.REVIEW_RECOMMENDATION_OPTIONS}. Storing raw value.")
                # Store the raw value anyway, or return None? Let's store raw for now.
                parsed_data['recommendation'] = recommendation # Store raw
                # return None # Option: Fail parsing on invalid recommendation
        else:
             logger.warning(f"Encountered unexpected header during parsing: {header}")


    # Final check: ensure all expected keys are present
    expected_keys = {'summary', 'strengths', 'weaknesses', 'recommendation'}
    if not expected_keys.issubset(parsed_data.keys()):
        logger.error(f"Parsing failed: Missing expected sections. Found keys: {parsed_data.keys()}")
        return None

    logger.info("Successfully parsed review text into structured dictionary.")
    return parsed_data
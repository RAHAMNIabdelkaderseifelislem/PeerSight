import re
import logging
from typing import Dict, Optional, List

from . import prompts

logger = logging.getLogger(__name__)


def parse_review_text(review_text: str) -> Optional[Dict[str, str]]:
    """
    Parses the cleaned review text into a structured dictionary.
    Handles unexpected headers and validates required sections are present and non-empty.

    Args:
        review_text: The cleaned review text string.

    Returns:
        A dictionary with keys 'summary', 'strengths', 'weaknesses',
        and 'recommendation', or None if parsing fails required validation.
    """
    logger.debug("Attempting to parse review text.")
    if not review_text or not review_text.strip():
        logger.error("Parsing failed: Input review text is empty or whitespace.")
        return None

    known_headers_ordered = [
        prompts.REVIEW_SECTION_SUMMARY,
        prompts.REVIEW_SECTION_STRENGTHS,
        prompts.REVIEW_SECTION_WEAKNESSES,
        prompts.REVIEW_SECTION_RECOMMENDATION,
    ]
    known_headers_set = set(known_headers_ordered)

    any_header_pattern = r"^\s*(##\s+.*)"
    try:
        parts = re.split(any_header_pattern, review_text, flags=re.MULTILINE)
        logger.debug(f"Regex split (any header) produced {len(parts)} parts.")
    except Exception as e:
        logger.error(
            f"Regex splitting (any header) failed during parsing: {e}", exc_info=True
        )
        return None

    parsed_data = {}
    for header in known_headers_ordered:
        key = _header_to_key(header)
        if key:
            parsed_data[key] = ""

    current_known_header_key = None
    start_index = 0
    if parts and parts[0].strip() == "":
        start_index = 1

    for i in range(start_index, len(parts)):
        part = parts[i]
        # Corrected check: Need to strip before matching header pattern
        part_stripped = part.strip()
        is_header_line = (
            re.match(r"##\s+.*", part_stripped) is not None
        )  # Check stripped part
        header_text = part_stripped if is_header_line else None

        if is_header_line and header_text in known_headers_set:
            current_known_header_key = _header_to_key(header_text)
            logger.debug(
                f"Switched context to known header: '{header_text}' (key: {current_known_header_key})"
            )
        elif is_header_line:
            logger.warning(
                f"Ignoring unexpected header and its content: '{header_text}'"
            )
            current_known_header_key = None
        elif current_known_header_key is not None:
            # Check if part is not just whitespace before appending
            if part.strip():  # Only append if there's non-whitespace content
                parsed_data[current_known_header_key] += part.strip() + "\n"

    # Post-process and Validate
    final_parsed_data = {}
    required_keys = {"summary", "strengths", "weaknesses", "recommendation"}
    validation_passed = True

    for key in required_keys:
        content = parsed_data.get(
            key, ""
        ).strip()  # Get content, default to "", strip whitespace
        if not content:  # Check if content is empty after stripping
            logger.error(
                f"Parsing validation failed: Required section '{key}' is missing or empty."
            )
            validation_passed = False
            # No need to continue processing this key if empty
            continue

        if key == "recommendation":
            # Validate recommendation format/value
            recommendation = content
            valid_recommendations = [
                opt.lower() for opt in prompts.REVIEW_RECOMMENDATION_OPTIONS
            ]
            processed_recommendation = recommendation.lower().strip(".?! ")

            if processed_recommendation in valid_recommendations:
                final_parsed_data[key] = recommendation  # Store original case
            else:
                logger.warning(
                    f"Parsing warning: Invalid recommendation found: '{recommendation}'. Storing raw value."
                )
                final_parsed_data[key] = (
                    recommendation  # Store raw (still counts as present)
                )
                # If strict validation is needed:
                # logger.error(f"Parsing validation failed: Invalid recommendation '{recommendation}'.")
                # validation_passed = False
        else:
            final_parsed_data[key] = content  # Store the non-empty, stripped content

    # Return None if any required section was missing/empty
    if not validation_passed:
        return None

    logger.info("Successfully parsed review text and validated required sections.")
    return final_parsed_data


def _header_to_key(header: str) -> Optional[str]:
    # ... (keep existing helper function) ...
    if header == prompts.REVIEW_SECTION_SUMMARY:
        return "summary"
    if header == prompts.REVIEW_SECTION_STRENGTHS:
        return "strengths"
    if header == prompts.REVIEW_SECTION_WEAKNESSES:
        return "weaknesses"
    if header == prompts.REVIEW_SECTION_RECOMMENDATION:
        return "recommendation"
    return None

import logging
import re
from typing import Dict, List, Optional

from . import prompts

logger = logging.getLogger(__name__)

# --- Helper Functions for Parsing ---


def _split_text_by_any_header(review_text: str) -> Optional[List[str]]:
    """Splits the review text by any '## Header' pattern."""
    any_header_pattern = r"^\s*(##\s+.*)"  # Capture the full header line
    try:
        # Split the text by *any* header
        # Parts will be ['', '## Header1', 'Content1', '## Header2', 'Content2', ...]
        # Or ['Content0', '## Header1', 'Content1', ...]
        parts = re.split(any_header_pattern, review_text, flags=re.MULTILINE)
        logger.debug(f"Regex split (any header) produced {len(parts)} parts.")
        return parts
    except Exception as e:
        logger.error(
            f"Regex splitting (any header) failed during parsing: {e}", exc_info=True
        )
        return None


def _extract_content_for_known_headers(
    parts: List[str], known_headers_set: set, known_headers_ordered: List[str]
) -> Dict[str, str]:
    """Iterates through split parts, extracting content for known headers."""
    parsed_data: Dict[str, str] = {}
    # Initialize keys
    for header in known_headers_ordered:
        key = _header_to_key(header)
        if key:
            parsed_data[key] = ""  # Assignment on new line

    current_known_header_key: Optional[str] = None
    start_index = 0
    if parts and parts[0].strip() == "":
        start_index = 1  # Skip leading empty part

    for i in range(start_index, len(parts)):
        part = parts[i]
        part_stripped = part.strip()
        # Check if it looks like a header (starts with ##)
        is_header_line = part_stripped.startswith("## ")
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
            current_known_header_key = None  # Ignore content until next known header
        elif current_known_header_key is not None and part_stripped:
            # Append non-whitespace content to the last known header's value
            parsed_data[current_known_header_key] += part_stripped + "\n"

    # Trim final newline added during accumulation
    for key in parsed_data:
        parsed_data[key] = parsed_data[key].strip()

    return parsed_data


def _validate_parsed_data(parsed_data: Dict[str, str]) -> bool:
    """Validates that required sections have content and recommendation is valid."""
    required_keys = {"summary", "strengths", "weaknesses", "recommendation"}
    validation_passed = True

    for key in required_keys:
        content = parsed_data.get(key, "")  # Already stripped in _extract_content
        if not content:
            logger.error(
                f"Parsing validation failed: Required section '{key}' is missing or empty."
            )
            validation_passed = False
            continue  # No point validating recommendation format if it's empty

        if key == "recommendation":
            recommendation = content
            valid_recommendations = [
                opt.lower() for opt in prompts.REVIEW_RECOMMENDATION_OPTIONS
            ]
            processed_recommendation = recommendation.lower().strip(".?! ")

            if processed_recommendation not in valid_recommendations:
                # Log warning but currently don't fail validation based on content
                logger.warning(
                    f"Parsing warning: Invalid recommendation content found: '{recommendation}'. "
                    f"Expected one of {prompts.REVIEW_RECOMMENDATION_OPTIONS}. Storing raw value."
                )
                # If strict validation is needed:
                # logger.error(f"Parsing validation failed: Invalid recommendation '{recommendation}'.")
                # validation_passed = False
    return validation_passed


def _header_to_key(header: str) -> Optional[str]:
    """Maps known header text to dictionary keys."""
    header_map = {
        prompts.REVIEW_SECTION_SUMMARY: "summary",
        prompts.REVIEW_SECTION_STRENGTHS: "strengths",
        prompts.REVIEW_SECTION_WEAKNESSES: "weaknesses",
        prompts.REVIEW_SECTION_RECOMMENDATION: "recommendation",
    }
    return header_map.get(header)


# --- Main Parsing Function ---


def parse_review_text(review_text: str) -> Optional[Dict[str, str]]:
    """
    Parses the cleaned review text into a structured dictionary.

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

    # Define known headers
    known_headers_ordered = [
        prompts.REVIEW_SECTION_SUMMARY,
        prompts.REVIEW_SECTION_STRENGTHS,
        prompts.REVIEW_SECTION_WEAKNESSES,
        prompts.REVIEW_SECTION_RECOMMENDATION,
    ]
    known_headers_set = set(known_headers_ordered)

    # 1. Split text by any header pattern
    parts = _split_text_by_any_header(review_text)
    if parts is None:
        return None  # Regex split failed

    # 2. Extract content associated with known headers
    parsed_data = _extract_content_for_known_headers(
        parts, known_headers_set, known_headers_ordered
    )

    # 3. Validate the extracted data (check for missing required sections)
    if not _validate_parsed_data(parsed_data):
        return None  # Validation failed

    logger.info("Successfully parsed review text into structured dictionary.")
    return parsed_data


def find_reference_section(paper_content: str) -> Optional[str]:
    """
    Attempts to find the 'References' or 'Bibliography' section of a paper.
    Returns the text of that section, or None if not found.
    """
    # Common headers for reference sections (case-insensitive)
    reference_headers = [
        "References",
        "Bibliography",
        "Literature Cited",
        "Works Cited",
    ]
    # Regex to find these headers at the start of a line, possibly with '##'
    pattern_str = r"^(?:\#\#\s*)?(" + "|".join(reference_headers) + r")\s*$"
    header_pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)

    match = header_pattern.search(paper_content)
    if not match:
        logger.warning("Could not find a standard reference section header.")
        return None

    # Get text after the found header
    reference_section_text = paper_content[match.end() :]
    logger.info(f"Found potential reference section starting with: '{match.group(1)}'")

    # Optional: Try to find the end of the reference section (e.g., start of Appendix, or just take N chars)
    # This is complex; for now, we might take a large chunk or until another major H2 header.
    # For simplicity in this step, let's assume the rest of the doc after "References" is mostly references.
    # A more robust method would be needed for real-world scenarios.
    return reference_section_text.strip()


def extract_references_from_text(reference_section_text: str) -> List[str]:
    """
    Extracts individual reference strings from the text of a reference section.
    This uses heuristics and may not be perfect.

    Args:
        reference_section_text: The string content of the reference section.

    Returns:
        A list of strings, where each string is a potential reference.
    """
    if not reference_section_text:
        return []

    references = []
    # Heuristic 1: Split by common numbering patterns like "[1]", "1.", "1)" at the start of a line
    # This pattern looks for optional [, then digits, then optional ], then . or ), then whitespace.
    # It tries to capture the text *after* this pattern up to the next such pattern or end of string.
    # Using a positive lookahead `(?=...)` to split *before* the next number.
    numbered_refs = re.split(
        r"^\s*(?:\[\d+\]|\d+\.|\d+\))\s+", reference_section_text, flags=re.MULTILINE
    )

    if len(numbered_refs) > 1:  # Indicates numbered list format was likely found
        logger.debug(f"Found {len(numbered_refs)-1} potential numbered references.")
        for ref_text in numbered_refs[1:]:  # Skip the part before the first number
            if ref_text.strip():
                references.append(ref_text.strip())
    else:
        # Heuristic 2: If no numbering, assume each non-empty line in the section is a reference.
        # This is very broad and works best if the reference section is clean.
        # Or, split by double newlines if references are paragraph-separated.
        potential_refs = (
            reference_section_text.splitlines()
        )  # Split by single newline first
        current_ref = ""
        for line in potential_refs:
            line_stripped = line.strip()
            if not line_stripped:  # Empty line might separate references
                if current_ref:
                    references.append(current_ref)
                    current_ref = ""
            else:
                # Heuristic for new reference: starts with likely author initial or year
                # e.g. "Smith, J.", "Adams B", "(2020)", "2020."
                # Or simply if the line is not clearly a continuation of the previous.
                # This is very tricky. For now, let's be simple:
                # If a line looks like it starts a new reference (e.g., not indented, or follows specific patterns)
                # For simplicity, let's assume for now that non-numbered lists are one per line or separated by blank lines.
                if current_ref and (
                    not line.startswith(" ") and not line.startswith("\t")
                ):  # Basic new line start
                    if current_ref:
                        references.append(current_ref)
                    current_ref = line_stripped
                else:
                    current_ref = (current_ref + " " + line_stripped).strip()

        if current_ref:  # Add the last accumulated reference
            references.append(current_ref)

        if not references:  # Fallback, treat each non-empty line as a ref
            logger.debug(
                "No clear numbered or block references, treating each non-empty line as a reference."
            )
            references = [
                line.strip()
                for line in reference_section_text.splitlines()
                if line.strip()
            ]

    # Basic cleaning of extracted references
    cleaned_references = []
    for ref in references:
        # Remove any "Retrieved from..." or "Available at..." common phrases if they are very long
        ref = re.sub(r"\s*\[Accessed:.*\]", "", ref, flags=re.IGNORECASE)
        ref = re.sub(r"\s*Retrieved from http.*", "", ref, flags=re.IGNORECASE)
        ref = re.sub(r"\s*Available at: http.*", "", ref, flags=re.IGNORECASE)
        ref = ref.strip()
        if len(ref) > 15:  # Arbitrary minimum length for a plausible reference
            cleaned_references.append(ref)

    logger.info(f"Extracted {len(cleaned_references)} potential reference strings.")
    logger.debug(f"First few extracted references (if any): {cleaned_references[:3]}")
    return cleaned_references

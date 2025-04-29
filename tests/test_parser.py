import sys
from pathlib import Path
import pytest

# Add src directory to sys.path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Import the module to test and dependencies
from peersight import parser
from peersight import prompts

# --- Test Data ---
VALID_SUMMARY = "This is the main summary text."
VALID_STRENGTHS = "- Strength A\n- Strength B is good."
VALID_WEAKNESSES = "- Weakness 1\n- Weakness 2 needs work."
VALID_RECOMMENDATION = "Accept"
VALID_RECOMMENDATION_LOWER = "minor revision" # Test case insensitivity

VALID_REVIEW_TEXT = f"""{prompts.REVIEW_SECTION_SUMMARY}
{VALID_SUMMARY}
{prompts.REVIEW_SECTION_STRENGTHS}
{VALID_STRENGTHS}
{prompts.REVIEW_SECTION_WEAKNESSES}
{VALID_WEAKNESSES}
{prompts.REVIEW_SECTION_RECOMMENDATION}
{VALID_RECOMMENDATION}"""

VALID_REVIEW_TEXT_LOWER_REC = f"""{prompts.REVIEW_SECTION_SUMMARY}
{VALID_SUMMARY}
{prompts.REVIEW_SECTION_STRENGTHS}
{VALID_STRENGTHS}
{prompts.REVIEW_SECTION_WEAKNESSES}
{VALID_WEAKNESSES}
{prompts.REVIEW_SECTION_RECOMMENDATION}
{VALID_RECOMMENDATION_LOWER}""" # Ends with lowercase rec

# --- Tests for parse_review_text ---

def test_parse_review_text_success_basic():
    """Test parsing a well-formed review text."""
    parsed = parser.parse_review_text(VALID_REVIEW_TEXT)
    assert parsed is not None
    assert parsed['summary'] == VALID_SUMMARY
    assert parsed['strengths'] == VALID_STRENGTHS
    assert parsed['weaknesses'] == VALID_WEAKNESSES
    assert parsed['recommendation'] == VALID_RECOMMENDATION

def test_parse_review_text_success_lowercase_recommendation():
    """Test parsing with a lowercase but valid recommendation."""
    parsed = parser.parse_review_text(VALID_REVIEW_TEXT_LOWER_REC)
    assert parsed is not None
    assert parsed['recommendation'] == VALID_RECOMMENDATION_LOWER # Should store original case

def test_parse_review_text_extra_whitespace():
    """Test parsing handles extra whitespace around sections."""
    text = f"""

    {prompts.REVIEW_SECTION_SUMMARY}

    {VALID_SUMMARY}


    {prompts.REVIEW_SECTION_STRENGTHS}

    {VALID_STRENGTHS}

    {prompts.REVIEW_SECTION_WEAKNESSES}
    {VALID_WEAKNESSES}


    {prompts.REVIEW_SECTION_RECOMMENDATION}

    {VALID_RECOMMENDATION}


    """
    parsed = parser.parse_review_text(text)
    assert parsed is not None
    assert parsed['summary'] == VALID_SUMMARY
    assert parsed['strengths'] == VALID_STRENGTHS
    assert parsed['weaknesses'] == VALID_WEAKNESSES
    assert parsed['recommendation'] == VALID_RECOMMENDATION

def test_parse_review_text_missing_strengths_section():
    """Test parsing fails if a middle section (Strengths) is missing."""
    text = f"""{prompts.REVIEW_SECTION_SUMMARY}
    {VALID_SUMMARY}
    {prompts.REVIEW_SECTION_WEAKNESSES}
    {VALID_WEAKNESSES}
    {prompts.REVIEW_SECTION_RECOMMENDATION}
    {VALID_RECOMMENDATION}"""
    parsed = parser.parse_review_text(text)
    # Expect failure because a required key will be missing
    assert parsed is None

def test_parse_review_text_missing_recommendation_section():
    """Test parsing fails if the recommendation section is missing."""
    text = f"""{prompts.REVIEW_SECTION_SUMMARY}
    {VALID_SUMMARY}
    {prompts.REVIEW_SECTION_STRENGTHS}
    {VALID_STRENGTHS}
    {prompts.REVIEW_SECTION_WEAKNESSES}
    {VALID_WEAKNESSES}"""
    parsed = parser.parse_review_text(text)
    assert parsed is None

def test_parse_review_text_invalid_recommendation():
    """Test parsing handles an invalid recommendation string (stores raw)."""
    invalid_rec = "Maybe Accept?"
    text = f"""{prompts.REVIEW_SECTION_SUMMARY}
    {VALID_SUMMARY}
    {prompts.REVIEW_SECTION_STRENGTHS}
    {VALID_STRENGTHS}
    {prompts.REVIEW_SECTION_WEAKNESSES}
    {VALID_WEAKNESSES}
    {prompts.REVIEW_SECTION_RECOMMENDATION}
    {invalid_rec}""" # Invalid recommendation
    parsed = parser.parse_review_text(text)
    # Currently, the parser logs a warning but still returns the dict with raw value
    assert parsed is not None
    assert parsed['recommendation'] == invalid_rec
    # If parser were stricter (return None on invalid rec), this assert would change to `is None`

def test_parse_review_text_empty_input():
    """Test parsing with empty string input."""
    parsed = parser.parse_review_text("")
    assert parsed is None

def test_parse_review_text_only_whitespace():
    """Test parsing with only whitespace input."""
    parsed = parser.parse_review_text("   \n \t ")
    assert parsed is None

def test_parse_review_text_missing_summary_header():
    """Test parsing fails if the initial summary header is missing."""
    text = f"""This is my summary.
    {prompts.REVIEW_SECTION_STRENGTHS}
    {VALID_STRENGTHS}
    {prompts.REVIEW_SECTION_WEAKNESSES}
    {VALID_WEAKNESSES}
    {prompts.REVIEW_SECTION_RECOMMENDATION}
    {VALID_RECOMMENDATION}"""
    parsed = parser.parse_review_text(text)
    assert parsed is None # Fails because regex split won't work as expected

def test_parse_review_text_unexpected_header():
    """Test parsing handles an unexpected header (it should be ignored)."""
    text = f"""{prompts.REVIEW_SECTION_SUMMARY}
    {VALID_SUMMARY}
    ## Some Other Header
    Some other content.
    {prompts.REVIEW_SECTION_STRENGTHS}
    {VALID_STRENGTHS}
    {prompts.REVIEW_SECTION_WEAKNESSES}
    {VALID_WEAKNESSES}
    {prompts.REVIEW_SECTION_RECOMMENDATION}
    {VALID_RECOMMENDATION}"""
    parsed = parser.parse_review_text(text)
    # The parser should still extract the known sections correctly
    assert parsed is not None
    assert parsed['summary'] == VALID_SUMMARY
    assert parsed['strengths'] == VALID_STRENGTHS
    assert parsed['weaknesses'] == VALID_WEAKNESSES
    assert parsed['recommendation'] == VALID_RECOMMENDATION
    # Check that the unexpected header wasn't included
    assert "some other header" not in parsed # Check keys
    assert "Some other content." not in parsed.values() # Check values
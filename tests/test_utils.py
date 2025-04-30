import sys
from pathlib import Path

import pytest

# Add src directory to sys.path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from peersight import (
    config,
    prompts,  # Import prompts for markers
    utils,
)


# --- Test Fixtures ---
@pytest.fixture(scope="function")
def temp_test_dir(tmp_path):
    """Creates a temporary directory for test files."""
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()
    return test_dir


# --- Tests for read_text_file ---
# ... (keep existing tests for read_text_file) ...
def test_read_text_file_success(temp_test_dir):
    file_path = temp_test_dir / "test_read.txt"
    expected_content = "This is a test file.\nWith multiple lines."
    with open(file_path, "w", encoding=config.DEFAULT_ENCODING) as f:
        f.write(expected_content)
    content = utils.read_text_file(str(file_path))
    assert content is not None and content == expected_content


def test_read_text_file_not_found(temp_test_dir):
    file_path = temp_test_dir / "non_existent.txt"
    content = utils.read_text_file(str(file_path))
    assert content is None


def test_read_text_file_different_encoding_success(temp_test_dir):
    file_path = temp_test_dir / "test_encoding.txt"
    expected_content = "Test content with accents: éàçü"
    test_encoding = "latin-1"
    with open(file_path, "w", encoding=test_encoding) as f:
        f.write(expected_content)
    content = utils.read_text_file(str(file_path), encoding=test_encoding)
    assert content is not None and content == expected_content


def test_read_text_file_wrong_encoding_fails(temp_test_dir):
    file_path = temp_test_dir / "test_wrong_encoding.txt"
    content_to_write = "你好世界"
    write_encoding = "utf-8"
    read_encoding = "ascii"
    with open(file_path, "w", encoding=write_encoding) as f:
        f.write(content_to_write)
    content = utils.read_text_file(str(file_path), encoding=read_encoding)
    assert content is None


# --- Tests for write_text_file ---
# ... (keep existing tests for write_text_file) ...
def test_write_text_file_success(temp_test_dir):
    file_path = temp_test_dir / "test_write.txt"
    content_to_write = "Content to be written.\nLine 2."
    success = utils.write_text_file(str(file_path), content_to_write)
    assert success is True
    assert file_path.exists()
    with open(file_path, "r", encoding=config.DEFAULT_ENCODING) as f:
        read_content = f.read()
    assert read_content == content_to_write


def test_write_text_file_creates_directory(temp_test_dir):
    nested_dir = temp_test_dir / "nested" / "dir"
    file_path = nested_dir / "test_nested_write.txt"
    content_to_write = "Testing nested directory creation."
    assert not nested_dir.exists()
    success = utils.write_text_file(str(file_path), content_to_write)
    assert success is True
    assert nested_dir.exists() and file_path.exists()
    with open(file_path, "r", encoding=config.DEFAULT_ENCODING) as f:
        read_content = f.read()
    assert read_content == content_to_write


# --- Tests for clean_llm_output ---

# Define the expected clean output structure for tests
EXPECTED_CLEAN_REVIEW = f"""{prompts.REVIEW_SECTION_SUMMARY}
This is the summary.
{prompts.REVIEW_SECTION_STRENGTHS}

Strength 1

Strength 2
{prompts.REVIEW_SECTION_WEAKNESSES}

Weakness 1
{prompts.REVIEW_SECTION_RECOMMENDATION}
Accept"""  # Note: No trailing newline in this definition


def test_clean_llm_output_already_clean():
    """Test cleaning output that is already in the correct format."""
    raw_output = EXPECTED_CLEAN_REVIEW + "\n"  # Add newline like LLM might
    cleaned = utils.clean_llm_output(raw_output)
    assert cleaned == EXPECTED_CLEAN_REVIEW


def test_clean_llm_output_with_preamble():
    """Test cleaning output with text before the first marker."""
    raw_output = f"""Here is the review you requested:
    Blah blah blah.
    {EXPECTED_CLEAN_REVIEW}
    """
    cleaned = utils.clean_llm_output(raw_output)
    assert cleaned == EXPECTED_CLEAN_REVIEW


def test_clean_llm_output_with_postamble_think():
    """Test cleaning output with <think> blocks after recommendation."""
    raw_output = f"""{EXPECTED_CLEAN_REVIEW}

    <think>
    Okay, planning complete. The user wants just the review.
    </think>
    Let me know if you need more help!"""
    cleaned = utils.clean_llm_output(raw_output)
    assert cleaned == EXPECTED_CLEAN_REVIEW


def test_clean_llm_output_with_postamble_prose():
    """Test cleaning output with general prose after recommendation."""
    raw_output = f"""{EXPECTED_CLEAN_REVIEW}
    Okay, so that's the review. I tried to follow the instructions.
    I hope this is helpful.
    Let me know!
    """
    cleaned = utils.clean_llm_output(raw_output)
    # Expect fallback might trigger here if structure cleaning fails due to prose marker
    # Depending on the exact fallback markers, this might or might not work perfectly.
    # Let's assert the ideal outcome based on the primary structure cleaning.
    assert cleaned == EXPECTED_CLEAN_REVIEW


def test_clean_llm_output_recommendation_at_end():
    """Test cleaning when recommendation is the absolute last text."""
    raw_output = EXPECTED_CLEAN_REVIEW  # No trailing newline or text
    cleaned = utils.clean_llm_output(raw_output)
    assert cleaned == EXPECTED_CLEAN_REVIEW


def test_clean_llm_output_missing_recommendation_marker():
    """Test cleaning when the recommendation marker is missing (should use fallback)."""
    raw_output = f"""{prompts.REVIEW_SECTION_SUMMARY}
    Summary text.
    {prompts.REVIEW_SECTION_STRENGTHS}

    Good stuff.
    {prompts.REVIEW_SECTION_WEAKNESSES}

    Bad stuff.

    Some Other Section Header
    Minor Revision"""  # Missing the standard Recommendation header
    # Expect the fallback (regex) cleaner to run. It might not clean perfectly
    # if no regex end markers are hit. It should at least start correctly.
    cleaned = utils.clean_llm_output(raw_output)
    # Check if it starts correctly (fallback might not truncate if no end markers match)
    assert cleaned.startswith(prompts.REVIEW_SECTION_SUMMARY)
    # We cannot easily assert the exact end point with the fallback,
    # but we can check it didn't return the original raw string if preamble existed.
    # For this specific input, fallback might return the whole thing. Let's just check start.


def test_clean_llm_output_missing_summary_marker():
    """Test cleaning when the initial summary marker is missing."""
    raw_output = """Here's the review:
    Strengths: blah
    Weaknesses: blah
    Recommendation: Accept"""  # Missing ## Summary
    cleaned = utils.clean_llm_output(raw_output)
    # Should return the raw output stripped, as the start anchor is missing
    assert cleaned == raw_output.strip()


def test_clean_llm_output_empty_input():
    """Test cleaning with empty string input."""
    raw_output = ""
    cleaned = utils.clean_llm_output(raw_output)
    assert cleaned == ""


def test_clean_llm_output_junk_input():
    """Test cleaning with input that doesn't match structure."""
    raw_output = "This is just some random text."
    cleaned = utils.clean_llm_output(raw_output)
    # Should return raw stripped as start marker is missing
    assert cleaned == raw_output

import sys
from pathlib import Path

# Add src directory to sys.path BEFORE importing peersight
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Now import from peersight
from peersight import prompts

# --- Tests for format_review_prompt ---


def test_format_review_prompt_basic():
    """Test basic formatting of the review prompt."""
    test_paper_content = "This is the paper text."
    formatted_prompt = prompts.format_review_prompt(test_paper_content)

    assert (
        f"--- START PAPER ---\n{test_paper_content}\n--- END PAPER ---"
        in formatted_prompt
    )
    assert prompts.REVIEW_SECTION_SUMMARY in formatted_prompt
    assert prompts.REVIEW_SECTION_STRENGTHS in formatted_prompt
    assert prompts.REVIEW_SECTION_WEAKNESSES in formatted_prompt
    assert prompts.REVIEW_SECTION_RECOMMENDATION in formatted_prompt
    options_str = ", ".join(f'"{opt}"' for opt in prompts.REVIEW_RECOMMENDATION_OPTIONS)
    assert options_str in formatted_prompt
    assert "CRITICAL:" in formatted_prompt
    assert "Do NOT include any preamble" in formatted_prompt
    # Correct the assertion to match the template text (MUST is uppercase)
    assert (
        "Your entire output MUST start directly with" in formatted_prompt
    )  # Changed must -> MUST
    assert formatted_prompt.endswith("\nReview Output:\n")


def test_format_review_prompt_empty_content():
    """Test prompt formatting with empty paper content."""
    test_paper_content = ""
    formatted_prompt = prompts.format_review_prompt(test_paper_content)

    assert (
        f"--- START PAPER ---\n{test_paper_content}\n--- END PAPER ---"
        in formatted_prompt
    )
    assert prompts.REVIEW_SECTION_SUMMARY in formatted_prompt
    assert prompts.REVIEW_SECTION_RECOMMENDATION in formatted_prompt
    assert formatted_prompt.endswith("\nReview Output:\n")

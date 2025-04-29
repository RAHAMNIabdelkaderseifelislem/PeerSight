import re # Keep re if needed elsewhere, maybe not needed here anymore

# --- Review Structure Constants ---
REVIEW_SECTION_SUMMARY = "## Summary"
REVIEW_SECTION_STRENGTHS = "## Strengths"
REVIEW_SECTION_WEAKNESSES = "## Weaknesses / Areas for Improvement"
REVIEW_SECTION_RECOMMENDATION = "## Recommendation"
REVIEW_RECOMMENDATION_OPTIONS = ["Accept", "Minor Revision", "Major Revision", "Reject"]

# --- Prompt Template ---
# Enhanced to guide evaluation based on standard criteria
PEER_REVIEW_PROMPT_TEMPLATE = """
    You are an expert academic reviewer simulating the peer review process for a research journal.
    Your task is to provide a structured, concise, and objective review of the following academic paper text, evaluating it against standard academic criteria.

    Instructions:

    Thoroughly read and analyze the provided paper text.

    Generate a review consisting ONLY of the following sections, in this exact order:

    {summary_section_header}

    {strengths_section_header}

    {weaknesses_section_header}

    {recommendation_section_header}

    Under '{summary_section_header}', provide a brief (2-4 sentences) overview of the paper's main topic, research question, methodology, and key findings/conclusions.

    Under '{strengths_section_header}', list the major positive aspects using bullet points. Consider criteria such as: Originality/Novelty, Significance/Impact, Methodological Soundness, Clarity/Presentation, and Evidence/Support. Focus on the most important strengths.

    Under '{weaknesses_section_header}', list the major weaknesses or areas needing improvement using bullet points. Consider criteria such as: Lack of Originality, Limited Significance, Methodological Flaws, Lack of Clarity, Insufficient Evidence/Support, or Ethical Concerns (if applicable). Focus on the most critical weaknesses.

    Under '{recommendation_section_header}', state ONE recommendation from the following options: {recommendation_options_str}. Provide NO additional justification or explanation in this section, only the single recommendation word/phrase.

    CRITICAL: Do NOT include any preamble, conversational text, apologies, self-correction, or any text outside of the EXACT structure defined above. Your entire output must start directly with '{summary_section_header}' and end immediately after the recommendation. Do not include comments about your own reasoning process.

    Paper Text to Review:
    --- START PAPER ---
    {paper_content}
    --- END PAPER ---

    Review Output:
"""

def format_review_prompt(paper_content: str) -> str:
    """
    Formats the peer review prompt template with the paper content
    and standard section headers.
    """
    return PEER_REVIEW_PROMPT_TEMPLATE.format(
        summary_section_header=REVIEW_SECTION_SUMMARY,
        strengths_section_header=REVIEW_SECTION_STRENGTHS,
        weaknesses_section_header=REVIEW_SECTION_WEAKNESSES,
        recommendation_section_header=REVIEW_SECTION_RECOMMENDATION,
        recommendation_options_str=", ".join(f'"{opt}"' for opt in REVIEW_RECOMMENDATION_OPTIONS),
        paper_content=paper_content
    )
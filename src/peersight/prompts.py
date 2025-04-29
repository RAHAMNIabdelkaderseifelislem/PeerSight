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

    Under '{strengths_section_header}', list the main strengths using bullet points (-). Start each bullet point clearly. Consider criteria such as: Originality/Novelty (e.g., "- The approach introduces a novel technique..."), Significance/Impact (e.g., "- The findings have significant implications for..."), Methodological Soundness (e.g., "- The methodology is robust and appropriate..."), Clarity/Presentation (e.g., "- The paper is clearly written and well-organized..."), and Evidence/Support (e.g., "- Claims are well-supported by the data...").

    Under '{weaknesses_section_header}', list the main weaknesses or areas for improvement using bullet points (-). Start each bullet point clearly. Consider criteria such as: Lack of Originality (e.g., "- The work largely replicates existing studies..."), Limited Significance (e.g., "- The contribution appears incremental..."), Methodological Flaws (e.g., "- The sample size is too small..."), Lack of Clarity (e.g., "- Key terms are not clearly defined..."), Insufficient Evidence/Support (e.g., "- Conclusions are not fully supported by the results..."), or Ethical Concerns.

    Under '{recommendation_section_header}', state ONE recommendation from the following options: {recommendation_options_str}. Provide NO additional justification or explanation in this section, only the single recommendation word/phrase.

    CRITICAL: Your entire output MUST start directly with '{summary_section_header}' and end immediately after the recommendation word/phrase. Do NOT include any preamble, conversation, apologies, self-correction, or any text beyond the structured review defined above (including no comments about your own reasoning process). Ensure each section header appears exactly as specified on its own line.

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
    # ... (formatting function remains the same) ...
    return PEER_REVIEW_PROMPT_TEMPLATE.format(
        summary_section_header=REVIEW_SECTION_SUMMARY,
        strengths_section_header=REVIEW_SECTION_STRENGTHS,
        weaknesses_section_header=REVIEW_SECTION_WEAKNESSES,
        recommendation_section_header=REVIEW_SECTION_RECOMMENDATION,
        recommendation_options_str=", ".join(f'"{opt}"' for opt in REVIEW_RECOMMENDATION_OPTIONS),
        paper_content=paper_content
    )
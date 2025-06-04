import textwrap  # Import textwrap
from typing import Optional

# --- Review Structure Constants ---
REVIEW_SECTION_SUMMARY = "## Summary"
REVIEW_SECTION_STRENGTHS = "## Strengths"
REVIEW_SECTION_WEAKNESSES = "## Weaknesses / Areas for Improvement"
REVIEW_SECTION_RECOMMENDATION = "## Recommendation"
REVIEW_RECOMMENDATION_OPTIONS = ["Accept", "Minor Revision", "Major Revision", "Reject"]

# --- Prompt Template ---
# Use textwrap.dedent to remove common leading whitespace
PEER_REVIEW_PROMPT_TEMPLATE = textwrap.dedent(
    """
    You are an expert academic reviewer simulating the peer review process for a research journal.
    Your task is to provide a structured, concise, and objective review of the following academic paper text, evaluating it against standard academic criteria.

    **Instructions:**
    1.  Thoroughly read and analyze the provided paper text.
    2.  Generate a review consisting ONLY of the following sections, in this exact order:
        - {summary_section_header}
        - {strengths_section_header}
        - {weaknesses_section_header}
        - {recommendation_section_header}
    3.  Under '{summary_section_header}', provide a brief (2-4 sentences) overview of the paper's main topic, research question, methodology, and key findings/conclusions.
    4.  Under '{strengths_section_header}', **list the main strengths using bullet points (`- `)**. Start each bullet point clearly. Consider criteria such as: Originality/Novelty (e.g., "- The approach introduces a novel technique..."), Significance/Impact (e.g., "- The findings have significant implications for..."), Methodological Soundness (e.g., "- The methodology is robust and appropriate..."), Clarity/Presentation (e.g., "- The paper is clearly written and well-organized..."), and Evidence/Support (e.g., "- Claims are well-supported by the data...").
    5.  Under '{weaknesses_section_header}', **list the main weaknesses or areas for improvement using bullet points (`- `)**. Start each bullet point clearly. Consider criteria such as: Lack of Originality (e.g., "- The work largely replicates existing studies..."), Limited Significance (e.g., "- The contribution appears incremental..."), Methodological Flaws (e.g., "- The sample size is too small..."), Lack of Clarity (e.g., "- Key terms are not clearly defined..."), Insufficient Evidence/Support (e.g., "- Conclusions are not fully supported by the results..."), or Ethical Concerns.
    6.  Under '{recommendation_section_header}', state ONE recommendation from the following options: {recommendation_options_str}. Provide NO additional justification or explanation in this section, only the single recommendation word/phrase.
    7.  **CRITICAL:** Your entire output MUST start directly with '{summary_section_header}' and end immediately after the recommendation word/phrase. Do NOT include any preamble, conversation, apologies, self-correction, or any text beyond the structured review defined above (including no comments about your own reasoning process). Ensure each section header appears exactly as specified on its own line.

    **Paper Text to Review:**
    --- START PAPER ---
    {paper_content}
    --- END PAPER ---

    Review Output:
    """
)  # Dedent automatically handles the closing """

# --- New Prompt for Specialty Determination ---
SPECIALTY_DETERMINATION_PROMPT_TEMPLATE = textwrap.dedent(
    """
    You are an expert academic editor tasked with classifying research papers.
    Based on the provided abstract and optional keywords, determine the primary academic specialty or sub-field of this paper.

    **Instructions:**
    1.  Analyze the abstract and keywords carefully.
    2.  Identify the most specific and relevant academic discipline and sub-discipline.
    3.  Provide ONLY the specialty name as your response.
    4.  Format: "Primary Field - Sub-Field" (e.g., "Computer Science - Artificial Intelligence", "Biology - Molecular Biology", "History - European Renaissance"). If a sub-field isn't clear, provide the primary field (e.g., "Philosophy").
    5.  Do NOT include any preamble, explanation, or conversational text. Your entire output must be the specialty string.

    **Paper Abstract:**
    {paper_abstract}

    **Keywords (if provided):**
    {paper_keywords}

    **Academic Specialty:**
    """
)  # Priming the LLM for the direct answer


def format_specialty_determination_prompt(
    paper_abstract: str, paper_keywords: Optional[str] = None
) -> str:
    """Formats the prompt for determining paper specialty."""
    keywords_text = paper_keywords if paper_keywords else "Not provided"
    return SPECIALTY_DETERMINATION_PROMPT_TEMPLATE.format(
        paper_abstract=paper_abstract, paper_keywords=keywords_text
    )


def format_review_prompt(paper_content: str) -> str:
    """
    Formats the peer review prompt template with the paper content
    and standard section headers.
    """
    # The template string is already dedented when defined
    return PEER_REVIEW_PROMPT_TEMPLATE.format(
        summary_section_header=REVIEW_SECTION_SUMMARY,
        strengths_section_header=REVIEW_SECTION_STRENGTHS,
        weaknesses_section_header=REVIEW_SECTION_WEAKNESSES,
        recommendation_section_header=REVIEW_SECTION_RECOMMENDATION,
        recommendation_options_str=", ".join(
            f'"{opt}"' for opt in REVIEW_RECOMMENDATION_OPTIONS
        ),
        paper_content=paper_content,
    )

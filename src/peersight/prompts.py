import textwrap  # Import textwrap
from typing import Optional

# --- Review Structure Constants ---
REVIEW_SECTION_SUMMARY = "## Summary"
REVIEW_SECTION_STRENGTHS = "## Strengths"
REVIEW_SECTION_WEAKNESSES = "## Weaknesses / Areas for Improvement"
REVIEW_SECTION_RECOMMENDATION = "## Recommendation"
REVIEW_RECOMMENDATION_OPTIONS = ["Accept", "Minor Revision", "Major Revision", "Reject"]

# --- Prompt Template ---

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


STRICT_PEER_REVIEW_PROMPT_TEMPLATE = textwrap.dedent(
    """
You are an expert academic journal reviewer tasked with providing a rigorous, structured, and impartial peer review.
The paper is in the field of: **{paper_specialty}**. While you should provide a general academic review, keep this specialty in mind if specific domain knowledge is relevant to assess claims or methodology (though your primary focus is general academic rigor unless specific instructions for the specialty are given later).

**CRITICAL INSTRUCTIONS FOR OUTPUT FORMATTING:**
1.  Your ENTIRE response MUST begin *exactly* with "## Summary" and end *exactly* after the single-word/phrase recommendation.
2.  Do NOT include ANY preamble, apologies, self-correction, conversational text, or any text outside the defined section structure.
3.  Each section header (e.g., "## Summary") MUST be on its own line, followed by its content.
4.  Use Markdown for bullet points (`- `) within Strengths and Weaknesses.

**REVIEW STRUCTURE & GUIDELINES:**

{summary_section_header}
Provide a concise (3-5 sentences) summary covering:
- The paper's primary research question or objective(s).
- The core methodology employed.
- The most significant findings and conclusions.
- The purported contribution to the field of {paper_specialty}.

{strengths_section_header}
Identify and articulate the paper's most significant strengths using bullet points. For each strength, briefly explain *why* it is a strength. Consider:
- **Originality & Novelty:** (e.g., "- The work presents a novel approach to [problem] by [method/idea], which has not been explored previously.")
- **Significance & Impact:** (e.g., "- The findings offer substantial insights into [area], potentially influencing future research in {paper_specialty}.")
- **Methodological Rigor:** (e.g., "- The research design is sound and appropriate for addressing the research question; data collection and analysis methods are robust and well-executed.")
- **Clarity & Presentation:** (e.g., "- The paper is exceptionally well-written and logically structured, making complex ideas accessible.")
- **Evidence & Argumentation:** (e.g., "- Claims are consistently well-supported by strong empirical evidence and logical reasoning.")

{weaknesses_section_header}
Identify and articulate the paper's most critical weaknesses or areas requiring improvement using bullet points. For each weakness, explain *why* it is a concern and, if possible, suggest specific ways it could be addressed. Consider:
- **Originality & Novelty:** (e.g., "- The contribution appears incremental, building only marginally on existing work in {paper_specialty} without offering significant new perspectives.")
- **Significance & Impact:** (e.g., "- The practical or theoretical implications of the findings are unclear or not sufficiently demonstrated.")
- **Methodological Flaws:** (e.g., "- The study suffers from [specific flaw, e.g., small sample size, lack of control group, inappropriate statistical tests], which limits the validity of the conclusions.")
- **Clarity & Presentation:** (e.g., "- Certain sections are ambiguously worded or poorly organized, hindering reader comprehension (e.g., specify section/concept).")
- **Evidence & Argumentation:** (e.g., "- Conclusions are not adequately supported by the presented data/evidence, or alternative interpretations are not sufficiently addressed.")
- **Literature Review:** (e.g., "- The literature review overlooks key relevant studies in {paper_specialty} or fails to adequately contextualize the research.")
- **Ethical Concerns (if applicable):** (e.g., "- [Describe any ethical concerns regarding methodology, data, etc.]")

{recommendation_section_header}
State ONE of the following recommendations: {recommendation_options_str}.
(Provide NO other text in this section).

**Paper Text to Review:**
--- START PAPER ---
{paper_content}
--- END PAPER ---

Review Output:
"""
)


def format_strict_review_prompt(paper_content: str, paper_specialty: str) -> str:
    """Formats the strict peer review prompt template."""
    return STRICT_PEER_REVIEW_PROMPT_TEMPLATE.format(
        paper_specialty=(
            paper_specialty if paper_specialty else "General Academic"
        ),  # Ensure specialty is never None
        summary_section_header=REVIEW_SECTION_SUMMARY,
        strengths_section_header=REVIEW_SECTION_STRENGTHS,
        weaknesses_section_header=REVIEW_SECTION_WEAKNESSES,
        recommendation_section_header=REVIEW_SECTION_RECOMMENDATION,
        recommendation_options_str=", ".join(
            f'"{opt}"' for opt in REVIEW_RECOMMENDATION_OPTIONS
        ),
        paper_content=paper_content,
    )

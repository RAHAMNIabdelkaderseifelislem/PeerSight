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
    keywords_text = paper_keywords if paper_keywords else "Not provided"
    return SPECIALTY_DETERMINATION_PROMPT_TEMPLATE.format(
        paper_abstract=paper_abstract, paper_keywords=keywords_text
    )


STRICT_PEER_REVIEW_PROMPT_TEMPLATE = textwrap.dedent(
    """
You are an expert academic journal reviewer tasked with providing a rigorous, structured, and impartial peer review.
The paper's determined primary academic specialty is: **{paper_specialty}**.
Your review should critically assess the paper's general academic merit AND its suitability and contribution specifically within the context of **{paper_specialty}**.

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
- The purported contribution to the field of **{paper_specialty}**. Comment on whether the abstract accurately reflects this.

{strengths_section_header}
Identify and articulate the paper's most significant strengths using bullet points. For each strength, briefly explain *why* it is a strength. Consider its relevance to **{paper_specialty}**:
- **Originality & Novelty:** (e.g., "- The work presents a novel approach to [problem] by [method/idea] within {paper_specialty}, which has not been explored previously in this context.")
- **Significance & Impact:** (e.g., "- The findings offer substantial insights into [area], potentially influencing future research and practice within {paper_specialty}.")
- **Methodological Rigor:** (e.g., "- The research design is sound and appropriate for addressing the research question; methods are consistent with established practices in {paper_specialty} and are well-executed.")
- **Clarity & Presentation:** (e.g., "- The paper is exceptionally well-written and logically structured, making complex ideas accessible to an audience familiar with {paper_specialty}.")
- **Evidence & Argumentation:** (e.g., "- Claims are consistently well-supported by strong empirical evidence and logical reasoning, meeting the standards expected in {paper_specialty}.")

{weaknesses_section_header}
Identify and articulate the paper's most critical weaknesses or areas requiring improvement using bullet points. For each weakness, explain *why* it is a concern and, if possible, suggest specific ways it could be addressed. Consider its relevance to **{paper_specialty}**:
- **Scope & Fit for Specialty:** (e.g., "- The paper's scope may be too narrow/broad for a typical contribution to {paper_specialty}, or it may not clearly align with the central themes/debates in this field.")
- **Originality & Novelty:** (e.g., "- The contribution appears incremental, building only marginally on existing work in {paper_specialty} without offering significant new perspectives relevant to this field.")
- **Significance & Impact:** (e.g., "- The practical or theoretical implications of the findings for {paper_specialty} are unclear or not sufficiently demonstrated.")
- **Methodological Flaws:** (e.g., "- The study suffers from [specific flaw, e.g., inappropriate for {paper_specialty}], which limits the validity of the conclusions within this field.")
- **Clarity & Presentation:** (e.g., "- Certain sections use jargon that may not be standard in {paper_specialty} or are poorly organized, hindering comprehension.")
- **Evidence & Argumentation:** (e.g., "- Conclusions are not adequately supported by the presented data/evidence to meet the rigor expected in {paper_specialty}.")
- **Literature Review:** (e.g., "- The literature review overlooks key relevant studies specific to {paper_specialty} or fails to adequately contextualize the research within this field.")
- **Ethical Concerns (if applicable).**

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
    # Ensure paper_specialty has a fallback if somehow empty/None, though core.py should provide one
    specialty = (
        paper_specialty
        if paper_specialty and paper_specialty.strip()
        else "General Academic"
    )
    return STRICT_PEER_REVIEW_PROMPT_TEMPLATE.format(
        paper_specialty=specialty,
        summary_section_header=REVIEW_SECTION_SUMMARY,
        strengths_section_header=REVIEW_SECTION_STRENGTHS,
        weaknesses_section_header=REVIEW_SECTION_WEAKNESSES,
        recommendation_section_header=REVIEW_SECTION_RECOMMENDATION,
        recommendation_options_str=", ".join(
            f'"{opt}"' for opt in REVIEW_RECOMMENDATION_OPTIONS
        ),
        paper_content=paper_content,
    )

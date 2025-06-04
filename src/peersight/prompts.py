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
You are an expert academic journal reviewer providing a rigorous, structured, and impartial peer review.
The paper's determined primary academic specialty is: **{paper_specialty}**.
Your review should critically assess general academic merit AND suitability/contribution within **{paper_specialty}**.

**CRITICAL INSTRUCTIONS FOR OUTPUT FORMATTING:**
1.  ENTIRE response MUST begin *exactly* with "## Summary" and end *exactly* after the recommendation.
2.  NO preamble, apologies, self-correction, or conversational text outside the defined structure.
3.  Each main section header (e.g., "## Summary", "## Strengths") MUST be on its own line.
4.  Sub-criteria headers (e.g., "### Originality & Novelty") MUST also be on their own lines.
5.  Provide comments or bullet points (`- `) under each sub-criterion. If a sub-criterion is not applicable or no specific comment, state "N/A" or "No specific comments."

**REVIEW STRUCTURE & GUIDELINES:**

{summary_section_header}
(Concise 3-5 sentences: research question, methodology, key findings/conclusions, purported contribution to **{paper_specialty}**, abstract accuracy)

{strengths_section_header}
(For each sub-criterion below, provide specific comments or bullet points explaining *why* it's a strength, considering relevance to **{paper_specialty}**. If no specific strength, state "No specific strengths noted for this criterion.")

### Originality & Novelty
(e.g., "- The work presents a novel approach to [problem] by [method/idea] within {paper_specialty}...")

### Significance & Impact
(e.g., "- The findings offer substantial insights into [area], potentially influencing future research in {paper_specialty}...")

### Methodological Rigor
(e.g., "- The research design is sound; methods are consistent with practices in {paper_specialty} and well-executed...")

### Clarity & Presentation
(e.g., "- The paper is exceptionally well-written and logically structured, accessible to an audience familiar with {paper_specialty}...")

### Evidence & Argumentation
(e.g., "- Claims are consistently well-supported by strong evidence and logical reasoning, meeting standards in {paper_specialty}...")

{weaknesses_section_header}
(For each sub-criterion below, provide specific comments or bullet points explaining *why* it's a weakness and suggest improvements, considering relevance to **{paper_specialty}**. If no specific weakness, state "No specific weaknesses noted for this criterion.")

### Scope & Fit for Specialty
(e.g., "- The paper's scope may be too narrow/broad for {paper_specialty}, or not clearly aligned with its central themes...")

### Originality & Novelty
(e.g., "- The contribution appears incremental, marginally building on existing work in {paper_specialty}...")

### Significance & Impact
(e.g., "- Implications of findings for {paper_specialty} are unclear or not sufficiently demonstrated...")

### Methodological Flaws
(e.g., "- The study suffers from [specific flaw, e.g., inappropriate for {paper_specialty}], limiting conclusions...")

### Clarity & Presentation
(e.g., "- Certain sections use jargon not standard in {paper_specialty} or are poorly organized...")

### Evidence & Argumentation
(e.g., "- Conclusions are not adequately supported by presented data to meet rigor expected in {paper_specialty}...")

### Literature Review
(e.g., "- Overlooks key relevant studies specific to {paper_specialty} or fails to contextualize the research adequately...")

### Ethical Concerns (if applicable)
(State "N/A" if no concerns)

{recommendation_section_header}
(State ONE: {recommendation_options_str}. NO other text.)

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

import json
import logging
from typing import Dict, Optional, Tuple, Union  # For type hints

from . import agent, config, parser, utils

logger = logging.getLogger(__name__)


# Modify return type hint
# Add temperature parameter
def generate_review(
    paper_path: str,
    model_override: Optional[str] = None,
    api_url_override: Optional[str] = None,
    temperature_override: Optional[float] = None,
    top_k_override: Optional[int] = None,  # Add top_k
    top_p_override: Optional[float] = None,  # Add top_p
    perform_web_search: bool = False,  # New flag, default to False
    search_engine: str = "google_scholar",  # Default search engine
) -> Tuple[bool, Optional[Union[Dict, str]]]:
    """
    Orchestrates the academic paper review generation process.
    Accepts optional overrides for model, API URL, and temperature.
    """
    logger.info(f"Starting review generation for: {paper_path}")
    # ... (log model/URL overrides) ...
    if model_override:
        logger.debug(f"Using CLI model override: {model_override}")
    if api_url_override:
        logger.debug(f"Using CLI API URL override: {api_url_override}")
    # Log temp override if present
    if temperature_override is not None:
        logger.debug(f"Using CLI temperature override: {temperature_override}")
    if top_k_override is not None:
        logger.debug(f"Using CLI top_k override: {top_k_override}")
    if top_p_override is not None:
        logger.debug(f"Using CLI top_p override: {top_p_override}")

    # 1. Read Paper Content
    paper_content = utils.read_paper_file(paper_path)  # Changed this line
    paper_length = 0
    if paper_content is not None:
        paper_length = len(paper_content)
    else:
        logger.error(
            f"Failed to read paper content from '{paper_path}'. Aborting review."
        )
        return False, None  # Return failure, no data

    logger.info(f"Successfully loaded paper content ({paper_length} characters).")
    if paper_length > config.MAX_PAPER_LENGTH_WARN_THRESHOLD:
        # ... (warning log) ...
        logger.warning(
            f"Input paper length ({paper_length} chars) exceeds threshold ({config.MAX_PAPER_LENGTH_WARN_THRESHOLD} chars). Processing may be slow or fail."
        )

    if perform_web_search:
        # Naive title extraction: first non-empty line (up to N chars)
        lines = paper_content.splitlines()
        potential_title = ""
        for line in lines:
            if line.strip():
                potential_title = line.strip()[:150]  # Limit title length for query
                break

        if potential_title:
            logger.info(
                f"Attempting web search for potential title: '{potential_title}' on {search_engine}"
            )
            utils.open_search_for_paper(potential_title, search_engine=search_engine)
            # Note: This opens the browser and continues. It doesn't wait or parse results yet.
        else:
            logger.warning(
                "Could not determine a title for web search from paper content."
            )

    # 2. Determine Paper Specialty using EditorAgent
    first_double_newline = paper_content.find("\n\n")
    paper_abstract_for_specialty = (
        paper_content[:first_double_newline].strip()
        if first_double_newline != -1 and first_double_newline < 1500
        else paper_content[:1000].strip()
    )
    logger.debug(
        f"Using pseudo-abstract for specialty: '{paper_abstract_for_specialty[:100]}...'"
    )

    editor_llm_temp = 0.3  # Low temp for classification
    editor_agent = agent.EditorAgent(
        model=model_override, api_url=api_url_override, temperature=editor_llm_temp
    )
    determined_specialty = editor_agent.determine_paper_specialty(
        paper_abstract_for_specialty
    )
    if not determined_specialty:  # If None or empty from agent after cleaning
        logger.warning(
            "Could not determine paper specialty via EditorAgent. Defaulting to 'General Academic'."
        )
        determined_specialty = "General Academic"
    logger.info(f"Paper specialty determined as: {determined_specialty}")

    # 3. Generate Review using ReviewerAgent
    logger.info("Instantiating ReviewerAgent...")
    reviewer_agent = agent.ReviewerAgent(
        model=model_override,
        api_url=api_url_override,
        temperature=temperature_override,  # Use main temp CLI/config override
        top_k=top_k_override,
        top_p=top_p_override,
    )
    # Call the ReviewerAgent's generate_review method
    raw_review_output = reviewer_agent.generate_review(
        paper_content, determined_specialty
    )

    if not raw_review_output:
        logger.error("ReviewerAgent failed to generate review output from LLM.")
        return False, None
    logger.info("Received raw response from LLM via ReviewerAgent.")

    # 4. Clean LLM Output (remains the same, operates on raw_review_output)
    cleaned_review_text = utils.clean_llm_output(raw_review_output)
    if not cleaned_review_text:
        logger.error("Review text is empty after cleaning process.")
        return False, None
    logger.info("Cleaned LLM review response successfully.")

    # 5. Parse Cleaned Text (remains the same)
    parsed_review = parser.parse_review_text(cleaned_review_text)
    if parsed_review is None:
        logger.error(
            "Failed to parse cleaned review text. Returning raw cleaned text instead."
        )
        return True, cleaned_review_text
    else:
        logger.info("Successfully parsed review into structured data.")
        logger.debug(f"Parsed Review Data:\n{json.dumps(parsed_review, indent=2)}")
        return True, parsed_review

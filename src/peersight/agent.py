import logging
from typing import Optional

from . import (
    llm_client,
    prompts,  # We might add new prompts here or in prompts.py
)

logger = logging.getLogger(__name__)


class EditorAgent:
    """
    Agent responsible for initial paper assessment, like determining specialty.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_url: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        self.model = model
        self.api_url = api_url
        self.temperature = temperature  # Store for LLM calls

    def determine_paper_specialty(
        self, paper_abstract: str, paper_keywords: Optional[str] = None
    ) -> Optional[str]:
        """
        Uses an LLM to determine the likely academic specialty of the paper.

        Args:
            paper_abstract: The abstract of the paper.
            paper_keywords: Optional keywords from the paper.

        Returns:
            A string representing the determined specialty (e.g., "Computer Science - Artificial Intelligence"),
            or None if determination fails.
        """
        if not paper_abstract:
            logger.error("Cannot determine specialty without paper abstract.")
            return None

        # We'll create this prompt in the next step
        prompt_text = prompts.format_specialty_determination_prompt(
            paper_abstract, paper_keywords
        )
        logger.info("Determining paper specialty using LLM...")
        logger.debug(
            f"Specialty determination prompt: {prompt_text[:500]}..."
        )  # Log snippet

        raw_response = llm_client.query_ollama(
            prompt=prompt_text,
            model=self.model,
            api_url=self.api_url,
            temperature=(
                self.temperature if self.temperature is not None else 0.3
            ),  # Use lower temp for classification
        )

        if not raw_response:
            logger.error("Failed to get response from LLM for specialty determination.")
            return None

        # For now, assume the LLM returns just the specialty string.
        # We'll need to parse/clean this later.
        # Example: "Computer Science - Artificial Intelligence"
        # Example: "Medicine - Oncology"
        # Example: "History - Ancient Rome"
        # Example: "Physics - Quantum Mechanics"
        determined_specialty = raw_response.strip()
        if not determined_specialty:
            logger.warning("LLM returned empty string for specialty.")
            return None

        logger.info(f"LLM suggested specialty: {determined_specialty}")
        return determined_specialty


# We will add ReviewerAgent class later

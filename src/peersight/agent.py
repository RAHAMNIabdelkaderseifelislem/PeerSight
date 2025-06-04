import logging
import re  # For more advanced cleaning if needed
from typing import Optional

from . import llm_client, prompts

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
        self.temperature = temperature

    def _clean_specialty_response(self, raw_response: str) -> str:
        """Cleans the LLM's raw response for the specialty."""
        # Remove leading/trailing whitespace
        cleaned = raw_response.strip()

        # Remove potential leading/trailing quotes (single or double)
        if (cleaned.startswith('"') and cleaned.endswith('"')) or (
            cleaned.startswith("'") and cleaned.endswith("'")
        ):
            cleaned = cleaned[1:-1]

        # Remove common LLM preamble/postamble if it slips through
        # (More robust cleaning could use regex for specific patterns)
        phrases_to_remove = [
            "The academic specialty is:",
            "Academic Specialty:",
            "Specialty:",
            "Primary Field - Sub-Field:",
            "Primary Field:",
            "The determined specialty is ",
            "I would classify this as ",
            "This paper falls under ",
        ]
        for phrase in phrases_to_remove:
            if cleaned.lower().startswith(phrase.lower()):
                cleaned = cleaned[len(phrase) :].strip()
            # Could also check endswith if needed

        # Basic format validation (optional, can be expanded)
        # Example: Check if it contains at least one word
        if not cleaned or not re.search(
            r"\w", cleaned
        ):  # Check for at least one word character
            logger.warning(
                f"Cleaned specialty string '{cleaned}' appears invalid (empty or no words)."
            )
            return "General Academic"  # Fallback if cleaning results in invalid string

        # Capitalize words for consistency (e.g., "computer science - artificial intelligence" -> "Computer Science - Artificial Intelligence")
        # Simple capitalization of first letter of each word, handles hyphens ok.
        parts = cleaned.split(" - ")
        capitalized_parts = []
        for part in parts:
            capitalized_parts.append(
                " ".join(word.capitalize() for word in part.split())
            )

        cleaned = " - ".join(capitalized_parts)

        return cleaned.strip()

    def determine_paper_specialty(
        self, paper_abstract: str, paper_keywords: Optional[str] = None
    ) -> Optional[str]:
        """
        Uses an LLM to determine the likely academic specialty of the paper.
        """
        if not paper_abstract:
            logger.error("Cannot determine specialty without paper abstract.")
            return None

        prompt_text = prompts.format_specialty_determination_prompt(
            paper_abstract, paper_keywords
        )
        logger.info("Determining paper specialty using LLM...")
        logger.debug(f"Specialty determination prompt: {prompt_text[:500]}...")

        raw_response = llm_client.query_ollama(
            prompt=prompt_text,
            model=self.model,
            api_url=self.api_url,
            temperature=self.temperature if self.temperature is not None else 0.3,
        )

        if not raw_response:
            logger.error("Failed to get response from LLM for specialty determination.")
            return None

        determined_specialty = self._clean_specialty_response(raw_response)

        if (
            not determined_specialty
            or determined_specialty.lower() == "general academic"
        ):  # Check if cleaning defaulted
            logger.warning(
                "LLM response for specialty was empty or invalid after cleaning. Using fallback."
            )
            return "General Academic"  # Return fallback if cleaning results in empty or default

        logger.info(f"Editor Agent determined specialty: {determined_specialty}")
        return determined_specialty


class ReviewerAgent:
    """
    Agent responsible for generating the detailed academic peer review.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_url: Optional[str] = None,
        temperature: Optional[float] = None,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None,
    ):
        self.model = model
        self.api_url = api_url
        self.temperature = temperature
        self.top_k = top_k
        self.top_p = top_p

    def generate_review(
        self, paper_content: str, paper_specialty: str
    ) -> Optional[str]:
        """
        Uses an LLM to generate a structured peer review.

        Args:
            paper_content: The full text content of the paper.
            paper_specialty: The determined specialty of the paper.

        Returns:
            A raw string containing the structured review from the LLM, or None on failure.
        """
        if not paper_content:
            logger.error("Cannot generate review without paper content.")
            return None

        # Use the new strict prompt template
        # We will modify format_strict_review_prompt later to actually use paper_specialty
        prompt_text = prompts.format_strict_review_prompt(
            paper_content, paper_specialty
        )
        logger.info(f"Generating review for paper in specialty: {paper_specialty}...")
        logger.debug(f"Strict review prompt (first 500 chars): {prompt_text[:500]}...")

        raw_response = llm_client.query_ollama(
            prompt=prompt_text,
            model=self.model,
            api_url=self.api_url,
            temperature=self.temperature,  # Use instance temperature
            top_k=self.top_k,
            top_p=self.top_p,
        )

        if not raw_response:
            logger.error("Failed to get response from LLM for review generation.")
            return None

        # Raw response is returned; cleaning is handled by the core logic for now
        return raw_response

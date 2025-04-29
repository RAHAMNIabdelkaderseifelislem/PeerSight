# src/peersight/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- Ollama Configuration ---
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-coder:latest")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")

# --- Application Settings ---
DEFAULT_ENCODING = "utf-8"
# Add a character length threshold for warning about long papers
# This is arbitrary; adjust based on typical LLM limits and performance.
# ~15k characters is roughly 3k-4k tokens, a reasonable point for a warning.
MAX_PAPER_LENGTH_WARN_THRESHOLD = int(os.getenv("MAX_PAPER_LENGTH_WARN_THRESHOLD", 15000))


# --- Remove Temporary Print ---
# print(f"Config loaded: OLLAMA_MODEL={OLLAMA_MODEL}, OLLAMA_API_URL={OLLAMA_API_URL}")
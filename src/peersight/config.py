import os

from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=dotenv_path)

# --- Ollama Configuration ---
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-8b:latest")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", 0.7))
# Add top_k and top_p defaults (Ollama defaults are often high/disabled)
# Use -1 or similar convention to indicate 'not set' / use Ollama's internal default
# Note: Ollama API expects integers for top_k, floats for top_p
OLLAMA_TOP_K = int(os.getenv("OLLAMA_TOP_K", -1))  # -1 indicates not set by us
OLLAMA_TOP_P = float(os.getenv("OLLAMA_TOP_P", -1.0))  # -1.0 indicates not set by us


# --- Application Settings ---
DEFAULT_ENCODING = "utf-8"
MAX_PAPER_LENGTH_WARN_THRESHOLD = int(
    os.getenv("MAX_PAPER_LENGTH_WARN_THRESHOLD", 15000)
)

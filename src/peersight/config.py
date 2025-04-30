import os
from dotenv import load_dotenv

# ... load_dotenv ...
dotenv_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=dotenv_path)


# --- Ollama Configuration ---
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-8b:latest")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
# Add default temperature (0.7 is often a reasonable balance)
# Can be overridden by .env or CLI
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", 0.7))

# --- Application Settings ---
DEFAULT_ENCODING = "utf-8"
MAX_PAPER_LENGTH_WARN_THRESHOLD = int(
    os.getenv("MAX_PAPER_LENGTH_WARN_THRESHOLD", 15000)
)

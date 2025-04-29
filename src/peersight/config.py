import os
from dotenv import load_dotenv

# Load environment variables from .env file
# find_dotenv() searches for the .env file in parent directories
# Useful if the script is run from a subdirectory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env') # Adjust path relative to config.py
load_dotenv(dotenv_path=dotenv_path) # More explicit path finding

# --- Ollama Configuration ---
# Get the model name from environment variable, with a fallback default
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-8b:latest")
# Default Ollama API endpoint (adjust if your Ollama runs elsewhere)
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")

# --- Application Settings ---
# You can add other configuration variables here as needed
DEFAULT_ENCODING = "utf-8"

# Example of how to potentially add more settings later
# MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
# TIMEOUT = int(os.getenv("TIMEOUT", 60))

print(f"Config loaded: OLLAMA_MODEL={OLLAMA_MODEL}, OLLAMA_API_URL={OLLAMA_API_URL}") # Temporary print for verification
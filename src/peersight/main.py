"""
PeerSight: AI Academic Paper Reviewer
"""
# Import the configuration settings
from . import config # Relative import within the package

def run():
    print("Initializing PeerSight...")
    # Access configuration variables via the config module
    print(f"Using Ollama model: {config.OLLAMA_MODEL}")
    print(f"Connecting to Ollama API at: {config.OLLAMA_API_URL}")
    # Add more application logic later...

if __name__ == "__main__":
    run()
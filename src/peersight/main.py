"""
PeerSight: AI Academic Paper Reviewer
"""
from . import config
from . import llm_client # Import the new client

def run():
    print(f"--- PeerSight Initializing ---")
    print(f"Using Ollama model: {config.OLLAMA_MODEL}")
    print(f"Connecting to Ollama API at: {config.OLLAMA_API_URL}")
    print("-" * 30)

    # --- Simple Test Query ---
    test_prompt = "Why is the sky blue?"
    print(f"Sending test prompt: '{test_prompt}'")

    response = llm_client.query_ollama(test_prompt)

    print("-" * 30)
    if response:
        print("Received response from Ollama:")
        print(response)
    else:
        print("Failed to get response from Ollama. Check logs for details.")
    print("-" * 30)
    print("--- PeerSight Initialization Complete ---")


if __name__ == "__main__":
    run()
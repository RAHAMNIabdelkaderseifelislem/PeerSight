# PeerSight - AI Academic Paper Reviewer

This project aims to create an AI agent capable of reviewing academic papers using local LLMs via Ollama.

## Features (Planned/Implemented)

*   Accepts plain text paper files.
*   Uses local Ollama LLM for review generation.
*   Provides structured review output (Summary, Strengths, Weaknesses, Recommendation).
*   Strips intermediate LLM thinking steps.
*   Command-line interface.
*   JSON output option.
*   Configurable model and API endpoint (via `.env` and CLI).

## Installation

Ensure you have Python >= 3.9 and pip installed.

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd PeerSight
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    # source venv/bin/activate
    ```
3.  **Install the package:**
    *   For regular use:
        ```bash
        pip install .
        ```
    *   For development (editable install):
        ```bash
        pip install -e .[test]
        ```
        (This installs dependencies including testing tools).

4.  **Set up `.env`:**
    Create a `.env` file in the project root (it's gitignored):
    ```dotenv
    # .env
    OLLAMA_MODEL="your-ollama-model-name:latest" # e.g., deepseek-coder:latest or llama3:latest
    # OLLAMA_API_URL="http://custom-host:11434/api/generate" # Optional override
    ```
5.  **Ensure Ollama is running** and serving the specified model.

## Basic Usage

After installation, you can run the tool using the `peersight` command:

```bash
# Basic review, print to console
peersight path/to/your/paper.txt

# Save review text to a file
peersight path/to/your/paper.txt -o output/review.md

# Get review in JSON format, print to console
peersight --json path/to/your/paper.txt

# Save review in JSON format to a file
peersight --json path/to/your/paper.txt -o output/review.json

# Use a different model for this run
peersight --model "another-model:latest" path/to/your/paper.txt

# Get help
peersight --help

# Check version
peersight --version
```

# PeerSight - AI Academic Paper Reviewer

**Version:** 0.1.0

PeerSight is an AI-powered command-line tool designed to automate and enhance the academic paper review process. It acts like a virtual journal reviewer, leveraging local Large Language Models (LLMs) via Ollama to provide structured peer reviews of research papers supplied as plain text files.

The goal is to simulate the *output* of an expert reviewer – clean, concise, and decision-oriented – without exposing the underlying step-by-step reasoning process of the LLM.

## ✨ Features

*   📄 Accepts academic papers as plain text files (`.txt`).
*   🧠 Uses a locally hosted LLM via **Ollama** for review generation.
*   ⚙️ Configurable LLM model, API endpoint, and generation parameters (temperature, top_k, top_p) via `.env` file and CLI flags.
*   📝 Generates structured reviews including:
    *   `## Summary`
    *   `## Strengths` (considering novelty, significance, methodology, clarity, evidence)
    *   `## Weaknesses / Areas for Improvement` (considering same criteria)
    *   `## Recommendation` (Accept, Minor Revision, Major Revision, Reject)
*   🧹 Post-processes LLM output to remove extraneous thinking steps or conversational filler.
*   💾 Outputs review in human-readable **Text** format (default) or machine-readable **JSON** format (`--json` flag).
*    M️ Warns if input paper exceeds a configurable length threshold (`MAX_PAPER_LENGTH_WARN_THRESHOLD`).
*   💻 Simple and clean Command-Line Interface (CLI).
*   📦 Installable Python package via `pip`.
*   ✅ Includes unit tests and code quality checks (`pytest`, `black`, `ruff`, `pre-commit`).

## ⚙️ Configuration

PeerSight uses a `.env` file in the project root directory for base configuration. Create this file if it doesn't exist (it's ignored by git).

**`.env` File Example:**

```dotenv
# --- REQUIRED ---
# Specify the Ollama model to use by default
# Make sure Ollama is serving this model!
OLLAMA_MODEL="llama3:latest" # Or deepseek-coder:latest, mistral:latest, etc.

# --- OPTIONAL ---
# Override the default Ollama API endpoint if needed
# OLLAMA_API_URL="http://custom-host:11434/api/generate"

# Override default generation parameters
# OLLAMA_TEMPERATURE=0.5  # Default: 0.7 (Lower = more deterministic)
# OLLAMA_TOP_K=40         # Default: -1 (disabled) (Consider only top K tokens)
# OLLAMA_TOP_P=0.9        # Default: -1.0 (disabled) (Consider tokens cumulative prob > P)

# Warning threshold for long papers (characters)
# MAX_PAPER_LENGTH_WARN_THRESHOLD=20000 # Default: 15000
```

**Command-Line Overrides:**

You can override the model, API URL, temperature, top-k, and top-p for a single run using CLI flags:

```bash
--model "model-name:tag"
# e.g., --model "llama3:8b"
# e.g., --model "deepseek-coder:latest"
```

```bash
--api-url "http://host:port/api/endpoint"
# e.g., --api-url "http://localhost:11434/api/generate"
```

```bash
-t TEMPERATURE or --temperature TEMPERATURE (e.g., -t 0.5)
# e.g., --temperature 0.3
# e.g., -t 0.7
```

```bash
--top-k K (e.g., --top-k 40)
# e.g., --top-k 20
# e.g., --top-k 0
```

```bash
--top-p P (e.g., --top-p 0.9)
# e.g., --top-p 0.95
```

CLI flags take precedence over .env settings.

## 🚀 Installation

Ensure you have Python >= 3.9 and pip installed. Ollama must also be installed and running separately (ollama.com).

- Clone the repository:
```bash
git clone https://github.com/RAHAMNIabdelkaderseifelislem/PeerSight
cd PeerSight
```

- Create and activate a virtual environment:

```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS/Linux
# source venv/bin/activate
```

- Install the package:

    - For regular use:

    ```bash
    pip install .
    ```

    - For development (includes testing and quality tools):

    ```bash
    pip install -e .[dev]
    ```

- Set up .env: Copy the example above into a .env file in the project root and set your desired OLLAMA_MODEL.

* (Crucial) Ensure Ollama is running and the model specified in your config (OLLAMA_MODEL) is downloaded and available (e.g., ollama run llama3).

## 🛠️ Usage

Once installed, use the peersight command.

Basic:

* Review paper, print Text output to console
```bash
peersight path/to/your/paper.txt
```

* Get help/see all options
```bash
peersight --help
```

* Check version
```bash
peersight --version
```

### Output Control:

* Save Text review to a file
```bash
peersight path/to/paper.txt -o output/review.md
```

* Output JSON to console
```bash
peersight --json path/to/paper.txt
```

* Save JSON review to a file
```bash
peersight --json path/to/paper.txt -o output/review.json
```

### LLM Control:

* Use a different model for this run
```bash
peersight --model "mistral:latest" path/to/paper.txt
```

* Adjust temperature for less randomness
```bash
peersight -t 0.3 path/to/paper.txt
```

* Use nucleus sampling
```bash
peersight --top-p 0.95 path/to/paper.txt
```

### Combine options
* Use a different model, save JSON output to a file, and set temperature
```bash
peersight --model "llama3:8b" -t 0.5 --json path/to/paper.txt -o reviews/paper1_llama3.json
```

### Verbose Logging:

* See DEBUG level logs (useful for troubleshooting)
```bash
peersight -v path/to/paper.txt
```

## 📝 Output Formats

* Text (Default): Human-readable Markdown-like text with standard headers (## Summary, etc.). Suitable for quick reading or pasting into documents.

* JSON (--json): Structured JSON object with keys summary, strengths, weaknesses, and recommendation. Useful for programmatic access or integration with other tools.
```json
{
    "summary": "The paper discusses...",
    "strengths": "- Strength 1...\n- Strength 2...",
    "weaknesses": "- Weakness 1...\n- Weakness 2...",
    "recommendation": "Minor Revision"
}
```

## ⚠️ Limitations

* **Input Length:** Very long papers may exceed the LLM's context window or Ollama's processing limits, potentially leading to poor results or errors (a warning is issued). Chunking is not yet implemented.

* **LLM Consistency:** The quality and adherence to instructions depend heavily on the specific LLM used (model, size) and its inherent variability. Results may differ between runs, especially with higher temperatures.

* **Factuality/Citation Check:** PeerSight does not verify the factual accuracy of the paper's claims or check citations. It simulates the review based on the provided text only.

* **Deep Understanding:** As an AI simulation, it lacks the deep domain expertise and nuanced understanding of a human expert in a specific field.

* **No Feedback Loop:** Does not currently support incorporating reviewer comments back into revisions.

## 🔧 Development

* Install dev dependencies:
```bash
pip install -e .[dev]
```

* Install pre-commit hooks:
```bash
python -m pre_commit install
```

* Run tests:
```bash
pytest
```

* Run linters/formatters:
```bash
ruff check --fix . and black .
```

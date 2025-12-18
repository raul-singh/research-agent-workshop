# Research Agent Workshop

This repository contains the necessary code for building a research agent that searches through a D&D 5e Systems Reference Document (SRD) knowledge base to answer questions.

## Project Structure

- **`agent/`** — Contains the code skeleton for you to implement during the workshop
- **`ready_implementation/`** — Contains the complete, fully-built implementation for reference
- **`knowledge_base/`** — Contains the D&D 5e SRD documents that the agent searches through
- **`main.py`** — Entry point to run the agent

## Prerequisites

This project uses **uv** as the Python package manager.

If you don't have uv installed, you can install it from:  
👉 https://docs.astral.sh/uv/getting-started/installation/

Quick install (macOS/Linux):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Getting Started

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd research-agent-workshop
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Set your OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```
   
   Or create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your-api-key
   ```

## Running the Code

To run any script, use `uv run`:

```bash
uv run main.py
```

You can also pass a query directly:

```bash
uv run main.py --query "What are the rules for grappling?"
```

Or use the short form:

```bash
uv run main.py -q "How does the Fireball spell work?"
```

## Workshop Instructions

1. Start by exploring the code in the `agent/` folder
2. Implement the missing functionality following the skeleton provided
3. If you get stuck, refer to the `ready_implementation/` folder for guidance
4. Test your implementation by running `uv run main.py` with different queries

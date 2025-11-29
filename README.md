# D&D 5e SRD Knowledge Base Agent

A D&D 5e rules assistant that searches the Systems Reference Document (SRD) to answer questions about rules, spells, monsters, items, classes, and more.

## Setup

1. Install dependencies:

```bash
uv sync
```

2. Set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key"
```

Or create a `.env` file in the project root:

```
OPENAI_API_KEY=your-api-key
```

## Usage

Run the agent with a question:

```bash
uv run python main.py --query "What are the rules for grappling?"
```

Or use the short form:

```bash
uv run python main.py -q "How does the Fireball spell work?"
```

You can also run it interactively (you'll be prompted for your question):

```bash
uv run python main.py
```


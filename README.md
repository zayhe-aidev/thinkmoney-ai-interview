# thinkmoney AI Customer Service — Senior AI Engineer Interview

A multi-agent customer service system built with [LangGraph](https://github.com/langchain-ai/langgraph). This exercise tests your ability to design and implement AI agent architectures.

## Quick Start

### Prerequisites

- [UV](https://docs.astral.sh/uv/) (Python package manager)
- One of the following LLM providers:
  - **Ollama** (local, free) — [install guide](https://ollama.ai)
  - **OpenAI** API key
  - **Anthropic** API key

### Setup

```bash
# Install dependencies
uv sync

# If using Ollama, pull the model first:
ollama pull gpt-oss:20b

# Run with your chosen provider:
uv run thinkmoney --provider ollama
uv run thinkmoney --provider openai --model gpt-4o-mini
uv run thinkmoney --provider anthropic --model claude-haiku-4-5-20251001
```

For OpenAI/Anthropic, set the API key as an environment variable:
```bash
export OPENAI_API_KEY="sk-..."
# or
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Provider Defaults

| Provider | Default Model | Notes |
|---|---|---|
| `ollama` | `gpt-oss:20b` | Must be running locally |
| `openai` | `gpt-4o-mini` | Requires `OPENAI_API_KEY` |
| `anthropic` | `claude-haiku-4-5-20251001` | Requires `ANTHROPIC_API_KEY` |

## Project Structure

```
├── src/
│   ├── main.py              # CLI entry point
│   ├── config.py             # LLM provider factory
│   ├── models.py             # State definitions, mock user data
│   ├── graph.py              # Agent graph definition
│   ├── agents/
│   │   ├── triage.py         # Triage agent (provided, reference impl)
│   │   └── README.md         # Pattern guide for building sub-agents
│   ├── knowledge_base/
│   │   ├── loader.py         # ChromaDB semantic search
│   │   └── data/             # Markdown knowledge base files
│   └── tools/
│       ├── __init__.py       # Tool groups (ACCOUNT_TOOLS, CARD_TOOLS, etc.)
│       ├── account.py        # Account management tools
│       ├── cards.py          # Card management tools
│       ├── transactions.py   # Transaction query tools
│       ├── payments.py       # Payment & transfer tools
│       └── kyc.py            # KYC/compliance tools
└── tests/
    └── test_tools.py         # Tool sanity tests
```

## Your Task

See **[TASK.md](TASK.md)** for full instructions.

## Running Tests

```bash
uv run pytest -v
```

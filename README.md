# thinkmoney AI Customer Service — Senior AI Engineer Interview

A multi-agent customer service system built with [LangGraph](https://github.com/langchain-ai/langgraph).

_Submission by Zainab Yusuf — AI Dev Solutions Ltd — April 2026_

---

## What was built

Starting from a working triage agent, this submission adds:

**7 specialist sub-agents** wired into the LangGraph StateGraph:
- `account_agent` — account details, balances, limits, contact info updates
- `card_agent` — freeze/unfreeze, replacements, card status
- `transaction_agent` — transaction history, details, dispute filing
- `payment_agent` — transfers to saved payees, exchange rates, standing orders
- `kyc_agent` — KYC verification status, document submission, account restrictions
- `conflict_resolver` — cross-domain fraud handling (freeze + dispute + investigation in one flow)
- `hitl_escalation` — human escalation for frustrated or complex cases

**3 new tools:**
- `detect_tone` — LLM-based classifier (provider-agnostic factory pattern); classifies customer messages as frustrated/neutral/satisfied with confidence score
- `flag_fraud_investigation` — opens a fraud case combining card and transaction data
- `escalate_to_human` — creates a human support ticket with reference and estimated wait

**Routing logic:**
- Triage can use `detect_tone` before specialist routing. If the customer appears frustrated, triage is instructed to escalate to `hitl_escalation` rather than a domain agent.
- Each sub-agent loops through its tool node until done, then hands back to triage.
- `conflict_resolver` handles cross-domain fraud scenarios that combine card and transaction actions in one flow.

Full design rationale, agent specifications, routing conditions, edge cases, and post-implementation hardening notes are documented separately in the assessment write-up.

---

## Quick Start

### Prerequisites

- Python >=3.12
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

### Try these conversations

```
"Freeze my card"                                    → card_agent
"There's a charge I don't recognise"                → transaction_agent
"I need to send £50 to James Wilson"                → payment_agent
"What's my account balance?"                        → account_agent
"Why is my account restricted?"                     → kyc_agent
"Someone has been using my card fraudulently"       → conflict_resolver
"I'm absolutely furious, nobody ever helps me"      → hitl_escalation
```

---

## Project Structure

```
├── src/
│   ├── main.py                    # CLI entry point
│   ├── config.py                  # LLM provider factory
│   ├── models.py                  # State definitions, mock user data
│   ├── graph.py                   # Agent graph — all nodes and edges
│   ├── agents/
│   │   ├── triage.py              # Triage agent (entry point, tone-aware routing)
│   │   ├── account.py             # Account specialist
│   │   ├── card.py                # Card specialist
│   │   ├── transaction.py         # Transaction specialist
│   │   ├── payment.py             # Payment specialist
│   │   ├── kyc.py                 # KYC specialist
│   │   ├── conflict_resolver.py   # Cross-domain fraud resolver
│   │   ├── hitl.py                # Human escalation agent
│   │   └── utils.py               # prepare_messages utility (tool_use sequencing)
│   ├── knowledge_base/
│   │   ├── loader.py              # ChromaDB semantic search
│   │   └── data/                  # Markdown knowledge base files
│   └── tools/
│       ├── __init__.py            # Tool groups (ACCOUNT_TOOLS, CARD_TOOLS, etc.)
│       ├── account.py             # Account management tools
│       ├── cards.py               # Card management tools
│       ├── transactions.py        # Transaction query tools
│       ├── payments.py            # Payment & transfer tools
│       ├── kyc.py                 # KYC/compliance tools
│       ├── sentiment.py           # detect_tone factory (provider-agnostic)
│       ├── fraud.py               # flag_fraud_investigation mock tool
│       └── escalation.py          # escalate_to_human mock tool
└── tests/
    ├── test_tools.py              # Tool sanity tests
    ├── test_triage.py             # Triage agent and routing tests
    └── ...                        # Additional graph and config tests
```

---

## Running Tests

```bash
uv run pytest -v
```

All 145 tests pass.

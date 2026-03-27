# Interview Task: Build Sub-Agents for thinkmoney Customer Service

**Time budget:** Up to 3 hours (take-home)

## Context

You are given a working customer service system for **thinkmoney**, an e-money provider. The system currently has:

- A **triage agent** that can answer general questions from a knowledge base, do a quick account lookup, and route to specialist sub-agents
- A **knowledge base** (ChromaDB-backed) with FAQs, policies, products, and fee information
- **22 mock tools** across 5 domains: accounts, cards, transactions, payments, and KYC/compliance
- A **CLI chat interface** that runs locally

The triage agent works — you can ask it general questions and it will search the knowledge base. It can also do a basic account lookup. But when a customer needs specific actions (freeze a card, dispute a transaction, make a transfer), there are no sub-agents to handle these requests yet.

The CLI shows real-time visibility into what's happening — you'll see which agents are active, which tools are called, and routing decisions as they happen. This extends automatically to any agents and tools you add.

## Setup & Running

See **[README.md](README.md)** for full setup instructions, including how to install dependencies and configure your LLM provider.

### LLM Provider Options

The system supports multiple LLM providers — use whichever you have access to:

| Provider | Command | What You Need |
|---|---|---|
| **Ollama** (local) | `uv run thinkmoney --provider ollama` | Ollama running locally with a model pulled |
| **OpenAI** | `uv run thinkmoney --provider openai` | `OPENAI_API_KEY` environment variable |
| **Anthropic** | `uv run thinkmoney --provider anthropic` | `ANTHROPIC_API_KEY` environment variable |

You can also override the default model with `--model <name>` (e.g. `--model gpt-4o`).

### A Note on Tests

The project includes **145 tests** covering all existing tools, the knowledge base, graph routing, CLI, and configuration. These are there for you to validate the existing code works — run `uv run pytest -v` to confirm everything is green before you start. **You do not need to write tests as part of this exercise.** Spend your time on building agents, not on test coverage.

## Your Task

**Build sub-agents that the triage agent routes to.**

This is deliberately open-ended. We want to see how you think, not just how you code.

### Core Requirement

- Create **at least one sub-agent** and wire it into the agent graph so the triage agent can route to it
- The sub-agent should use the provided mock tools to handle customer requests
- The routing should work end-to-end: customer asks → triage routes → sub-agent handles → response

### What We Want to See

- **Explore the codebase first.** Look at the tools available (`src/tools/`), understand the triage agent pattern (`src/agents/triage.py`), and read the graph structure (`src/graph.py`).
- **Think about what's possible.** You have 22 tools across 5 domains. What kind of customer experiences can you build? What would make this system actually useful?
- **Be creative.** The suggested domains (account, card, transaction, payment, KYC) are starting points, not constraints. Maybe you combine tools in interesting ways, add cross-domain capabilities, build an escalation flow, or design agents that collaborate.
- **Don't be afraid to experiment.** Try things. If something doesn't work, pivot. We value the thought process as much as the result.
- **Create your own tools if you want to.** The 22 provided tools are a starting point. If you think a new tool would unlock an interesting capability or improve the customer experience, go ahead and build it. Add it to `src/tools/` following the same `@tool` pattern — it's mock data, so keep it simple.

### Suggested Starting Points

These are ideas, not requirements. Pick what interests you or invent your own approach:

- An **account agent** that handles balance checks, limit inquiries, and contact updates
- A **card agent** that manages freezing/unfreezing, replacements, and status checks
- A **transaction agent** that helps customers review history and dispute charges
- A **payment agent** that assists with transfers, exchange rates, and standing orders
- A **compliance agent** that handles KYC status and document verification
- Something else entirely — a multi-domain agent, a supervisor pattern, an investigation flow for fraud, a proactive advisor...

### Where to Add Your Code

1. **Create your agent(s)** in `src/agents/` — study `triage.py` to understand the pattern
2. **Integrate them** in `src/graph.py` — study how the triage agent is wired to understand the registration, node, and edge patterns
3. Read `src/agents/README.md` for available tool groups and state access

### Helpful Commands

```bash
# Run the app (pick your provider)
uv run thinkmoney --provider ollama
uv run thinkmoney --provider openai
uv run thinkmoney --provider anthropic --model claude-sonnet-4-5-20241022

# Validate existing code
uv run pytest -v

# Try these conversations to play around with the initial agent:
# "What fees does thinkmoney charge?"
# "What account types do you offer?"
# "What currencies are supported?"
# "What's your complaints procedure?"
# "Tell me my account details for USR-2847"
```

## Tips

- The `state["user_info"]` dict has the mock customer's details — pass these to tools that need them.
- `src/tools/__init__.py` exports convenience groups you can bind to your agents.
- The knowledge base in `src/knowledge_base/data/` has real-ish content — your agents can reference it.
- Look at `tests/test_tools.py` to quickly understand what each tool returns.

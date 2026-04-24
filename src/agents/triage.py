"""Triage agent — the entry point for all customer conversations.

This agent answers general questions using the knowledge base and routes
specialist requests to sub-agents via the route_to_agent tool.
"""

from langchain_core.messages import SystemMessage
from langchain_core.tools import tool

from src.knowledge_base.loader import KnowledgeBase
from src.tools.account import get_account_details
from src.tools.sentiment import make_detect_tone_tool
from src.agents.utils import prepare_messages

# Initialise the knowledge base (loads/indexes on first use)
_kb = KnowledgeBase()


@tool
def search_knowledge_base(query: str) -> str:
    """Search the thinkmoney knowledge base for information about products, policies, fees, and FAQs.

    Use this tool to answer general questions about thinkmoney services,
    fees, policies, account types, and how things work.

    Args:
        query: A natural language search query.
    """
    return _kb.search(query)


@tool
def route_to_agent(agent_name: str, reason: str) -> str:
    """Route the conversation to a specialised sub-agent for handling.

    Use this when the customer needs a specific action performed on their
    account, cards, transactions, payments, or identity verification.
    Only route to agents that are listed as available in the system prompt.

    Args:
        agent_name: The sub-agent to route to. Must be one of the agents
                    listed as available in the system prompt.
        reason: Brief explanation of why this routing is needed.
    """
    return f"Routing to {agent_name} agent. Reason: {reason}"


# Tools exposed by the triage agent
TRIAGE_TOOLS = [search_knowledge_base, get_account_details, route_to_agent]


_TRIAGE_BASE_PROMPT = """You are thinkmoney's AI customer service triage agent. You are the first point of \
contact for all customer queries.

Your responsibilities:

1. **Answer general questions** about thinkmoney products, policies, fees, and procedures using the \
search_knowledge_base tool. Always search before answering factual questions.

2. **Quick account lookup** — You can use the get_account_details tool to look up the customer's basic \
account information (name, balance, account type, status). Use this for simple identity confirmation or \
quick balance checks. For detailed account work (updating limits, changing contact info, etc.), route to \
the account agent instead.

3. **Route to specialist agents** when the customer needs a specific action performed on their account. \
Use the route_to_agent tool with the appropriate agent name.

{available_agents_section}

Routing guidelines:
- Use detect_tone on the customer's latest message before routing to a specialist agent.
- If tone is frustrated with confidence >= 0.7, route to 'hitl' instead of the specialist agent.
- If the customer is asking a general "how does it work?" question → search the knowledge base
- If the customer wants to perform an action or look up their specific data → route to the appropriate agent if one is available
- If no specialist agent is available for the request, let the customer know that capability is not yet available and offer to help with what you can do
- If unclear, ask the customer a clarifying question rather than guessing
- Be friendly, professional, and concise

The customer's name is {user_name}. Address them by their first name.
"""

_NO_AGENTS_SECTION = """Currently, no specialist agents are available. You can only answer general questions \
using the knowledge base and perform basic account lookups. If a customer needs a specialist action \
(like freezing a card, disputing a transaction, or making a transfer), let them know that capability \
is not yet available and offer to help with what you can do."""

_AGENTS_HEADER = """Available specialist agents:
{agent_list}

Only route to agents listed above. Do not route to agents that are not listed."""


def _build_system_prompt(user_name: str, available_agents: dict[str, str] | None = None) -> str:
    """Build the triage system prompt with dynamic agent availability."""
    if available_agents:
        agent_lines = "\n".join(
            f'- "{name}" — {description}' for name, description in available_agents.items()
        )
        agents_section = _AGENTS_HEADER.format(agent_list=agent_lines)
    else:
        agents_section = _NO_AGENTS_SECTION

    return _TRIAGE_BASE_PROMPT.format(
        available_agents_section=agents_section,
        user_name=user_name,
    )


def create_triage_node(llm, available_agents: dict[str, str] | None = None):
    """Create the triage agent node function for use in a LangGraph StateGraph.

    This is the pattern to follow when creating sub-agents:
    1. Bind your tools to the LLM
    2. Define a node function that takes state and returns a state update
    3. Return the node function

    Args:
        llm: A LangChain chat model instance.
        available_agents: Optional dict mapping agent names to descriptions.
            Example: {"account": "Account details, balances, limits, contact updates"}
            When None or empty, triage will not attempt to route.

    Returns:
        A callable node function compatible with StateGraph.add_node().
    """
    detect_tone = make_detect_tone_tool(llm)
    all_tools = TRIAGE_TOOLS + [detect_tone]
    llm_with_tools = llm.bind_tools(all_tools)

    def triage_node(state):
        user_name = state.get("user_info", {}).get("name", "Customer")
        first_name = user_name.split()[0] if user_name else "Customer"

        system = SystemMessage(
            content=_build_system_prompt(first_name, available_agents)
        )
        messages = [system] + prepare_messages(state["messages"])
        response = llm_with_tools.invoke(messages)
        return {"messages": [response], "current_agent": "triage"}

    return triage_node

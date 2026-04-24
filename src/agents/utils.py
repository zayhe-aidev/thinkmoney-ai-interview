"""Shared utilities for sub-agent node functions."""

from langchain_core.messages import AIMessage, ToolMessage


def prepare_messages(messages: list) -> list:
    """Inject synthetic ToolMessages for any unresolved tool_use blocks.

    When triage routes via route_to_agent, the graph skips triage_tools so no
    tool_result is ever created. Anthropic's API requires every tool_use to have
    a corresponding tool_result. This injects one for any that are missing.
    """
    resolved = {
        msg.tool_call_id
        for msg in messages
        if isinstance(msg, ToolMessage) and hasattr(msg, "tool_call_id")
    }

    result = []
    for msg in messages:
        result.append(msg)
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc["id"] not in resolved:
                    result.append(ToolMessage(
                        content="Routed to specialist agent.",
                        tool_call_id=tc["id"],
                    ))
    return result

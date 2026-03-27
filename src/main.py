"""CLI entry point for the thinkmoney customer service agent."""

import argparse
import sys

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from rich.console import Console
from rich.panel import Panel

from src.config import get_llm
from src.graph import build_graph
from src.models import MOCK_USER


def _log_stream_event(console: Console, node_name: str, state_update: dict):
    """Print real-time visibility into graph execution.

    Logs agent activations, tool calls, and routing decisions as they happen.
    Works automatically for any agent or tool — including ones the candidate adds.
    """
    # Log agent/node activation
    if node_name.endswith("_tools"):
        pass  # Tool execution nodes are logged via tool calls on the agent message
    elif node_name not in ("__start__", "__end__"):
        console.print(f"  [dim]> Agent: {node_name}[/]")

    # Inspect messages in the state update for tool calls and routing
    messages = state_update.get("messages", [])
    if not isinstance(messages, list):
        return

    for msg in messages:
        # Log tool calls made by an agent
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                name = tc.get("name", "unknown")
                args = tc.get("args", {})

                # Special handling for route_to_agent
                if name == "route_to_agent":
                    target = args.get("agent_name", "?")
                    reason = args.get("reason", "")
                    console.print(
                        f"  [dim]> Routing: → {target} ({reason})[/]"
                    )
                else:
                    # Format tool args concisely
                    args_parts = []
                    for k, v in args.items():
                        val = str(v)
                        if len(val) > 40:
                            val = val[:37] + "..."
                        args_parts.append(f'{k}="{val}"')
                    args_str = ", ".join(args_parts)
                    console.print(f"  [dim]> Tool: {name}({args_str})[/]")

        # Log tool results (abbreviated)
        if isinstance(msg, ToolMessage):
            content = str(msg.content) if msg.content else ""
            if len(content) > 80:
                content = content[:77] + "..."
            console.print(f"  [dim]> Result: {content}[/]")


def main():
    parser = argparse.ArgumentParser(
        description="thinkmoney AI Customer Service Agent"
    )
    parser.add_argument(
        "--provider",
        required=True,
        choices=["ollama", "openai", "anthropic"],
        help="LLM provider to use",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name override (defaults: ollama=gpt-oss:20b, openai=gpt-4o-mini, anthropic=claude-haiku-4-5-20251001)",
    )
    args = parser.parse_args()

    console = Console()

    try:
        llm = get_llm(args.provider, args.model)
    except (ImportError, ValueError) as e:
        console.print(f"[bold red]Error:[/] {e}")
        sys.exit(1)

    graph = build_graph(llm)

    console.print(
        Panel.fit(
            "[bold]thinkmoney[/] AI Customer Service\n"
            f"Provider: [cyan]{args.provider}[/] | "
            f"Model: [cyan]{args.model or 'default'}[/]\n"
            f"Customer: [green]{MOCK_USER['name']}[/] ({MOCK_USER['user_id']})\n\n"
            "Type [bold]quit[/] to exit.",
            title="Welcome",
            border_style="blue",
        )
    )

    conversation_messages = []

    while True:
        try:
            user_input = console.input("\n[bold green]You:[/] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/]")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            console.print("[dim]Goodbye![/]")
            break

        conversation_messages.append(HumanMessage(content=user_input))

        # Stream graph execution for real-time visibility into agent activity.
        # stream_mode="values" yields the full accumulated state after each node,
        # so we can log events AND capture the final state in one pass.
        final_state = None
        # Start counting from current message length so we only log NEW messages
        prev_message_count = len(conversation_messages)

        with console.status("[bold blue]Thinking...", spinner="dots"):
            for state_snapshot in graph.stream(
                {
                    "messages": conversation_messages,
                    "user_info": MOCK_USER,
                    "current_agent": "triage",
                },
                stream_mode="values",
            ):
                # Determine which messages are new since last snapshot
                all_messages = state_snapshot.get("messages", [])
                new_messages = all_messages[prev_message_count:]
                prev_message_count = len(all_messages)

                current_agent = state_snapshot.get("current_agent", "")

                # Build a pseudo state_update for our logger
                if new_messages:
                    node_name = current_agent or "unknown"
                    # Detect if these are tool result messages (from a _tools node)
                    if new_messages and isinstance(new_messages[0], ToolMessage):
                        node_name = f"{current_agent}_tools"

                    _log_stream_event(console, node_name, {"messages": new_messages})

                final_state = state_snapshot

        if final_state:
            conversation_messages = final_state["messages"]

            # Find the last AI message with content to display
            for msg in reversed(final_state["messages"]):
                if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
                    console.print(f"\n[bold blue]thinkmoney:[/] {msg.content}")
                    break
            else:
                for msg in reversed(final_state["messages"]):
                    if isinstance(msg, AIMessage) and msg.content:
                        console.print(f"\n[bold blue]thinkmoney:[/] {msg.content}")
                        break


if __name__ == "__main__":
    main()

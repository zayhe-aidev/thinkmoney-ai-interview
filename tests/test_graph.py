"""Tests for the agent graph — compilation, routing, and structure."""

import pytest
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph import END

from src.graph import (
    build_graph,
    _make_route_target_fn,
    _handle_unavailable_agent,
    _route_from_subagent,
)
from src.models import AgentState


def _make_ai_message(tool_calls=None, content=""):
    """Helper to create an AIMessage with optional tool calls."""
    msg = AIMessage(content=content)
    if tool_calls:
        msg.tool_calls = tool_calls
    return msg


@pytest.fixture
def mock_llm():
    """A mock LLM that returns a simple AIMessage."""
    llm = MagicMock()
    llm.bind_tools = MagicMock(return_value=llm)
    llm.invoke = MagicMock(return_value=AIMessage(content="Hello!"))
    return llm


@pytest.fixture
def empty_route_fn():
    """Routing function with no agents registered."""
    return _make_route_target_fn({})


@pytest.fixture
def populated_route_fn():
    """Routing function with some agents registered."""
    return _make_route_target_fn({
        "account": "account_agent",
        "card": "card_agent",
    })


class TestGraphCompilation:
    def test_graph_compiles(self, mock_llm):
        graph = build_graph(mock_llm)
        assert graph is not None

    def test_graph_has_triage_node(self, mock_llm):
        graph = build_graph(mock_llm)
        node_names = list(graph.get_graph().nodes.keys())
        assert "triage" in node_names

    def test_graph_has_triage_tools_node(self, mock_llm):
        graph = build_graph(mock_llm)
        node_names = list(graph.get_graph().nodes.keys())
        assert "triage_tools" in node_names

    def test_graph_has_unavailable_agent_node(self, mock_llm):
        graph = build_graph(mock_llm)
        node_names = list(graph.get_graph().nodes.keys())
        assert "unavailable_agent" in node_names

    def test_graph_has_start_and_end(self, mock_llm):
        graph = build_graph(mock_llm)
        node_names = list(graph.get_graph().nodes.keys())
        assert "__start__" in node_names
        assert "__end__" in node_names


class TestGetRouteTarget:
    def test_no_tool_calls_returns_end(self, empty_route_fn):
        msg = AIMessage(content="Just a response")
        state: AgentState = {
            "messages": [msg],
            "current_agent": "triage",
            "user_info": {},
        }
        assert empty_route_fn(state) == END

    def test_empty_tool_calls_returns_end(self, empty_route_fn):
        msg = _make_ai_message(tool_calls=[])
        state: AgentState = {
            "messages": [msg],
            "current_agent": "triage",
            "user_info": {},
        }
        assert empty_route_fn(state) == END

    def test_kb_search_routes_to_triage_tools(self, empty_route_fn):
        msg = _make_ai_message(
            tool_calls=[{"name": "search_knowledge_base", "args": {"query": "fees"}, "id": "1"}]
        )
        state: AgentState = {
            "messages": [msg],
            "current_agent": "triage",
            "user_info": {},
        }
        assert empty_route_fn(state) == "triage_tools"

    def test_get_account_details_routes_to_triage_tools(self, empty_route_fn):
        msg = _make_ai_message(
            tool_calls=[{"name": "get_account_details", "args": {"user_id": "USR-2847"}, "id": "1"}]
        )
        state: AgentState = {
            "messages": [msg],
            "current_agent": "triage",
            "user_info": {},
        }
        assert empty_route_fn(state) == "triage_tools"

    def test_route_to_unknown_agent_goes_to_unavailable(self, empty_route_fn):
        msg = _make_ai_message(
            tool_calls=[{
                "name": "route_to_agent",
                "args": {"agent_name": "transaction", "reason": "view history"},
                "id": "1",
            }]
        )
        state: AgentState = {
            "messages": [msg],
            "current_agent": "triage",
            "user_info": {},
        }
        assert empty_route_fn(state) == "unavailable_agent"

    def test_route_to_registered_agent(self, populated_route_fn):
        msg = _make_ai_message(
            tool_calls=[{
                "name": "route_to_agent",
                "args": {"agent_name": "account", "reason": "balance check"},
                "id": "1",
            }]
        )
        state: AgentState = {
            "messages": [msg],
            "current_agent": "triage",
            "user_info": {},
        }
        assert populated_route_fn(state) == "account_agent"

    def test_route_to_second_registered_agent(self, populated_route_fn):
        msg = _make_ai_message(
            tool_calls=[{
                "name": "route_to_agent",
                "args": {"agent_name": "card", "reason": "freeze card"},
                "id": "1",
            }]
        )
        state: AgentState = {
            "messages": [msg],
            "current_agent": "triage",
            "user_info": {},
        }
        assert populated_route_fn(state) == "card_agent"

    def test_unregistered_agent_with_populated_map(self, populated_route_fn):
        msg = _make_ai_message(
            tool_calls=[{
                "name": "route_to_agent",
                "args": {"agent_name": "kyc", "reason": "verify docs"},
                "id": "1",
            }]
        )
        state: AgentState = {
            "messages": [msg],
            "current_agent": "triage",
            "user_info": {},
        }
        assert populated_route_fn(state) == "unavailable_agent"

    def test_message_without_tool_calls_attr(self, empty_route_fn):
        """Messages without tool_calls attribute should return END."""
        msg = HumanMessage(content="Hi")
        state: AgentState = {
            "messages": [msg],
            "current_agent": "triage",
            "user_info": {},
        }
        assert empty_route_fn(state) == END


class TestHandleUnavailableAgent:
    def test_returns_tool_message(self):
        msg = _make_ai_message(
            tool_calls=[{
                "name": "route_to_agent",
                "args": {"agent_name": "transaction", "reason": "view history"},
                "id": "call_123",
            }]
        )
        state: AgentState = {
            "messages": [msg],
            "current_agent": "triage",
            "user_info": {},
        }
        result = _handle_unavailable_agent(state)
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], ToolMessage)

    def test_tool_message_mentions_agent_name(self):
        msg = _make_ai_message(
            tool_calls=[{
                "name": "route_to_agent",
                "args": {"agent_name": "payment", "reason": "transfer"},
                "id": "call_456",
            }]
        )
        state: AgentState = {
            "messages": [msg],
            "current_agent": "triage",
            "user_info": {},
        }
        result = _handle_unavailable_agent(state)
        content = result["messages"][0].content
        assert "payment" in content
        assert "not available" in content

    def test_tool_message_has_correct_call_id(self):
        msg = _make_ai_message(
            tool_calls=[{
                "name": "route_to_agent",
                "args": {"agent_name": "kyc", "reason": "docs"},
                "id": "call_789",
            }]
        )
        state: AgentState = {
            "messages": [msg],
            "current_agent": "triage",
            "user_info": {},
        }
        result = _handle_unavailable_agent(state)
        assert result["messages"][0].tool_call_id == "call_789"


class TestRouteFromSubagent:
    def test_with_tool_calls_routes_to_tools(self):
        msg = _make_ai_message(
            tool_calls=[{"name": "get_account_details", "args": {"user_id": "USR-2847"}, "id": "1"}]
        )
        state: AgentState = {
            "messages": [msg],
            "current_agent": "account",
            "user_info": {},
        }
        assert _route_from_subagent(state) == "account_tools"

    def test_without_tool_calls_routes_to_triage(self):
        msg = AIMessage(content="Here is your balance.")
        state: AgentState = {
            "messages": [msg],
            "current_agent": "account",
            "user_info": {},
        }
        assert _route_from_subagent(state) == "triage"

    def test_empty_tool_calls_routes_to_triage(self):
        msg = _make_ai_message(tool_calls=[], content="Done.")
        state: AgentState = {
            "messages": [msg],
            "current_agent": "card",
            "user_info": {},
        }
        assert _route_from_subagent(state) == "triage"

    def test_uses_current_agent_for_tool_node_name(self):
        msg = _make_ai_message(
            tool_calls=[{"name": "freeze_card", "args": {"card_id": "CARD-5521"}, "id": "1"}]
        )
        state: AgentState = {
            "messages": [msg],
            "current_agent": "card",
            "user_info": {},
        }
        assert _route_from_subagent(state) == "card_tools"

    def test_defaults_to_triage_if_no_current_agent(self):
        msg = _make_ai_message(
            tool_calls=[{"name": "some_tool", "args": {}, "id": "1"}]
        )
        state: AgentState = {
            "messages": [msg],
            "current_agent": "",
            "user_info": {},
        }
        result = _route_from_subagent(state)
        assert "_tools" in result

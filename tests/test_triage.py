"""Tests for the triage agent — tools, prompts, and node creation."""

from unittest.mock import MagicMock

from langchain_core.messages import AIMessage

from src.agents.triage import (
    TRIAGE_TOOLS,
    _build_system_prompt,
    create_triage_node,
    search_knowledge_base,
    route_to_agent,
)
from src.tools.account import get_account_details


class TestTriageTools:
    def test_tools_list_has_three_tools(self):
        assert len(TRIAGE_TOOLS) == 3

    def test_search_knowledge_base_in_tools(self):
        tool_names = [t.name for t in TRIAGE_TOOLS]
        assert "search_knowledge_base" in tool_names

    def test_get_account_details_in_tools(self):
        tool_names = [t.name for t in TRIAGE_TOOLS]
        assert "get_account_details" in tool_names

    def test_route_to_agent_in_tools(self):
        tool_names = [t.name for t in TRIAGE_TOOLS]
        assert "route_to_agent" in tool_names


class TestSearchKnowledgeBase:
    def test_returns_string(self):
        result = search_knowledge_base.invoke({"query": "fees"})
        assert isinstance(result, str)

    def test_returns_content_for_fees(self):
        result = search_knowledge_base.invoke({"query": "ATM withdrawal fees"})
        assert len(result) > 0
        assert result != "No knowledge base content found."

    def test_returns_content_for_products(self):
        result = search_knowledge_base.invoke({"query": "Premium account features"})
        assert len(result) > 0


class TestRouteToAgent:
    def test_returns_routing_message(self):
        result = route_to_agent.invoke(
            {"agent_name": "account", "reason": "balance check"}
        )
        assert "account" in result
        assert "balance check" in result

    def test_includes_agent_name(self):
        result = route_to_agent.invoke(
            {"agent_name": "card", "reason": "freeze card"}
        )
        assert "card" in result

    def test_includes_reason(self):
        result = route_to_agent.invoke(
            {"agent_name": "kyc", "reason": "document verification needed"}
        )
        assert "document verification needed" in result


class TestBuildSystemPrompt:
    def test_with_no_agents_mentions_not_available(self):
        prompt = _build_system_prompt("Sarah", available_agents=None)
        assert "not yet available" in prompt
        assert "Sarah" in prompt

    def test_with_empty_agents_mentions_not_available(self):
        prompt = _build_system_prompt("Sarah", available_agents={})
        assert "not yet available" in prompt

    def test_with_agents_lists_them(self):
        agents = {
            "account": "Account details and balances",
            "card": "Card management",
        }
        prompt = _build_system_prompt("Sarah", available_agents=agents)
        assert '"account"' in prompt
        assert "Account details and balances" in prompt
        assert '"card"' in prompt
        assert "Card management" in prompt
        # Should have the agents header, not the "no agents" section
        assert "Only route to agents listed above" in prompt
        assert "no specialist agents are available" not in prompt

    def test_with_agents_includes_only_route_warning(self):
        agents = {"account": "Account stuff"}
        prompt = _build_system_prompt("Sarah", available_agents=agents)
        assert "Only route to agents listed above" in prompt

    def test_prompt_mentions_knowledge_base(self):
        prompt = _build_system_prompt("Sarah")
        assert "search_knowledge_base" in prompt

    def test_prompt_mentions_get_account_details(self):
        prompt = _build_system_prompt("Sarah")
        assert "get_account_details" in prompt

    def test_prompt_contains_user_name(self):
        prompt = _build_system_prompt("John")
        assert "John" in prompt


class TestCreateTriageNode:
    def test_returns_callable(self):
        mock_llm = MagicMock()
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        node = create_triage_node(mock_llm)
        assert callable(node)

    def test_bind_tools_called_with_triage_tools(self):
        mock_llm = MagicMock()
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        create_triage_node(mock_llm)
        mock_llm.bind_tools.assert_called_once_with(TRIAGE_TOOLS)

    def test_node_returns_state_update(self):
        mock_llm = MagicMock()
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        mock_llm.invoke = MagicMock(return_value=AIMessage(content="Hello!"))

        node = create_triage_node(mock_llm)
        result = node({
            "messages": [],
            "current_agent": "triage",
            "user_info": {"name": "Sarah Johnson"},
        })

        assert "messages" in result
        assert "current_agent" in result
        assert result["current_agent"] == "triage"

    def test_node_uses_user_name_from_state(self):
        mock_llm = MagicMock()
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        mock_llm.invoke = MagicMock(return_value=AIMessage(content="Hi"))

        node = create_triage_node(mock_llm)
        node({
            "messages": [],
            "current_agent": "triage",
            "user_info": {"name": "John Doe"},
        })

        call_args = mock_llm.invoke.call_args[0][0]
        system_msg = call_args[0]
        assert "John" in system_msg.content

    def test_node_defaults_to_customer_if_no_name(self):
        mock_llm = MagicMock()
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        mock_llm.invoke = MagicMock(return_value=AIMessage(content="Hi"))

        node = create_triage_node(mock_llm)
        node({
            "messages": [],
            "current_agent": "triage",
            "user_info": {},
        })

        call_args = mock_llm.invoke.call_args[0][0]
        system_msg = call_args[0]
        assert "Customer" in system_msg.content

    def test_node_with_available_agents(self):
        mock_llm = MagicMock()
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        mock_llm.invoke = MagicMock(return_value=AIMessage(content="Hi"))

        agents = {"account": "Account management"}
        node = create_triage_node(mock_llm, available_agents=agents)
        node({
            "messages": [],
            "current_agent": "triage",
            "user_info": {"name": "Sarah"},
        })

        call_args = mock_llm.invoke.call_args[0][0]
        system_msg = call_args[0]
        assert "account" in system_msg.content
        assert "Account management" in system_msg.content

    def test_node_without_available_agents(self):
        mock_llm = MagicMock()
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        mock_llm.invoke = MagicMock(return_value=AIMessage(content="Hi"))

        node = create_triage_node(mock_llm, available_agents=None)
        node({
            "messages": [],
            "current_agent": "triage",
            "user_info": {"name": "Sarah"},
        })

        call_args = mock_llm.invoke.call_args[0][0]
        system_msg = call_args[0]
        assert "not yet available" in system_msg.content

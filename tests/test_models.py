"""Tests for shared state definitions and mock data."""

from src.models import AgentState, MOCK_USER


class TestAgentState:
    def test_has_messages_key(self):
        assert "messages" in AgentState.__annotations__

    def test_has_current_agent_key(self):
        assert "current_agent" in AgentState.__annotations__

    def test_has_user_info_key(self):
        assert "user_info" in AgentState.__annotations__


class TestMockUser:
    REQUIRED_FIELDS = [
        "user_id",
        "name",
        "email",
        "phone",
        "account_id",
        "primary_card_id",
        "address",
        "account_type",
        "member_since",
    ]

    def test_has_all_required_fields(self):
        for field in self.REQUIRED_FIELDS:
            assert field in MOCK_USER, f"Missing field: {field}"

    def test_user_id(self):
        assert MOCK_USER["user_id"] == "USR-2847"

    def test_name(self):
        assert MOCK_USER["name"] == "Sarah Johnson"

    def test_account_id(self):
        assert MOCK_USER["account_id"] == "ACC-9182"

    def test_primary_card_id(self):
        assert MOCK_USER["primary_card_id"] == "CARD-5521"

    def test_account_type(self):
        assert MOCK_USER["account_type"] == "Premium"

    def test_all_values_are_strings(self):
        for key, value in MOCK_USER.items():
            assert isinstance(value, str), f"MOCK_USER['{key}'] should be str, got {type(value)}"

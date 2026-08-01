"""Tests for the guardrails module."""

import pytest
from unittest.mock import patch, MagicMock


class TestCheckQueryPreChecks:
    """Test pre-check logic (no API calls)."""

    def test_empty_query_rejected(self):
        """Empty or whitespace queries should be rejected."""
        from agent.guardrails import check_query

        valid, message = check_query("")
        assert valid is False
        assert "Please ask a question" in message

        valid, message = check_query("   ")
        assert valid is False

    def test_short_query_rejected(self):
        """Queries shorter than 3 chars should be rejected."""
        from agent.guardrails import check_query

        valid, message = check_query("hi")
        assert valid is False

    def test_greeting_rejected_with_friendly_message(self):
        """Simple greetings should get a friendly redirection."""
        from agent.guardrails import check_query

        greetings = ["hi", "hello", "hey", "Hello", "HI"]
        for greeting in greetings:
            valid, message = check_query(greeting)
            assert valid is False
            assert "Census data assistant" in message or "US Census" in message


class TestCheckQueryWithAPI:
    """Test API-based validation (mocked)."""

    @patch('agent.guardrails.anthropic.Anthropic')
    def test_valid_census_query_accepted(self, mock_anthropic):
        """Census-related queries should be accepted."""
        from agent.guardrails import check_query

        # Mock API response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="VALID")]
        mock_client.messages.create.return_value = mock_response

        valid, message = check_query("What is the population of California?")
        assert valid is True
        assert message is None

    @patch('agent.guardrails.anthropic.Anthropic')
    def test_off_topic_query_rejected(self, mock_anthropic):
        """Off-topic queries should be rejected with explanation."""
        from agent.guardrails import check_query

        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="INVALID: This is about weather, not census data")]
        mock_client.messages.create.return_value = mock_response

        valid, message = check_query("What's the weather in NYC?")
        assert valid is False
        assert "Census data" in message

    @patch('agent.guardrails.anthropic.Anthropic')
    def test_api_error_graceful_degradation(self, mock_anthropic):
        """API errors should allow query through (graceful degradation)."""
        from agent.guardrails import check_query

        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API unavailable")

        valid, message = check_query("What is the population of California?")
        # Should allow through on API error
        assert valid is True
        assert message is None

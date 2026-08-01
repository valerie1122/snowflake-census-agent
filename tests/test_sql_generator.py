"""Tests for the SQL generator module."""

import pytest
from unittest.mock import patch, MagicMock


class TestGenerateSQL:
    """Test SQL generation from natural language."""

    @patch('agent.sql_generator.anthropic.Anthropic')
    def test_generates_valid_sql(self, mock_anthropic):
        """Should generate SQL from question."""
        from agent.sql_generator import generate_sql

        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='SELECT SUM("B01001e1") FROM "2020_CBG_B01"')]
        mock_client.messages.create.return_value = mock_response

        sql, error = generate_sql(
            question="What is the population?",
            schema_context="Table B01",
            detected_states=["06"],
            detected_cities=[],
            year="2020",
        )

        assert sql is not None
        assert error is None
        assert "SELECT" in sql

    @patch('agent.sql_generator.anthropic.Anthropic')
    def test_strips_markdown_code_blocks(self, mock_anthropic):
        """Should strip markdown code blocks if LLM includes them."""
        from agent.sql_generator import generate_sql

        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='```sql\nSELECT * FROM table\n```')]
        mock_client.messages.create.return_value = mock_response

        sql, error = generate_sql(
            question="What is the population?",
            schema_context="Table B01",
            detected_states=[],
            detected_cities=[],
            year="2020",
        )

        assert "```" not in sql
        assert "SELECT" in sql

    @patch('agent.sql_generator.anthropic.Anthropic')
    def test_api_error_returns_error(self, mock_anthropic):
        """API errors should return error message."""
        from agent.sql_generator import generate_sql
        import anthropic

        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = anthropic.APIError(
            message="API Error",
            request=MagicMock(),
            body=None
        )

        sql, error = generate_sql(
            question="What is the population?",
            schema_context="Table B01",
            detected_states=[],
            detected_cities=[],
            year="2020",
        )

        assert sql is None
        assert error is not None
        assert "API error" in error


class TestFixSQL:
    """Test SQL fix functionality."""

    @patch('agent.sql_generator.anthropic.Anthropic')
    def test_attempts_to_fix_sql(self, mock_anthropic):
        """Should attempt to fix broken SQL."""
        from agent.sql_generator import fix_sql

        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='SELECT SUM("B01001e1") FROM "2020_CBG_B01"')]
        mock_client.messages.create.return_value = mock_response

        fixed_sql, error = fix_sql(
            original_sql='SELECT SUM(B01001e1) FROM 2020_CBG_B01',
            error_message='invalid identifier',
            schema_context="Table B01",
        )

        assert fixed_sql is not None
        assert error is None


class TestBuildUserMessage:
    """Test user message building."""

    def test_includes_question(self):
        """User message should include the question."""
        from agent.sql_generator import _build_user_message

        msg = _build_user_message(
            question="What is the population?",
            detected_states=[],
            detected_cities=[],
            year="2020",
        )

        assert "What is the population?" in msg

    def test_includes_detected_states(self):
        """User message should include detected states."""
        from agent.sql_generator import _build_user_message

        msg = _build_user_message(
            question="Population of California",
            detected_states=["06"],
            detected_cities=[],
            year="2020",
        )

        assert "06" in msg
        assert "FIPS" in msg

    def test_includes_year(self):
        """User message should include year."""
        from agent.sql_generator import _build_user_message

        msg = _build_user_message(
            question="Population",
            detected_states=[],
            detected_cities=[],
            year="2019",
        )

        assert "2019" in msg

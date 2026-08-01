"""Integration tests for the full agent pipeline."""

import pytest
from unittest.mock import patch, MagicMock


class TestTopicRouter:
    """Test the topic routing module."""

    def test_route_question_returns_schema_context(self):
        """Route question should return schema context."""
        from agent.topic_router import route_question

        result = route_question("What is the population of California?")

        assert "schema_context" in result
        assert "topics" in result
        assert "year" in result
        assert len(result["schema_context"]) > 0

    def test_route_question_detects_states(self):
        """Should detect state mentions."""
        from agent.topic_router import route_question

        result = route_question("Population of California and Texas")

        assert "detected_states" in result
        assert "06" in result["detected_states"]  # California
        assert "48" in result["detected_states"]  # Texas

    def test_route_question_detects_year(self):
        """Should detect year in question."""
        from agent.topic_router import route_question

        result = route_question("What was the population in 2019?")

        assert result["year"] == "2019"

    def test_route_question_defaults_to_2020(self):
        """Should default to 2020 if no year specified."""
        from agent.topic_router import route_question

        result = route_question("What is the population?")

        assert result["year"] == "2020"


class TestAnswerGeneration:
    """Test answer generation module."""

    def test_format_results_empty(self):
        """Empty results should format properly."""
        from agent.prompts import _format_results

        formatted, truncated = _format_results([])

        assert "No results" in formatted
        assert truncated is False

    def test_format_results_with_data(self):
        """Results with data should format as table."""
        from agent.prompts import _format_results

        results = [
            {"state": "California", "population": 39538223},
            {"state": "Texas", "population": 29145505},
        ]

        formatted, truncated = _format_results(results)

        assert "California" in formatted
        assert "Texas" in formatted
        assert truncated is False

    def test_format_results_truncates(self):
        """Large results should be truncated."""
        from agent.prompts import _format_results, MAX_RESULTS_TO_SHOW

        results = [{"id": i} for i in range(50)]

        formatted, truncated = _format_results(results)

        assert truncated is True
        assert f"Showing {MAX_RESULTS_TO_SHOW}" in formatted


class TestFullPipeline:
    """Test the full agent pipeline (mocked)."""

    def test_process_message_returns_generator_and_sql(self):
        """process_message should return a generator and optionally SQL."""
        from agent.core import process_message

        # Test with a greeting (no API calls needed - pre-check catches it)
        answer_gen, sql_used = process_message("hello", [])

        # Greeting should be rejected, no SQL
        assert sql_used is None

        # Should still return a generator
        answer = "".join(list(answer_gen))
        assert len(answer) > 0
        assert "Census" in answer  # Friendly redirect message

    @patch('agent.guardrails.anthropic.Anthropic')
    def test_process_message_rejected_by_guardrails(self, mock_anthropic):
        """Off-topic queries should be rejected."""
        from agent.core import process_message

        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="INVALID: This is about sports")]
        mock_client.messages.create.return_value = mock_response

        answer_gen, sql_used = process_message("Who won the Super Bowl?", [])

        assert sql_used is None
        answer = "".join(list(answer_gen))
        assert "Census" in answer


class TestDatabaseConnector:
    """Test database connector (without actual connection)."""

    def test_get_config_reads_env(self):
        """Config should read from environment variables."""
        import os
        from db.connector import _get_secret

        # Set test env vars
        with patch.dict(os.environ, {
            "SNOWFLAKE_ACCOUNT": "test_account",
            "SNOWFLAKE_USER": "test_user",
        }):
            assert _get_secret("SNOWFLAKE_ACCOUNT") == "test_account"
            assert _get_secret("SNOWFLAKE_USER") == "test_user"

    def test_execute_query_safe_returns_tuple(self):
        """execute_query_safe should return (results, error) tuple."""
        from db.connector import execute_query_safe

        with patch('db.connector.execute_query') as mock_exec:
            mock_exec.return_value = [{"col": "value"}]

            results, error = execute_query_safe("SELECT 1")

            assert results == [{"col": "value"}]
            assert error is None

    def test_execute_query_safe_handles_error(self):
        """execute_query_safe should handle errors gracefully."""
        from db.connector import execute_query_safe
        from snowflake.connector.errors import ProgrammingError

        with patch('db.connector.execute_query') as mock_exec:
            mock_exec.side_effect = ProgrammingError("bad SQL")

            results, error = execute_query_safe("BAD SQL")

            assert results is None
            assert error is not None
            assert "trouble processing" in error

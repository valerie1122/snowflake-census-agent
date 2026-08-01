"""Snowflake database connector with connection pooling and error handling."""

import os
from contextlib import contextmanager
from typing import Generator

import snowflake.connector
from dotenv import load_dotenv
from snowflake.connector import SnowflakeConnection
from snowflake.connector.errors import DatabaseError, ProgrammingError

load_dotenv()

# Query timeout in seconds (55s to leave margin for 60s total)
QUERY_TIMEOUT = 55


def _get_config() -> dict:
    """Load Snowflake configuration from environment variables."""
    return {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "database": os.getenv("SNOWFLAKE_DATABASE"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    }


def get_connection() -> SnowflakeConnection:
    """
    Create and return a Snowflake connection.

    Raises:
        DatabaseError: If connection fails.
    """
    config = _get_config()
    return snowflake.connector.connect(**config)


@contextmanager
def get_connection_context() -> Generator[SnowflakeConnection, None, None]:
    """Context manager for Snowflake connection with automatic cleanup."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def execute_query(sql: str) -> list[dict]:
    """
    Execute SQL query and return results as list of dicts.

    Args:
        sql: SQL query string.

    Returns:
        List of row dicts.

    Raises:
        DatabaseError: If connection fails.
        ProgrammingError: If query fails or times out.
    """
    with get_connection_context() as conn:
        cursor = conn.cursor()
        try:
            # Set query timeout
            cursor.execute(f"ALTER SESSION SET STATEMENT_TIMEOUT_IN_SECONDS = {QUERY_TIMEOUT}")
            cursor.execute(sql)

            columns = [col[0] for col in cursor.description] if cursor.description else []
            rows = cursor.fetchall()

            return [dict(zip(columns, row)) for row in rows]
        finally:
            cursor.close()


def execute_query_safe(sql: str) -> tuple[list[dict] | None, str | None]:
    """
    Execute SQL query with error handling.

    Args:
        sql: SQL query string.

    Returns:
        Tuple of (results, error_message).
        On success: (list[dict], None)
        On failure: (None, error_string)
    """
    try:
        results = execute_query(sql)
        return results, None
    except ProgrammingError as e:
        # 改成友好消息
        return None, "I had trouble processing that query. Could you try rephrasing your question?"
    except DatabaseError as e:
        return None, "I'm having trouble connecting to the database. Please try again in a moment."
    except Exception as e:
        return None, "Something unexpected happened. Please try again."

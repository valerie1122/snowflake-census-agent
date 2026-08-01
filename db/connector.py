"""Snowflake database connector with connection pooling and error handling."""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import snowflake.connector
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from dotenv import load_dotenv
from snowflake.connector import SnowflakeConnection
from snowflake.connector.errors import DatabaseError, ProgrammingError

load_dotenv()


def _get_secret(key: str) -> str | None:
    """Get secret from Streamlit secrets or environment variables."""
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key)


def _get_private_key():
    """Load private key for key-pair authentication."""
    # Try to get from Streamlit secrets first (base64 encoded)
    key_content = _get_secret("SNOWFLAKE_PRIVATE_KEY")
    if key_content:
        import base64
        key_bytes = base64.b64decode(key_content)
    else:
        # Fall back to local file
        key_path = Path(__file__).parent.parent / "rsa_key.p8"
        with open(key_path, "rb") as f:
            key_bytes = f.read()

    private_key = serialization.load_pem_private_key(
        key_bytes,
        password=None,
        backend=default_backend()
    )
    return private_key

# Query timeout in seconds (55s to leave margin for 60s total)
QUERY_TIMEOUT = 55


def _get_config() -> dict:
    """Load Snowflake configuration from environment variables or Streamlit secrets."""
    return {
        "account": _get_secret("SNOWFLAKE_ACCOUNT"),
        "user": _get_secret("SNOWFLAKE_USER"),
        "private_key": _get_private_key(),
        "database": _get_secret("SNOWFLAKE_DATABASE"),
        "schema": _get_secret("SNOWFLAKE_SCHEMA"),
        "warehouse": _get_secret("SNOWFLAKE_WAREHOUSE"),
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

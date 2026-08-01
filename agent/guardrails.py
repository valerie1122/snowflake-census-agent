"""Guardrails module for validating user queries."""

import os

import anthropic


def _get_secret(key: str) -> str | None:
    """Get secret from Streamlit secrets or environment variables."""
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key)

SYSTEM_PROMPT = """You are a query validator for a US Census data assistant.
Your job is to determine if a user's question is about US population/demographic data.

ALLOW questions about:
- Population counts, demographics, age, sex, race
- Income, poverty, employment, education
- Housing, rent, home values
- Geographic areas (states, counties, cities)
- Comparisons between regions
- Trends and distributions

REJECT questions about:
- Weather, sports, entertainment, news
- Coding, writing, creative tasks
- Anything not related to US Census/demographic data
- Inappropriate or offensive content

Respond with ONLY:
VALID - if the question is about Census/demographic data
INVALID: <brief friendly reason> - if off-topic"""


def check_query(query: str) -> tuple[bool, str | None]:
    """
    Check if query is valid for Census data assistant.

    Returns:
        (True, None) if valid
        (False, rejection_message) if invalid
    """
    # Pre-check: empty or too short
    query_stripped = query.strip()
    if len(query_stripped) < 3:
        return (False, "Please ask a question about US Census data, such as population, income, or housing statistics.")

    # Pre-check: simple greetings
    greetings = ["hi", "hello", "hey", "你好", "hola", "howdy"]
    if query_stripped.lower() in greetings:
        return (False, "Hello! I'm a US Census data assistant. Ask me about population, income, housing, education, or other demographic topics in the United States.")

    try:
        client = anthropic.Anthropic(api_key=_get_secret("ANTHROPIC_API_KEY"))

        response = client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=100,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": query}],
        )

        result = response.content[0].text.strip()
    except Exception:
        # API error - default to allowing the query (graceful degradation)
        return (True, None)

    if result.startswith("VALID"):
        return (True, None)

    # Extract rejection message after "INVALID: "
    if result.startswith("INVALID:"):
        reason = result[8:].strip()
        return (False, f"I can only answer questions about US Census data, such as population, income, education, or housing. {reason}")

    # Fallback for unexpected format
    return (False, "I can only answer questions about US Census data, such as population, income, education, or housing. What would you like to know?")

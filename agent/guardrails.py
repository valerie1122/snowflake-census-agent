"""Guardrails module for validating user queries."""

import os

import anthropic

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
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model="claude-haiku-4-20250514",
        max_tokens=100,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": query}],
    )

    result = response.content[0].text.strip()

    if result.startswith("VALID"):
        return (True, None)

    # Extract rejection message after "INVALID: "
    if result.startswith("INVALID:"):
        reason = result[8:].strip()
        return (False, f"I can only help with US Census and demographic data questions. {reason}")

    # Fallback for unexpected format
    return (False, "I can only help with US Census and demographic data questions. Please ask about population, income, housing, or other demographic topics.")

# System prompts
import os
from typing import Generator

import anthropic

# Answer Generator constants
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 500
MAX_RESULTS_TO_SHOW = 20  # Truncate results

ANSWER_SYSTEM_PROMPT = """You are a helpful assistant explaining US Census data.

Given a user's question and query results, provide a clear, concise answer.

Rules:
1. Be direct - answer the question first, then add context if helpful
2. Format numbers nicely with commas (e.g., 39,538,223 not 39538223)
3. For aggregated median values across regions, mention it's a weighted estimate
4. If results are empty, explain the data might not be available for that specific query
5. Keep answers concise - 2-3 sentences unless more detail is needed
6. If showing partial results, mention how many total results there are
7. Be conversational but informative"""


def _format_results(results: list[dict]) -> tuple[str, bool]:
    """
    Format query results for LLM consumption.

    Args:
        results: List of row dicts from SQL query

    Returns:
        (formatted_string, was_truncated)
    """
    if not results:
        return "No results returned.", False

    total = len(results)
    truncated = total > MAX_RESULTS_TO_SHOW

    to_show = results[:MAX_RESULTS_TO_SHOW] if truncated else results

    # Format as simple text table
    lines = []
    if to_show:
        headers = list(to_show[0].keys())
        lines.append(" | ".join(headers))
        lines.append("-" * 40)
        for row in to_show:
            lines.append(" | ".join(str(v) for v in row.values()))

    if truncated:
        lines.append(f"\n(Showing {MAX_RESULTS_TO_SHOW} of {total} total results)")

    return "\n".join(lines), truncated


def generate_answer(
    question: str,
    sql: str,
    results: list[dict],
    conversation_history: list[dict] | None = None,
) -> str:
    """
    Generate natural language answer from query results (non-streaming).

    Args:
        question: Original user question
        sql: SQL query that was executed
        results: Query results as list of dicts
        conversation_history: Previous messages for context

    Returns:
        Natural language answer string
    """
    client = anthropic.Anthropic()

    formatted_results, _ = _format_results(results)

    user_content = f"""Question: {question}

SQL executed: {sql}

Results:
{formatted_results}"""

    messages = []
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_content})

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=ANSWER_SYSTEM_PROMPT,
            messages=messages,
        )
        return response.content[0].text
    except anthropic.APIError as e:
        return f"Sorry, I encountered an error generating the answer: {e}"


def generate_answer_stream(
    question: str,
    sql: str,
    results: list[dict],
    conversation_history: list[dict] | None = None,
) -> Generator[str, None, None]:
    """
    Generate natural language answer with streaming.

    Args:
        question: Original user question
        sql: SQL query that was executed
        results: Query results as list of dicts
        conversation_history: Previous messages for context

    Yields:
        Text chunks as they're generated
    """
    client = anthropic.Anthropic()

    formatted_results, _ = _format_results(results)

    user_content = f"""Question: {question}

SQL executed: {sql}

Results:
{formatted_results}"""

    messages = []
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_content})

    try:
        with client.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=ANSWER_SYSTEM_PROMPT,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text
    except anthropic.APIError as e:
        yield f"Sorry, I encountered an error generating the answer: {e}"

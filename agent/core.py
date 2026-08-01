"""Agent Core - orchestrates the full agent pipeline."""

from typing import Generator

from agent.guardrails import check_query
from agent.topic_router import route_question
from agent.sql_generator import generate_and_execute
from agent.prompts import generate_answer_stream


# Keywords that suggest a data query (need location context)
DATA_KEYWORDS = [
    "population", "income", "median", "average", "how many", "percent",
    "poverty", "education", "employed", "unemployment", "housing", "rent",
    "veteran", "insurance", "commute"
]


def _is_ambiguous_query(question: str, detected_states: list, detected_cities: list) -> tuple[bool, str | None]:
    """
    Check if query is ambiguous and needs clarification.

    Returns:
        (is_ambiguous, clarification_message)
    """
    question_lower = question.lower()

    # Check if it's a data query (contains data keywords)
    is_data_query = any(kw in question_lower for kw in DATA_KEYWORDS)

    # If it's a data query but no location specified
    if is_data_query and not detected_states and not detected_cities:
        # Check if user explicitly asks for national/US data
        national_keywords = ["national", "united states", "us total", "country", "nationwide", "america"]
        if any(kw in question_lower for kw in national_keywords):
            return False, None  # User wants national data, not ambiguous

        return True, (
            "I can help with that! To give you the most relevant data, "
            "could you specify a location? For example:\n"
            "- A state: \"...in California\" or \"...in TX\"\n"
            "- A city: \"...in Seattle\" or \"...in Miami\"\n"
            "- Or say \"nationwide\" for US totals\n\n"
            "What area are you interested in?"
        )

    return False, None


def process_message(
    user_message: str,
    conversation_history: list[dict],
) -> tuple[Generator[str, None, None], str | None]:
    """
    Process user message through the full agent pipeline.

    Pipeline:
    1. Guardrails check (check_query)
    2. Topic routing (route_question)
    3. SQL generation and execution (generate_and_execute)
    4. Answer generation with streaming (generate_answer_stream)

    Args:
        user_message: User's input
        conversation_history: Previous messages in Anthropic format
                              [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
                              This list will NOT be mutated by this function.

    Returns:
        (answer_generator, sql_used)
        - answer_generator: Generator yielding answer text chunks
        - sql_used: The SQL query that was executed, or None if no SQL was run
    """
    # Step 1: Guardrails check
    is_valid, rejection_message = check_query(user_message)
    if not is_valid:
        def rejection_generator():
            yield rejection_message
        return rejection_generator(), None

    # Step 2: Topic routing
    route_result = route_question(user_message)

    # Step 2.5: Check for ambiguous queries
    is_ambiguous, clarification = _is_ambiguous_query(
        user_message,
        route_result["detected_states"],
        route_result["detected_cities"]
    )
    if is_ambiguous:
        def clarification_generator():
            yield clarification
        return clarification_generator(), None

    # Step 3: SQL generation and execution
    results, sql_used, error = generate_and_execute(
        question=user_message,
        schema_context=route_result["schema_context"],
        detected_states=route_result["detected_states"],
        detected_cities=route_result["detected_cities"],
        year=route_result["year"],
        conversation_history=conversation_history,
    )

    if error:
        def error_generator():
            yield error
        return error_generator(), None

    # Step 4: Answer generation with streaming
    answer_gen = generate_answer_stream(
        question=user_message,
        sql=sql_used,
        results=results,
        conversation_history=conversation_history,
    )

    return answer_gen, sql_used


def format_conversation_for_display(conversation_history: list[dict]) -> list[tuple[str, str]]:
    """
    Format conversation history for Streamlit chat display.

    Returns:
        List of (role, content) tuples
    """
    return [(msg["role"], msg["content"]) for msg in conversation_history]

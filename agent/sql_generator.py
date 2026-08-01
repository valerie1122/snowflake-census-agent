# Text-to-SQL generation

import os

import anthropic

from db.connector import execute_query_safe

MODEL = "claude-opus-4-5-20251101"
MAX_TOKENS = 1000
MAX_HISTORY_MESSAGES = 10  # 5 turns

SYSTEM_PROMPT = """You are a SQL expert for US Census Bureau data. Generate Snowflake SQL queries based on user questions.

## Database Structure

{schema_context}

## Key Rules

1. **Table naming**: Tables are named `{year}_CBG_{{table_code}}` (e.g., `{year}_CBG_B01`)
2. **Primary key**: `CENSUS_BLOCK_GROUP` format is `{{state_fips_2}}{{county_fips_3}}{{tract}}{{block}}`
3. **Field suffixes**: `e` = estimate, `m` = margin of error. Always use `e` fields for values.
4. **Aggregation**: Data is at Census Block Group level. For state/county totals, use SUM().
5. **State filtering**: Use `"CENSUS_BLOCK_GROUP" LIKE '{{state_fips}}%'` to filter by state.
6. **CRITICAL - Quote ALL identifiers**: Snowflake is case-sensitive. Always quote table names AND column names with double quotes.
   - Table names: `"{year}_CBG_B01"`
   - Column names: `"B01001e1"`, `"CENSUS_BLOCK_GROUP"` (all columns need quotes)

## Output Format

Return ONLY valid SQL. No explanations, no markdown, no backticks. Just the raw SQL query.

## Self-Check Before Responding

1. Is the table name correct and quoted? ("{year}_CBG_{{tablecode}}")
2. Are field names correct? (check schema_context)
3. Is aggregation needed? (SUM for totals, AVG for averages)
4. Is the WHERE clause correct for geographic filtering?
5. For median values across regions, use weighted average: SUM(median * count) / SUM(count)
6. If no geographic filter is specified, query ALL data (national level) - don't assume a state

## Handling Ambiguous Queries

- If user asks about "income" or "population" without specifying a location, return NATIONAL totals
- Use METADATA_CBG_FIELD_DESCRIPTIONS table for field name lookups if unsure
- Use METADATA_CBG_FIPS_CODES table for state/county FIPS code lookups

## Examples

User: "What is the total population of California?"
SQL: SELECT SUM("B01001e1") as total_population FROM "{year}_CBG_B01" WHERE "CENSUS_BLOCK_GROUP" LIKE '06%'

User: "Compare median income in Texas and Florida"
SQL: SELECT CASE WHEN "CENSUS_BLOCK_GROUP" LIKE '48%' THEN 'Texas' ELSE 'Florida' END as state, SUM("B19013e1" * "B19001e1") / NULLIF(SUM("B19001e1"), 0) as weighted_median_income FROM "{year}_CBG_B19" WHERE "CENSUS_BLOCK_GROUP" LIKE '48%' OR "CENSUS_BLOCK_GROUP" LIKE '12%' GROUP BY CASE WHEN "CENSUS_BLOCK_GROUP" LIKE '48%' THEN 'Texas' ELSE 'Florida' END"""

FIX_SQL_PROMPT = """The following SQL query failed with this error:

SQL: {sql}
Error: {error}

Schema context:
{schema_context}

Please fix the SQL query. Return ONLY the corrected SQL, no explanations."""


def _get_client() -> anthropic.Anthropic:
    """Get Anthropic client."""
    return anthropic.Anthropic()


def _build_user_message(
    question: str,
    detected_states: list[str],
    detected_cities: list[tuple[str, str]],
    year: str,
) -> str:
    """Build user message with geographic context."""
    parts = [question]

    if detected_states:
        parts.append(f"\n[Detected states (FIPS): {', '.join(detected_states)}]")

    if detected_cities:
        city_strs = [f"{city} (state: {state})" for city, state in detected_cities]
        parts.append(f"\n[Detected cities: {', '.join(city_strs)}]")

    parts.append(f"\n[Year: {year}]")

    return "".join(parts)


def generate_sql(
    question: str,
    schema_context: str,
    detected_states: list[str],
    detected_cities: list[tuple[str, str]],
    year: str,
    conversation_history: list[dict] | None = None,
) -> tuple[str | None, str | None]:
    """
    Generate SQL from natural language question.

    Args:
        question: User's natural language question
        schema_context: Schema info from topic_router
        detected_states: List of state FIPS codes
        detected_cities: List of (city_name, state_fips) tuples
        year: Year for data (2019 or 2020)
        conversation_history: Previous conversation messages

    Returns:
        (sql_query, None) on success
        (None, error_message) on failure
    """
    try:
        client = _get_client()

        # Build system prompt with schema and year
        system = SYSTEM_PROMPT.format(schema_context=schema_context, year=year)

        # Build messages
        messages = []

        # Add conversation history (last 10 messages)
        if conversation_history:
            messages.extend(conversation_history[-MAX_HISTORY_MESSAGES:])

        # Add current question
        user_message = _build_user_message(
            question, detected_states, detected_cities, year
        )
        messages.append({"role": "user", "content": user_message})

        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=messages,
        )

        sql = response.content[0].text.strip()

        # Clean up any markdown code blocks if model returns them anyway
        if sql.startswith("```"):
            lines = sql.split("\n")
            sql = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            sql = sql.strip()

        return sql, None

    except anthropic.APIError as e:
        return None, f"API error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error generating SQL: {str(e)}"


def fix_sql(
    original_sql: str,
    error_message: str,
    schema_context: str,
) -> tuple[str | None, str | None]:
    """
    Attempt to fix a failed SQL query.

    Args:
        original_sql: The SQL that failed
        error_message: Error message from execution
        schema_context: Schema info for context

    Returns:
        (fixed_sql, None) on success
        (None, error_message) on failure
    """
    try:
        client = _get_client()

        prompt = FIX_SQL_PROMPT.format(
            sql=original_sql,
            error=error_message,
            schema_context=schema_context,
        )

        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )

        sql = response.content[0].text.strip()

        # Clean up any markdown code blocks
        if sql.startswith("```"):
            lines = sql.split("\n")
            sql = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            sql = sql.strip()

        return sql, None

    except anthropic.APIError as e:
        return None, f"API error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error fixing SQL: {str(e)}"


def generate_and_execute(
    question: str,
    schema_context: str,
    detected_states: list[str],
    detected_cities: list[tuple[str, str]],
    year: str,
    conversation_history: list[dict] | None = None,
) -> tuple[list[dict] | None, str | None, str | None]:
    """
    Generate SQL, execute it, retry once if failed.

    Args:
        question: User's natural language question
        schema_context: Schema info from topic_router
        detected_states: List of state FIPS codes
        detected_cities: List of (city_name, state_fips) tuples
        year: Year for data (2019 or 2020)
        conversation_history: Previous conversation messages

    Returns:
        (results, sql_used, None) on success
        (None, None, error_message) on failure
    """
    # Step 1: Generate SQL
    sql, gen_error = generate_sql(
        question=question,
        schema_context=schema_context,
        detected_states=detected_states,
        detected_cities=detected_cities,
        year=year,
        conversation_history=conversation_history,
    )

    if gen_error:
        return None, None, gen_error

    # Step 2: Execute SQL
    results, exec_error = execute_query_safe(sql)

    if results is not None:
        return results, sql, None

    # Step 3: Try to fix and retry once
    fixed_sql, fix_error = fix_sql(
        original_sql=sql,
        error_message=exec_error,
        schema_context=schema_context,
    )

    if fix_error:
        return None, None, "I couldn't process that query. Please try rephrasing your question."

    # Step 4: Execute fixed SQL
    results, exec_error = execute_query_safe(fixed_sql)

    if results is not None:
        return results, fixed_sql, None

    # Both attempts failed
    return None, None, "I had trouble with that query. Could you try asking in a different way?"

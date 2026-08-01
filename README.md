# US Census Data Assistant

An AI-powered chat assistant that answers natural language questions about US Census demographic data, built with Streamlit, Snowflake, and Claude.

## Live Demo

**URL**: https://app-census-agent-2xw8tvr4lzc2ndukfkvp9d.streamlit.app

No authentication required - just open and ask questions!

## Features

- **Natural Language Interface**: Ask questions in plain English about US population, income, education, housing, veterans, and more
- **Multi-turn Conversations**: Context is preserved across questions for follow-up queries
- **Streaming Responses**: Answers stream in real-time for better UX
- **SQL Transparency**: View the generated SQL queries powering each answer
- **Guardrails**: Off-topic and inappropriate queries are politely redirected
- **Graceful Degradation**: User-friendly error messages when queries fail

## Architecture

```
User Question
     │
     ▼
┌─────────────┐
│  Guardrails │ ── reject off-topic ──▶ Friendly redirect
└─────────────┘
     │ pass
     ▼
┌──────────────┐
│ Topic Router │ ── detect topics, states, cities, year
└──────────────┘
     │
     ▼
┌───────────────┐
│ SQL Generator │ ── Claude LLM generates Snowflake SQL
└───────────────┘
     │
     ▼
┌──────────────┐
│  Snowflake   │ ── execute query (retry once on error)
└──────────────┘
     │
     ▼
┌───────────────────┐
│ Answer Generator  │ ── Claude LLM explains results
└───────────────────┘
     │
     ▼
Streaming Response
```

## Project Structure

```
├── app.py                  # Streamlit web interface
├── agent/
│   ├── core.py             # Pipeline orchestration
│   ├── guardrails.py       # Query validation
│   ├── topic_router.py     # Topic/geography detection
│   ├── sql_generator.py    # Text-to-SQL generation
│   └── prompts.py          # Answer generation
├── db/
│   ├── connector.py        # Snowflake connection
│   └── schema.py           # Census table metadata
├── tests/
│   ├── test_guardrails.py
│   ├── test_schema.py
│   ├── test_sql_generator.py
│   └── test_integration.py
├── requirements.txt
└── .env                    # Environment variables (not committed)
```

## Setup

### Prerequisites

- Python 3.11+
- Snowflake account with US Census Marketplace data
- Anthropic API key

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd snowflake-fde-ai-takehome

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your credentials
```

### Environment Variables

```
ANTHROPIC_API_KEY=your_anthropic_key
SNOWFLAKE_ACCOUNT=your_account_id
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=US_OPEN_CENSUS_DATA_NEIGHBORHOOD_INSIGHTS_FREE_DATASET
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
```

### Running Locally

```bash
streamlit run app.py
```

The app will be available at http://localhost:8501

## Running Tests

```bash
pytest tests/ -v
```

## Example Questions

- "What is the population of California?"
- "Compare median income in Texas and New York"
- "How many veterans live in Florida?"
- "What's the education level in Seattle?"
- "What percentage of people in Michigan have health insurance?"
- "Show me housing data for counties in Ohio"

## Technical Details

### Data Source

The app queries the Snowflake Marketplace dataset "US Census Bureau: ACS Demographic & Socioeconomic Data" which contains:

- Census Block Group level data (most granular)
- 2019 and 2020 ACS 5-year estimates
- 29 demographic tables (B01-B99, C02-C24)

### Key Design Decisions

1. **Keyword-based Topic Routing**: Uses keyword matching for fast, predictable table selection rather than LLM classification
2. **Schema Context Injection**: Provides relevant schema info to the SQL generator LLM for accurate queries
3. **SQL Retry Mechanism**: On execution failure, attempts to fix the SQL once before returning an error
4. **Streaming**: Uses Claude's streaming API for real-time answer generation
5. **Quoted Identifiers**: All Snowflake identifiers are double-quoted for case sensitivity

## Limitations

- Geographic queries below state level (cities, counties) use approximate matching
- Median aggregations across regions are weighted estimates, not true medians
- Only supports 2019 and 2020 data years

## Assumptions & Interpretations

During development, I made the following interpretations of the requirements:

1. **"Preserve conversation context"**: Interpreted as passing conversation history to the LLM for follow-up questions, not as persistent storage across sessions.

2. **"Guardrails for off-topic responses"**: Implemented as a two-tier system - fast pre-checks for obvious cases (greetings, empty queries) plus LLM-based validation for nuanced off-topic detection.

3. **"60 second response time"**: Set query timeout to 55 seconds to leave margin. Used streaming to show progress immediately rather than waiting for full response.

4. **"Graceful degradation"**: Chose to show user-friendly error messages rather than technical errors. On guardrail API failure, allow query through (fail open) rather than blocking.

5. **"Ambiguous queries"**: Added clarification prompts when users ask data questions without specifying location, rather than assuming national data or failing silently.

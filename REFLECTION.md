# Reflection

## What Went Well

### 1. Clean Pipeline Architecture
The modular pipeline design (Guardrails → Topic Router → SQL Generator → Answer Generator) made the system easy to reason about and debug. Each component has a single responsibility and can be tested independently.

### 2. Effective Guardrails
The two-tier guardrail system works well:
- Pre-checks catch obvious cases (empty queries, greetings) without API calls
- LLM-based validation handles nuanced off-topic detection
- Graceful degradation allows queries through when the API is unavailable

### 3. Streaming UX
Implementing streaming responses significantly improves perceived latency. Users see answers appearing immediately rather than waiting for the full response.

### 4. SQL Retry Mechanism
The automatic SQL fix-and-retry saves many queries that would otherwise fail due to minor LLM mistakes (wrong column names, missing quotes). This happens transparently to the user.

### 5. Comprehensive Testing
50 unit and integration tests provide good coverage of the core logic without requiring actual API calls or database connections.

## What I Would Improve With More Time

### 1. Schema Accuracy
The `key_fields` in `db/schema.py` were populated based on Census Bureau documentation but haven't been fully verified against the actual Snowflake schema. Some field names may be incorrect. I would:
- Query `INFORMATION_SCHEMA.COLUMNS` for each table
- Validate every field reference
- Build a script to auto-generate schema metadata

### 2. Geographic Query Support
Currently, city-level queries are approximate (match city name to state, not actual boundaries). Improvements:
- Use the FIPS codes from `METADATA_CBG_FIPS_CODES` table for precise matching
- Add county-level routing with proper FIPS prefix filtering
- Consider adding ZIP code support

### 3. Conversation Memory
The current implementation passes full conversation history to the SQL generator, which can exceed context limits on long conversations. Would add:
- Conversation summarization for long sessions
- Smart history trimming that preserves relevant context
- Better handling of follow-up questions ("What about Texas?")

### 4. Caching Layer
No caching is currently implemented. Would add:
- Query result caching with TTL (Census data is static)
- LRU cache for common queries
- Connection pooling for Snowflake

### 5. Better Error Messages
Current error messages are generic. Would improve:
- Parse SQL errors to give specific guidance
- Suggest alternative phrasings when queries fail
- Show partial results when possible

### 6. Deployment Hardening
For production deployment, would add:
- Rate limiting per user
- Request logging and monitoring
- Health check endpoint
- Secrets management (not .env files)

## Technical Decisions and Tradeoffs

### Why Streamlit (not FastAPI + React)
**Decision**: Used Streamlit for the entire web interface instead of a separate backend/frontend.

**Tradeoff**: Less flexibility and customization, but:
- Rapid development (hours, not days)
- Built-in streaming support
- Native chat UI components
- One-click deployment to Streamlit Cloud
- Perfect for a 24-hour assignment where shipping matters

### Why Text-to-SQL (not RAG/Vector Search)
**Decision**: Used LLM to generate SQL queries directly against Snowflake.

**Tradeoff**: Requires careful prompt engineering and schema context, but:
- Census data is structured and tabular - SQL is the natural query language
- No need to embed/chunk data or manage a vector database
- Exact numeric aggregations (SUM, AVG) are reliable
- Users can see the actual SQL for transparency
- RAG would be overkill for structured data queries

### Why Static Schema Metadata (not Dynamic Discovery)
**Decision**: Hardcoded table topics and key fields in `db/schema.py` instead of querying `INFORMATION_SCHEMA` at runtime.

**Tradeoff**: Schema changes require code updates, but:
- Faster response times (no metadata queries)
- Curated field descriptions are more useful than raw column names
- Census schema is stable (doesn't change frequently)
- Allows keyword-to-table mapping for routing
- Production would add a schema sync job for updates

### Using Keyword Matching for Topic Routing
**Decision**: Used keyword-based matching instead of LLM classification for topic routing.

**Tradeoff**: Less flexible than LLM classification, but:
- Faster (no API call)
- Predictable behavior
- Easier to debug
- No additional cost

### Using Claude Opus 4.5 for All LLM Calls
**Decision**: Used the same model (Opus 4.5) for guardrails, SQL generation, and answer generation.

**Tradeoff**: Opus 4.5 may be overkill for simple guardrail checks where a smaller model would suffice. However:
- Simpler configuration
- Consistent behavior
- Note: Tried using Sonnet/Haiku but received 404 errors, so Opus was the only working option

### Quoting All Snowflake Identifiers
**Decision**: Modified the SQL generator prompt to quote all table and column names.

**Tradeoff**: Slightly more verbose SQL, but:
- Eliminates case-sensitivity issues
- More robust against unusual column names
- Matches Snowflake best practices

### Graceful Degradation on API Errors
**Decision**: Allow queries through when the guardrails API fails.

**Tradeoff**: Could let inappropriate queries through, but:
- Better UX than failing completely
- The SQL generator itself won't produce harmful output
- Production would have additional safeguards

### Streaming vs Batched Responses
**Decision**: Implemented streaming for answer generation.

**Tradeoff**: More complex code, but:
- Much better perceived latency
- Users can start reading immediately
- Matches expectations from modern chat interfaces

## Performance Considerations

- **Query Timeout**: Set to 55 seconds (leaving margin for 60-second total)
- **Result Truncation**: Limited to 20 rows to keep LLM context manageable
- **History Limit**: Last 10 messages (5 turns) to prevent context overflow

## Edge Cases and Failure Modes

### Identified and Handled
1. **Empty/short queries**: Pre-check rejects queries < 3 characters
2. **Greetings**: Detected and redirected with friendly message
3. **Off-topic queries**: LLM-based guardrails reject and explain
4. **SQL syntax errors**: Automatic retry with fix attempt
5. **Database connection failures**: User-friendly error message
6. **API unavailability**: Graceful degradation (allow query through)

### Identified but Not Fully Addressed
1. **Ambiguous queries**: "What's the income?" without location context - currently returns national data, could prompt for clarification
2. **Queries about unavailable data**: e.g., "What's the crime rate?" - not in Census dataset, would need explicit rejection
3. **Complex multi-table queries**: e.g., "Show income by education level" - requires JOINs which may fail
4. **Temporal comparisons**: "How has population changed?" - only 2019/2020 data available
5. **Very large result sets**: Could timeout on queries returning millions of rows

### Edge Cases for Future Work
- Handling typos in state/city names
- Supporting natural date ranges ("last 5 years")
- Multi-language support
- Clarification dialogs for ambiguous queries

## Testing Strategy and Tradeoffs

### Approach
I chose a **mock-heavy unit testing** strategy with 50 tests covering:
- Pre-check logic (no API calls)
- Schema utilities (pure functions)
- Topic routing (keyword matching)
- SQL generation (mocked LLM responses)
- Pipeline integration (mocked components)

### Why This Approach
1. **Fast execution**: Tests run in ~2 seconds without API calls
2. **Deterministic**: No flaky tests from API variability
3. **Cost-effective**: No API costs during test runs
4. **CI-friendly**: Can run in any environment

### Tradeoffs
- **Less realistic**: Mocked responses may not match real LLM behavior
- **Missing integration coverage**: Real Snowflake queries not tested
- **Prompt changes require test updates**: If prompts change, mock responses may become invalid

### What I Would Add
1. **End-to-end tests**: Real queries against Snowflake (run sparingly)
2. **Golden file tests**: Store expected SQL outputs and compare
3. **Load testing**: Verify 60-second response time under load
4. **Prompt regression tests**: Ensure prompt changes don't break SQL generation

## Development Process

1. **Planning**: Read requirements, designed pipeline architecture
2. **Data exploration**: Connected to Snowflake, explored schema, sampled tables
3. **Core pipeline**: Built guardrails → router → SQL generator → answer generator
4. **Integration**: Connected components, added streaming
5. **Error handling**: Added graceful degradation, user-friendly messages
6. **Testing**: Wrote 50 unit/integration tests
7. **Documentation**: README, REFLECTION
8. **Deployment**: Streamlit Cloud with key-pair auth

## AI Tools Usage

I used **Claude Code** (Claude Opus 4.5) extensively throughout this project. Here's how:

### What AI Helped With
- **Architecture design**: Discussed pipeline structure (guardrails → router → SQL → answer)
- **Snowflake authentication debugging**: Solved MFA issues, switched to key-pair auth
- **Prompt engineering**: Iterated on SQL generator prompts (quoting identifiers, examples)
- **Code generation**: Initial implementations of each module
- **Test writing**: Generated 50 unit/integration tests with proper mocking
- **Documentation**: README structure, REFLECTION content

### What I Did Manually
- **Decision making**: Chose Streamlit over FastAPI, Text-to-SQL over RAG
- **Requirements interpretation**: Decided what "ambiguous query" means
- **Quality review**: Verified generated code, fixed edge cases
- **Deployment configuration**: Streamlit Cloud secrets, GitHub setup

### How I Used It Effectively
1. **Iterative refinement**: Started with basic implementations, then added error handling
2. **Debugging partner**: When Snowflake MFA failed, worked through solutions together
3. **Time optimization**: AI handled boilerplate (tests, docs) so I could focus on architecture
4. **Prompt iteration**: Refined SQL generator prompts based on actual query failures

### Lessons Learned
- AI excels at generating boilerplate but needs human judgment for architecture
- Debugging complex auth issues (MFA, key-pair) required back-and-forth iteration
- Clear requirements lead to better AI output - vague requests get vague code

## What I Learned

1. **Snowflake Case Sensitivity**: Snowflake identifiers with mixed case must be quoted. Unquoted identifiers are automatically uppercased, causing "invalid identifier" errors for columns like `B01001e1`.

2. **MFA Integration**: Snowflake MFA with Duo requires `authenticator: "username_password_mfa"` and triggers a push notification on each connection.

3. **Census Data Structure**: Census Bureau data at Block Group level is aggregated (not pre-computed totals), requiring SUM() for state/county totals and weighted averages for medians.

4. **Prompt Engineering**: The SQL generator prompt needed explicit examples with proper quoting. Without examples, the LLM consistently forgot to quote identifiers.

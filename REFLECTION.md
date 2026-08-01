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

## What I Learned

1. **Snowflake Case Sensitivity**: Snowflake identifiers with mixed case must be quoted. Unquoted identifiers are automatically uppercased, causing "invalid identifier" errors for columns like `B01001e1`.

2. **MFA Integration**: Snowflake MFA with Duo requires `authenticator: "username_password_mfa"` and triggers a push notification on each connection.

3. **Census Data Structure**: Census Bureau data at Block Group level is aggregated (not pre-computed totals), requiring SUM() for state/county totals and weighted averages for medians.

4. **Prompt Engineering**: The SQL generator prompt needed explicit examples with proper quoting. Without examples, the LLM consistently forgot to quote identifiers.

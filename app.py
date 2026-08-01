import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from agent.core import process_message

# Page config
st.set_page_config(
    page_title="US Census Data Assistant",
    page_icon="🏛️",
    layout="centered",
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []  # [(role, content, sql_or_none), ...]

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []  # Anthropic format for LLM

# Title
st.title("🏛️ US Census Data Assistant")
st.caption("Ask questions about US population, income, education, housing, and more.")

# Example questions
st.markdown("**Try these examples:**")
col1, col2 = st.columns(2)
with col1:
    if st.button("Population of California", key="ex1"):
        st.session_state.pending_question = "What is the population of California?"
        st.rerun()
    if st.button("Education in Seattle", key="ex3"):
        st.session_state.pending_question = "What is the education level in Seattle?"
        st.rerun()
with col2:
    if st.button("Income: Texas vs New York", key="ex2"):
        st.session_state.pending_question = "Compare median income in Texas and New York"
        st.rerun()
    if st.button("Veterans in Florida", key="ex4"):
        st.session_state.pending_question = "How many veterans live in Florida?"
        st.rerun()

# Display chat history
for role, content, sql in st.session_state.messages:
    with st.chat_message(role):
        st.write(content)
        if sql and role == "assistant":
            with st.expander("Show SQL"):
                st.code(sql, language="sql")

# Clear button + Chat input
col1, col2 = st.columns([6, 1])
with col2:
    if st.button("Clear", type="secondary"):
        st.session_state.messages = []
        st.session_state.conversation_history = []
        st.rerun()

# Check for pending question (from example buttons)
user_input = None
if "pending_question" in st.session_state:
    user_input = st.session_state.pending_question
    del st.session_state.pending_question
else:
    user_input = st.chat_input("Ask about US Census data...")

# Process new messages
if user_input:
    # Display user message
    with st.chat_message("user"):
        st.write(user_input)

    # Add to messages list
    st.session_state.messages.append(("user", user_input, None))

    # Process message
    with st.chat_message("assistant"):
        answer_gen, sql_used = process_message(
            user_message=user_input,
            conversation_history=st.session_state.conversation_history,
        )

        # Streaming output
        response = st.write_stream(answer_gen)

        # Show SQL if available
        if sql_used:
            with st.expander("Show SQL"):
                st.code(sql_used, language="sql")

    # Update history
    st.session_state.messages.append(("assistant", response, sql_used))
    st.session_state.conversation_history.append({"role": "user", "content": user_input})
    st.session_state.conversation_history.append({"role": "assistant", "content": response})

# Optional styling
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

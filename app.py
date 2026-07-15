import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
import asyncio
from src.agent_utils import search_and_answer

load_dotenv()

# Page config
st.set_page_config(page_title="Knowledge Assistant", page_icon="🔍")
st.title("🔍 Internal Knowledge Assistant")

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Sidebar for user authentication
with st.sidebar:
    st.header("Authentication")

    # Preset user tokens
    user_options = {
        "Maria (Marketing)": "tok_marketing_demo",
        "Sam (Sales)": "tok_sales_demo",
        "Priya (People/HR)": "tok_people_demo",
        "Erin (Exec)": "tok_exec_demo"
    }

    selected_user = st.selectbox("Select User:", list(user_options.keys()))
    user_token = user_options[selected_user]

    st.success(f"Logged in as {selected_user}")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Track current user and reset chat when user switches
if "current_user" not in st.session_state:
    st.session_state.current_user = selected_user
elif st.session_state.current_user != selected_user:
    # User switched, clear chat history
    st.session_state.messages = []
    st.session_state.current_user = selected_user
    st.rerun()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("documents"):
            with st.expander("📄 Source Documents"):
                for i, doc in enumerate(message["documents"], 1):
                    st.markdown(f"**{i}. {doc['title']}**")
                    st.caption(f"Source: {doc['source']} | Period: {doc['period']} | Status: {doc['status']}")

# Chat input
if prompt := st.chat_input("Ask a question about internal documents..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base..."):
            # Run async function
            result = asyncio.run(search_and_answer(openai_client, user_token, prompt))

            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                st.markdown(result["answer"])

                # Show source documents
                with st.expander("📄 Source Documents"):
                    for i, doc in enumerate(result["documents"], 1):
                        st.markdown(f"**{i}. {doc['title']}**")
                        st.caption(f"Source: {doc['source']} | Period: {doc['period']} | Status: {doc['status']}")

                # Add assistant response to chat
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["answer"],
                    "documents": result["documents"]
                })

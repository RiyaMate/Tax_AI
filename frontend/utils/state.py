import streamlit as st

def init_session_state():
    defaults = {
        "api_connected": False,
        "fastapi_url": "http://localhost:8000",

        # Markdown handling
        "markdown_history": {},
        "selected_markdown_content": None,
        "selected_markdown_name": None,
        "markdown_ready": False,

        # LLM responses
        "llm_model": "gemini-2.5-flash-preview-09-2025",
        "summary_result": None,
        "question_result": None,
        "markdown_summaries": {},
        "markdown_qa": {},

        # PDF upload status
        "file_uploaded": False,
        "next_clicked": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
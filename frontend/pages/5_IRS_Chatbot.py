"""
IRS Chatbot - Answer tax questions
"""

import streamlit as st
import requests
import json
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="IRS Chatbot",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 IRS Chatbot")
st.markdown("Ask questions about taxes, forms, deductions, and IRS rules")

# ============================================================================
# SESSION STATE
# ============================================================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "api_endpoint" not in st.session_state:
    st.session_state.api_endpoint = "http://localhost:8000"

# ============================================================================
# SIDEBAR CONFIG
# ============================================================================

with st.sidebar:
    st.title("⚙️ Configuration")
    
    api_endpoint = st.text_input(
        "API Endpoint",
        value="http://localhost:8000",
        help="Base URL for the tax API"
    )
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

# ============================================================================
# MAIN CONTENT
# ============================================================================

# Display chat history
for message in st.session_state.chat_history:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(message["content"])
    else:
        with st.chat_message("assistant"):
            st.markdown(message["content"])

# Chat input
user_question = st.chat_input("Ask a tax question...")

if user_question:
    # Add user message to history
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_question
    })
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_question)
    
    # Get response from chatbot
    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking..."):
                response = requests.post(
                    f"{api_endpoint}/api/tax/chat",
                    json={"question": user_question},
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                bot_response = result.get("response", "I couldn't generate a response.")
            else:
                bot_response = f"Error: {response.status_code} - {response.text[:200]}"
        
        except Exception as e:
            bot_response = f"Error connecting to API: {str(e)}"
        
        # Display response
        st.markdown(bot_response)
        
        # Add to history
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": bot_response
        })

# ============================================================================
# QUICK QUESTIONS
# ============================================================================

st.divider()
st.subheader("📚 Quick Questions")

col1, col2 = st.columns(2)

with col1:
    quick_questions = [
        "What is the 2024 standard deduction for single filers?",
        "What forms trigger self-employment tax?",
        "How do I calculate self-employment tax?",
        "What's the difference between W-2 and 1099?",
    ]
    
    for q in quick_questions:
        if st.button(q, use_container_width=True, key=f"q1_{q}"):
            st.session_state.chat_history.append({
                "role": "user",
                "content": q
            })
            st.rerun()

with col2:
    quick_questions_2 = [
        "What are 2024 tax brackets?",
        "Can I deduct home office expenses?",
        "What is Form 1099-NEC used for?",
        "How do dividend taxes work?",
    ]
    
    for q in quick_questions_2:
        if st.button(q, use_container_width=True, key=f"q2_{q}"):
            st.session_state.chat_history.append({
                "role": "user",
                "content": q
            })
            st.rerun()

# ============================================================================
# TAX RESOURCES
# ============================================================================

st.divider()
st.subheader("📖 Tax Resources")

st.markdown("""
### Official IRS Resources
- [IRS.gov](https://www.irs.gov) - Official IRS website
- [Tax Forms & Publications](https://www.irs.gov/forms-pubs) - Download all tax forms
- [Interactive Tax Assistant](https://www.irs.gov/help-resources) - IRS FAQs

### Common Forms
- **Form 1040:** U.S. Individual Income Tax Return
- **Form W-2:** Wage and Tax Statement
- **Form 1099-NEC:** Nonemployee Compensation
- **Form 1099-MISC:** Miscellaneous Income
- **Form 1099-DIV:** Dividends and Distributions
- **Form 1099-INT:** Interest Income
- **Form 1099-K:** Payment Card Transactions

### 2024 Key Numbers
- **Standard Deduction (Single):** $14,600
- **Standard Deduction (Married Filing Jointly):** $29,200
- **Medicare Tax Threshold (Single):** $200,000
- **Net Investment Income Tax Threshold (Single):** $200,000
""")

import streamlit as st
import os
from utils.state import init_session_state
from utils.styles import DARK_THEME_CSS
from utils.sidebar_toggle import add_mobile_sidebar_toggle

# Try to import LLM provider
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

st.set_page_config(
    page_title="IRS Q&A Chatbot",
    layout="wide",
    initial_sidebar_state="auto"
)

init_session_state()

st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

# Add mobile sidebar toggle
add_mobile_sidebar_toggle()

st.markdown("<h1 style='background: #1a1f3a; color: white !important; text-align: center; padding: 20px; border-radius: 8px; margin: 0; border: 2px solid #10b981; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);'>IRS Q&A CHATBOT</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #10b981 !important; text-align: center; opacity: 0.9; font-size: 0.95em;'>AI-Powered Real-Time IRS Questions & Answers</p>", unsafe_allow_html=True)

# Define function first before using it
def get_irs_answer_realtime(user_query: str) -> str:
    """Get real-time IRS answer using AI."""
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return """I need an API key to provide real-time answers. 
        
Please set the GEMINI_API_KEY environment variable to enable AI-powered responses.

In the meantime, I can provide some quick information, but for real-time accurate answers about IRS tax guidance, please configure the API key."""
    
    if not GENAI_AVAILABLE:
        return """The AI library is not installed. Please install google-generativeai to enable real-time responses.
        
Install with: pip install google-generativeai"""
    
    try:
        genai.configure(api_key=api_key)
        
        system_prompt = """You are an expert IRS tax assistant with comprehensive knowledge of:
- US Tax Code and IRS regulations
- Tax forms and schedules (1040, W-2, 1099, schedules A-E, etc.)
- Deductions and tax credits
- Filing requirements and deadlines
- Special tax situations
- Tax planning strategies
- IRS procedures and services

IMPORTANT: Always provide accurate, current IRS information. If you're unsure about something, say so.
Current tax year information: 2024 taxes due April 15, 2025.

Provide clear, practical answers that are easy to understand. Include specific dollar amounts, dates, and form numbers when relevant."""
        
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        response = model.generate_content(
            f"{system_prompt}\n\nUser question about IRS/taxes: {user_query}"
        )
        
        if response.text:
            return response.text
        else:
            return "I couldn't generate a response. Please try again."
    
    except Exception as e:
        return f"I encountered an error while generating a real-time answer: {str(e)}. Please check that your GEMINI_API_KEY is configured correctly."


if "irs_qa_history" not in st.session_state:
    st.session_state.irs_qa_history = [
        {
            "role": "assistant",
            "content": "Hello! I'm your AI-powered IRS Q&A Assistant. Ask me any questions about taxes, filing, forms, deductions, credits, payments, or IRS services. I'll provide real-time answers based on current IRS guidance!"
        }
    ]

col_main, col_sidebar = st.columns([3, 1])

with col_main:
    st.subheader("Chat")
    
    # Add CSS for auto-scrolling chat container
    st.markdown("""
    <style>
    .chat-container {
        display: flex;
        flex-direction: column;
        height: 500px;
        overflow-y: auto;
        overflow-x: hidden;
        padding-right: 10px;
    }
    .chat-container::-webkit-scrollbar {
        width: 8px;
    }
    .chat-container::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    .chat-container::-webkit-scrollbar-thumb {
        background: #10b981;
        border-radius: 4px;
    }
    .chat-container::-webkit-scrollbar-thumb:hover {
        background: #059669;
    }
    </style>
    <script>
    function scrollChatToBottom() {
        const chatContainer = document.querySelector('[data-testid="stContainer"]');
        if (chatContainer) {
            setTimeout(() => {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }, 100);
        }
    }
    // Scroll on page load
    window.addEventListener('load', scrollChatToBottom);
    </script>
    """, unsafe_allow_html=True)
    
    chat_container = st.container(height=500)
    with chat_container:
        for message in st.session_state.irs_qa_history:
            with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
                st.markdown(message["content"])
    
    user_input = st.chat_input("Ask a question about the IRS...")
    
    if user_input:
        st.session_state.irs_qa_history.append({"role": "user", "content": user_input})
        
        with st.spinner("Generating real-time answer..."):
            response = get_irs_answer_realtime(user_input)
        
        st.session_state.irs_qa_history.append({"role": "assistant", "content": response})
        
        # Scroll to bottom after new message
        st.markdown("""
        <script>
        window.scrollTo(0, document.body.scrollHeight);
        </script>
        """, unsafe_allow_html=True)
        
        st.rerun()

with col_sidebar:
    st.subheader("Quick Tips")
    
    st.markdown("""
**Ask about:**
- Filing deadlines
- Tax forms needed
- Deductions & credits
- Refund status
- Payment options
- Who must file
- Document requirements
- Extensions
- Amendments
- Self-employment
- Dependents
- Filing status
    """)
    
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.irs_qa_history = [
            {
                "role": "assistant",
                "content": "Hello! I'm your AI-powered IRS Q&A Assistant. Ask me any questions about taxes, filing, forms, deductions, credits, payments, or IRS services. I'll provide real-time answers based on current IRS guidance!"
            }
        ]
        st.rerun()

st.markdown("---")
st.caption("Real-Time AI-Powered IRS Q&A | For official details visit www.irs.gov | Call 1-800-829-1040 for support")

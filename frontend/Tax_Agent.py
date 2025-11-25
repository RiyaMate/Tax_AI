"""
Streamlit UI for GreenGrowth CPAs Tax Calculator
Upload PDF → Document Extraction → AI Processing → Tax Calculation Display
"""

import streamlit as st
import requests
import json
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="GreenGrowth CPAs - Tax Calculator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if "tax_result" not in st.session_state:
    st.session_state["tax_result"] = None

if "pdf_extracted" not in st.session_state:
    st.session_state["pdf_extracted"] = False

if "pdf_landingai_output" not in st.session_state:
    st.session_state["pdf_landingai_output"] = None

if "calculate_clicked" not in st.session_state:
    st.session_state["calculate_clicked"] = False

if "current_manual_input" not in st.session_state:
    st.session_state["current_manual_input"] = None

# ============================================================================
# SIDEBAR CONFIG
# ============================================================================

with st.sidebar:
    st.title("⚙️ Configuration")
    
    # Filing status
    filing_status = st.selectbox(
        "Filing Status",
        options=[
            "single",
            "married_filing_jointly",
            "married_filing_separately",
            "head_of_household",
            "qualifying_widow"
        ],
        format_func=lambda x: {
            "single": "Single",
            "married_filing_jointly": "Married Filing Jointly",
            "married_filing_separately": "Married Filing Separately",
            "head_of_household": "Head of Household",
            "qualifying_widow": "Qualifying Widow(er)"
        }.get(x, x)
    )
    
    # Number of dependents
    num_dependents = st.number_input(
        "Number of Dependents",
        min_value=0,
        max_value=20,
        value=0,
        step=1
    )
    
    st.divider()
    st.subheader("ℹ️ About")
    st.markdown("""
    **GreenGrowth CPAs Tax Calculator** processes tax documents using:
    - 📄 Document extraction
    - 🧠 Intelligent processing
    - 📊 Automated 2024 IRS tax calculation
    
    Supported forms:
    - W-2
    - 1099-NEC
    - 1099-MISC (including Box 5 fishing)
    - 1099-INT
    - 1099-DIV
    - 1099-K
    """)


# ============================================================================
# MAIN UI
# ============================================================================

# Header with branding
col1, col2 = st.columns([0.7, 0.3])
with col1:
    st.title("📊 GreenGrowth CPAs")
    st.markdown("### Professional Tax Calculator")
with col2:
    st.markdown("""
    <div style='text-align: right; padding: 20px;'>
    <b>2024 Tax Year</b><br>
    Ready to calculate
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Quick info banner
st.info("✨ Upload your tax documents or enter values manually. We'll automatically calculate your 2024 taxes using IRS rules.", icon="💡")

# Create tabs with better organization
tab1, tab2, tab3, tab4 = st.tabs(
    ["📤 Upload & Calculate", "📝 Manual Entry", "📊 Results", "❓ Help"]
)

# ============================================================================
# TAB 1: UPLOAD & PROCESS
# ============================================================================

with tab1:
    st.header("Upload Tax Documents")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Supported Formats:** W-2, 1099-NEC, 1099-DIV, 1099-INT, 1099-MISC, 1099-K")
        st.markdown("---")
        
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=["pdf"],
            help="Upload your tax form PDF",
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            st.success(f"✅ File uploaded: **{uploaded_file.name}**")
            
            # Try to extract via PDF processing
            try:
                with st.spinner("🔄 Processing document... This may take a minute..."):
                    # Send file directly to API with longer timeout
                    response = requests.post(
                        "http://localhost:8000/api/tax/extract-landingai",
                        files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")},
                        timeout=300  # 5 minute timeout for document processing
                    )
                
                if response.status_code == 200:
                    landingai_output = response.json()
                    st.session_state["pdf_extracted"] = True
                    st.session_state["pdf_landingai_output"] = landingai_output
                    st.success("✅ Document extracted successfully!")
                    
                    # AUTO-PROCESS: Automatically calculate taxes after successful extraction
                    print(f"[TAB1] PDF extraction successful, auto-processing...")
                    try:
                        with st.spinner("🧮 Calculating taxes..."):
                            calc_response = requests.post(
                                "http://localhost:8000/api/tax/process-with-llm",
                                json={
                                    "landingai_output": landingai_output,
                                    "filing_status": filing_status,
                                    "num_dependents": num_dependents,
                                },
                                timeout=60
                            )
                        
                        print(f"[TAB1] Auto-calc API Response Status: {calc_response.status_code}")
                        if calc_response.status_code == 200:
                            result = calc_response.json()
                            print(f"[TAB1] Auto-calc result status: {result.get('status')}")
                            st.session_state["tax_result"] = result
                            print(f"[TAB1] Auto-calc: tax_result set = {st.session_state.get('tax_result') is not None}")
                            st.success("✅ Tax calculation complete!")
                            st.info("👉 Switch to **Results** tab to see your calculation")
                        else:
                            st.warning(f"⚠️ Tax calculation failed: {calc_response.status_code}")
                    except Exception as e:
                        st.warning(f"⚠️ Calculation error: {str(e)}")
                        print(f"[TAB1] Auto-calc exception: {str(e)}")
                elif response.status_code == 403:
                    st.error("❌ Authentication Error (403): Check VISION_AGENT_API_KEY")
                    st.info("Solution: Verify API key in .env file and restart the application")
                else:
                    st.warning(f"⚠️ Processing failed ({response.status_code}). Please try again or contact support.")
                    st.info(f"Error: {response.text[:200]}")
            except requests.exceptions.Timeout:
                st.error("❌ Processing timed out. The document is taking too long to process.")
                st.info("Solution: Try a simpler PDF or try again")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        else:
            st.markdown("<p style='color: #888; text-align: center; padding: 40px;'>👆 Select a PDF file to begin</p>", unsafe_allow_html=True)


# ============================================================================
# TAB 2: MANUAL ENTRY
# ============================================================================

with tab2:
    st.header("Manual Tax Data Entry")
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("💰 Income Sources")
        w2_wages = st.number_input("W-2 Wages (Box 1)", min_value=0.0, step=100.0)
        nec_income = st.number_input("1099-NEC Income (Box 1)", min_value=0.0, step=100.0)
        interest = st.number_input("1099-INT Interest (Box 1)", min_value=0.0, step=100.0)
    
    with col2:
        st.markdown("&nbsp;")
        st.markdown("&nbsp;")
        dividends = st.number_input("1099-DIV Dividends (Box 1a)", min_value=0.0, step=100.0)
        capital_gains = st.number_input("1099-DIV Capital Gains (Box 2a)", min_value=0.0, step=100.0)
        rents = st.number_input("1099-MISC Rents (Box 1)", min_value=0.0, step=100.0)
    
    with col3:
        st.markdown("&nbsp;")
        st.markdown("&nbsp;")
        royalties = st.number_input("1099-MISC Royalties (Box 2)", min_value=0.0, step=100.0)
        fishing = st.number_input("1099-MISC Fishing (Box 5)", min_value=0.0, step=100.0)
        st.markdown("&nbsp;")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Withholding")
        fed_withheld = st.number_input("Federal Income Tax Withheld", min_value=0.0, step=100.0)
        ss_withheld = st.number_input("Social Security Tax Withheld", min_value=0.0, step=100.0)
        medicare_withheld = st.number_input("Medicare Tax Withheld", min_value=0.0, step=100.0)
    
    with col2:
        st.markdown("&nbsp;")
        st.markdown("&nbsp;")
        st.markdown("&nbsp;")
    
    # Create JSON for API
    manual_input = {
        "markdown": "Manual entry",
        "extracted_values": [],
        "key_value_pairs": {
            "Box 1 (Wages)": str(w2_wages) if w2_wages > 0 else None,
            "Box 1 (1099-NEC)": str(nec_income) if nec_income > 0 else None,
            "Box 1 (Interest)": str(interest) if interest > 0 else None,
            "Box 1 (Dividends)": str(dividends) if dividends > 0 else None,
            "Box 2a (Capital Gains)": str(capital_gains) if capital_gains > 0 else None,
            "Box 1 (Rents)": str(rents) if rents > 0 else None,
            "Box 2 (Royalties)": str(royalties) if royalties > 0 else None,
            "Box 5 (Fishing)": str(fishing) if fishing > 0 else None,
            "Federal Withheld": str(fed_withheld) if fed_withheld > 0 else None,
            "SS Withheld": str(ss_withheld) if ss_withheld > 0 else None,
            "Medicare Withheld": str(medicare_withheld) if medicare_withheld > 0 else None,
        }
    }
    
    # Remove None values
    manual_input["key_value_pairs"] = {
        k: v for k, v in manual_input["key_value_pairs"].items() if v is not None
    }
    
    # Force recompute of manual_input by storing in session state
    if "current_manual_input" not in st.session_state:
        st.session_state["current_manual_input"] = None
    
    if "calculate_clicked" not in st.session_state:
        st.session_state["calculate_clicked"] = False
    
    col_button1, col_button2 = st.columns([1, 4])
    with col_button1:
        if st.button("🧮 Calculate Taxes", type="primary", key="manual_calc_btn"):
            st.session_state["current_manual_input"] = manual_input
            st.session_state["calculate_clicked"] = True
    
    # Now process if button was clicked
    if st.session_state.get("calculate_clicked"):
        try:
            current_input = st.session_state.get("current_manual_input")
            print(f"[MANUAL] Button was clicked! Calculating with input: {current_input}")
            print(f"[MANUAL] Filing status: {filing_status}, Dependents: {num_dependents}")
            
            with st.spinner("Processing with LLM Tax Agent..."):
                response = requests.post(
                    "http://localhost:8000/api/tax/process-with-llm",
                    json={
                        "landingai_output": current_input,
                        "filing_status": filing_status,
                        "num_dependents": num_dependents,
                    },
                    timeout=60
                )
            
            print(f"[MANUAL] API Response Status: {response.status_code}")
            print(f"[MANUAL] API Response Body: {response.text[:500]}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"[MANUAL] Parsed result status: {result.get('status')}")
                print(f"[MANUAL] About to set session state...")
                st.session_state["tax_result"] = result
                print(f"[MANUAL] Session state set. tax_result = {st.session_state.get('tax_result') is not None}")
                st.session_state["calculate_clicked"] = False  # Reset flag
                st.success("✅ Tax calculation complete!")
                st.info("👉 Switch to **Results** tab to see your tax calculation")
            else:
                st.error(f"❌ API Error: {response.status_code}")
                st.error(response.text)
                st.session_state["calculate_clicked"] = False
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            print(f"[MANUAL] Exception: {str(e)}")
            st.session_state["calculate_clicked"] = False


# ============================================================================
# TAB 3: RESULTS
# ============================================================================

with tab3:
    st.header("Tax Calculation Results")
    
    tax_result_val = st.session_state.get('tax_result')
    
    if tax_result_val is None:
        st.info("ℹ️ No results yet. Process a document or enter data to calculate taxes.")
        st.info("📝 Tip: Try Tab 2 (Manual Entry) - enter $75,000 for 1099-NEC income, then click Calculate")
    else:
        result = tax_result_val
        
        if not result or (isinstance(result, dict) and result.get("status") != "success"):
            st.error(f"❌ Error: {result.get('error_message', 'Unknown error') if isinstance(result, dict) else 'Invalid result'}")
            st.json(result)
        else:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Income",
                    f"${result['income_total_income']:,.2f}",
                    delta=None,
                    delta_color="off"
                )
            
            with col2:
                st.metric(
                    "Taxable Income",
                    f"${result['taxable_income']:,.2f}",
                    delta=None,
                    delta_color="off"
                )
            
            with col3:
                st.metric(
                    "Total Tax",
                    f"${result['total_tax_liability']:,.2f}",
                    delta=None,
                    delta_color="off"
                )
            
            with col4:
                result_type = result['result_type'].upper()
                result_amount = result['result_amount']
                
                if result['result_type'] == 'Refund':
                    st.metric(
                        "💰 Refund",
                        f"${result_amount:,.2f}",
                        delta=None,
                        delta_color="off"
                    )
                elif result['result_type'] == 'Amount Due':
                    st.metric(
                        "💳 Amount Due",
                        f"${result_amount:,.2f}",
                        delta=None,
                        delta_color="off"
                    )
                else:
                    st.metric(
                        "➖ Break Even",
                        "$0.00",
                        delta=None,
                        delta_color="off"
                    )
            
            st.divider()
            
            # Detailed breakdown
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Income Breakdown")
                income_data = {
                    "W-2 Wages": result.get('income_wages', 0),
                    "1099-NEC": result.get('income_nonemployee_compensation', 0),
                    "1099-MISC Box 5 (Fishing)": result.get('income_fishing_boat_proceeds', 0),
                    "1099-INT Interest": result.get('income_interest_income', 0),
                    "1099-DIV Dividends": result.get('income_dividend_income', 0),
                    "1099-DIV Capital Gains": result.get('income_capital_gains', 0),
                    "1099-MISC Rents": result.get('income_rents', 0),
                    "1099-MISC Royalties": result.get('income_royalties', 0),
                }
                
                income_data = {k: v for k, v in income_data.items() if v > 0}
                
                if income_data:
                    income_df = pd.DataFrame(
                        list(income_data.items()),
                        columns=["Income Type", "Amount"]
                    )
                    income_df["Amount"] = income_df["Amount"].apply(lambda x: f"${x:,.2f}")
                    st.dataframe(income_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No income reported")
            
            with col2:
                st.subheader("💼 Tax Breakdown")
                tax_data = {
                    "Federal Income Tax": result.get('taxes_federal_income_tax', 0),
                    "Self-Employment Tax": result.get('taxes_self_employment_tax', 0),
                    "Total Tax": result.get('total_tax_liability', 0),
                }
                
                tax_df = pd.DataFrame(
                    list(tax_data.items()),
                    columns=["Tax Type", "Amount"]
                )
                tax_df["Amount"] = tax_df["Amount"].apply(lambda x: f"${x:,.2f}")
                st.dataframe(tax_df, use_container_width=True, hide_index=True)
            
            st.divider()
            
            # Withholding analysis
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📋 Withholding Summary")
                withholding_data = {
                    "Federal Withheld": result.get('withholding_federal_withheld', 0),
                    "SS Withheld": result.get('withholding_ss_withheld', 0),
                    "Medicare Withheld": result.get('withholding_medicare_withheld', 0),
                    "Total Withheld": result.get('withholding_total_withheld', 0),
                }
                
                with_df = pd.DataFrame(
                    list(withholding_data.items()),
                    columns=["Withholding Type", "Amount"]
                )
                with_df["Amount"] = with_df["Amount"].apply(lambda x: f"${x:,.2f}")
                st.dataframe(with_df, use_container_width=True, hide_index=True)
            
            with col2:
                st.subheader("📊 Deduction Summary")
                deduction_info = f"""
                **Deduction Type:** {result.get('deduction_type', 'Standard Deduction')}
                
                **Deduction Amount:** ${result.get('deduction_amount', 0):,.2f}
                
                **Income before deduction:** ${result.get('income_total_income', 0):,.2f}
                
                **Taxable Income:** ${result.get('taxable_income', 0):,.2f}
                """
                st.markdown(deduction_info)
            
            st.divider()
            
            # Final result box
            st.subheader("✅ Final Result")
            
            if result['result_type'] == 'Refund':
                st.success(f"""
                ### 💰 You have a **REFUND** of **${result['result_amount']:,.2f}**
                
                Your withholding ($${result.get('withholding_total_withheld', 0):,.2f}) exceeded your tax liability (${result.get('total_tax_liability', 0):,.2f}).
                """)
            elif result['result_type'] == 'Amount Due':
                st.warning(f"""
                ### 💳 You owe **${result['result_amount']:,.2f}**
                
                Your tax liability (${result.get('total_tax_liability', 0):,.2f}) exceeds your withholding ($${result.get('withholding_total_withheld', 0):,.2f}).
                """)
            else:
                st.info("""
                ### ➖ You break even
                
                Your withholding matches your tax liability exactly.
                """)
            
            st.divider()
            
            # Export options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                json_str = json.dumps(result, indent=2)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_str,
                    file_name=f"tax_calculation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            with col2:
                # Convert result dict to CSV format
                csv_lines = []
                csv_lines.append("Field,Value")
                for key, value in result.items():
                    csv_lines.append(f'"{key}","{value}"')
                csv_str = "\n".join(csv_lines)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_str,
                    file_name=f"tax_calculation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with col3:
                if st.button("🔄 Calculate Another", use_container_width=True):
                    del st.session_state["tax_result"]
                    st.rerun()


# ============================================================================
# TAB 4: HELP
# ============================================================================

with tab4:
    st.header("❓ Help & Support")
    st.markdown("---")
    
    st.subheader("📚 Getting Started")
    st.markdown("""
    1. **Upload a Document** - Go to the "Upload & Calculate" tab and select your tax form PDF
    2. **Automatic Processing** - The system will extract data and calculate taxes automatically
    3. **View Results** - Switch to the "Results" tab to see your tax calculation
    4. **Manual Entry** - Use the "Manual Entry" tab to enter values yourself
    """)
    
    st.divider()
    st.subheader("🆘 Troubleshooting")
    
    with st.expander("❓ My PDF won't upload"):
        st.markdown("""
        • Make sure it's a PDF file (not image or other format)
        • File size should be less than 10MB
        • Try uploading a clearer scan or printout
        """)
    
    with st.expander("❓ Tax calculation seems wrong"):
        st.markdown("""
        • Double-check your filing status and number of dependents in the sidebar
        • Verify all income and withholding amounts are correct
        • Check that all fields from your form were extracted properly
        """)
    
    with st.expander("❓ What forms are supported?"):
        st.markdown("""
        • W-2 (Wages and Tax Statement)
        • 1099-NEC (Nonemployee Compensation)
        • 1099-DIV (Dividends)
        • 1099-INT (Interest Income)
        • 1099-MISC (Miscellaneous Income)
        • 1099-K (Payment Card/Third Party)
        """)
    
    with st.expander("❓ How are taxes calculated?"):
        st.markdown("""
        • Uses 2024 IRS tax brackets
        • Considers filing status and dependents
        • Includes standard deduction
        • Calculates self-employment tax where applicable
        """)
    
    st.divider()
    st.subheader("📞 Contact Support")
    st.markdown("""
    For questions or issues, please contact **GreenGrowth CPAs**
    
    We're here to help! 💚
    """)

    st.header("🤖 IRS Chatbot")
    st.markdown("Ask questions about taxes, forms, deductions, and IRS rules")
    
    st.markdown("---")
    
    # Chat input
    user_question = st.text_input(
        "Ask a tax question:",
        placeholder="e.g., What are 2024 tax brackets?",
        help="Ask about tax forms, deductions, brackets, and IRS rules"
    )
    
    if st.button("🔍 Ask", type="primary", use_container_width=True):
        if user_question.strip():
            try:
                with st.spinner("🔄 Searching IRS knowledge base..."):
                    response = requests.post(
                        "http://localhost:8000/api/tax/irs-chatbot",
                        json={"question": user_question},
                        timeout=10
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Display answer
                    st.markdown("---")
                    st.subheader(result.get("title", "Answer"))
                    
                    answer_text = result.get("answer", "No information found.")
                    st.markdown(answer_text)
                    
                    # Show status
                    if result.get("status") == "success":
                        st.success("✅ Found in IRS knowledge base")
                    elif result.get("status") == "no_match":
                        st.info("ℹ️ Topic not in knowledge base. Try one of the suggested topics above.")
                        if result.get("available_topics"):
                            st.markdown("**Available topics:**")
                            for topic in result["available_topics"]:
                                st.markdown(f"- {topic}")
                else:
                    st.error(f"❌ Error: {response.status_code}")
                    st.error(response.text)
            
            except Exception as e:
                st.error(f"❌ Connection error: {str(e)}")
                st.info("Make sure the API is running on http://localhost:8000")
        else:
            st.warning("⚠️ Please enter a question")
    
    # Popular topics
    st.markdown("---")
    st.subheader("📚 Popular Topics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Tax Forms:**
        - W-2
        - 1099-NEC
        - 1099-DIV
        - 1099-INT
        
        **Tax Calculations:**
        - 2024 tax brackets
        - Standard deduction
        - Self-employment tax
        """)
    
    with col2:
        st.markdown("""
        **Common Questions:**
        - Earned income tax credit
        - Taxable vs non-taxable income
        - Form explanations
        - Tax rules and regulations
        
        **Click any button below to ask:**
        """)
    
    # Quick question buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("2024 Tax Brackets"):
            st.session_state.quick_question = "What are 2024 tax brackets?"
            st.rerun()
    
    with col2:
        if st.button("Form 1099-NEC"):
            st.session_state.quick_question = "What is Form 1099-NEC used for?"
            st.rerun()
    
    with col3:
        if st.button("Standard Deduction"):
            st.session_state.quick_question = "What is the standard deduction?"
            st.rerun()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Self-Employment Tax"):
            st.session_state.quick_question = "What is self-employment tax?"
            st.rerun()
    
    with col2:
        if st.button("Form W-2"):
            st.session_state.quick_question = "What is Form W-2?"
            st.rerun()
    
    with col3:
        if st.button("Form 1099-DIV"):
            st.session_state.quick_question = "What is Form 1099-DIV?"
            st.rerun()
    
    # Process quick question if set
    if "quick_question" in st.session_state and st.session_state.quick_question:
        try:
            with st.spinner("🔄 Searching IRS knowledge base..."):
                response = requests.post(
                    "http://localhost:8000/api/tax/irs-chatbot",
                    json={"question": st.session_state.quick_question},
                    timeout=10
                )
            
            if response.status_code == 200:
                result = response.json()
                
                st.markdown("---")
                st.subheader(result.get("title", "Answer"))
                answer_text = result.get("answer", "No information found.")
                st.markdown(answer_text)
                
                if result.get("status") == "success":
                    st.success("✅ Found in IRS knowledge base")
            
            # Clear the session variable
            del st.session_state.quick_question
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


# ============================================================================
# TAB 4: HELP
# ============================================================================

with tab4:
    st.header("❓ Help & Documentation")
    
    st.subheader("How it works")
    st.markdown("""
    1. **Upload** a tax document (W-2 or 1099 form) as PDF or paste LandingAI JSON
    2. **AI Extraction** - LandingAI automatically extracts all form fields
    3. **LLM Processing** - An intelligent LLM agent validates and processes the data
    4. **Tax Calculation** - Automatic calculation using 2024 IRS rules
    5. **Results** - Complete tax breakdown with refund or amount due
    """)
    
    st.divider()
    
    st.subheader("Supported Forms")
    st.markdown("""
    - **W-2:** Wage and Tax Statement
    - **1099-NEC:** Nonemployee Compensation
    - **1099-MISC:** Miscellaneous Income (including Box 5 fishing)
    - **1099-INT:** Interest Income
    - **1099-DIV:** Dividends and Distributions
    - **1099-K:** Payment Card Transactions
    - **1099-B:** Brokerage Statements
    """)
    
    st.divider()
    
    st.subheader("About Self-Employment Tax")
    st.markdown("""
    Self-employment (SE) tax is calculated on:
    - **1099-NEC** income (nonemployee compensation)
    - **1099-MISC Box 5** (fishing boat proceeds)
    
    **Formula:** SE Income * 0.9235 * 0.153 = SE Tax
    
    Where:
    - 0.9235 = 92.35% (portion subject to SE tax)
    - 0.153 = 15.3% (combined SS 12.4% + Medicare 2.9%)
    """)
    
    st.divider()
    
    st.subheader("2024 Tax Brackets (Single Filer)")
    bracket_data = {
        "Tax Rate": ["10%", "12%", "22%", "24%", "32%", "35%", "37%"],
        "Income Range": [
            "$0 - $11,600",
            "$11,600 - $47,150",
            "$47,150 - $100,525",
            "$100,525 - $191,950",
            "$191,950 - $243,725",
            "$243,725 - $609,350",
            "$609,350+",
        ],
    }
    st.dataframe(pd.DataFrame(bracket_data), use_container_width=True, hide_index=True)
    
    st.divider()
    
    st.subheader("Frequently Asked Questions")
    
    with st.expander("Why do I owe SE tax with no federal income tax?"):
        st.markdown("""
        SE tax is separate from income tax. Even if your income is below the standard deduction
        (so no federal tax), you still owe SE tax on self-employment income at 15.3%.
        """)
    
    with st.expander("What's the difference between 1099-NEC and 1099-MISC?"):
        st.markdown("""
        - **1099-NEC:** Nonemployee compensation (freelance work, consulting)
        - **1099-MISC:** Miscellaneous income (rents, royalties, prizes, etc.)
        
        Both can trigger SE tax, but different boxes apply.
        """)
    
    with st.expander("Do dividends trigger self-employment tax?"):
        st.markdown("""
        No. Dividends from stocks are **passive income** and do NOT trigger SE tax.
        Only 1099-NEC and 1099-MISC Box 5 (fishing) trigger SE tax.
        """)
    
    with st.expander("Can I claim my home office deduction?"):
        st.markdown("""
        Yes, but that's beyond the scope of this calculator. We only calculate gross tax liability.
        Home office deduction would reduce your SE income and thus SE tax.
        """)

"""
TAX CALCULATOR PAGE
Integrates parsed forms + personal details → Complete 2024 tax calculation
"""

import streamlit as st
import json
from datetime import datetime
from utils.tax_engine import (
    calculate_tax,
    calculate_tax_from_parsed_forms,
    normalize_extracted_data,
    STANDARD_DEDUCTION_2024
)
from utils.styles import DARK_THEME_CSS

# Set page configuration with mobile support
st.set_page_config(
    page_title="Tax Calculator",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items={"About": "2024 Tax Calculation Engine"}
)

# Apply shared dark theme
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

st.markdown("<h1 style='background: #1a1f3a; color: white !important; text-align: center; padding: 20px; border-radius: 8px; margin: 0; border: 2px solid #10b981; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);'>💰 Tax Calculator - 2024 IRS</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #10b981 !important; text-align: center; opacity: 0.9; font-size: 0.95em;'>Complete tax calculation with Form 1040 generation</p>", unsafe_allow_html=True)

# ============================================================================
# SECTION 1: VALIDATE DATA SOURCES
# ============================================================================

st.divider()
st.header("📋 Step 1: Validate Data Sources")

col1, col2 = st.columns(2)

with col1:
    st.subheader("[OK] Parsed Forms")
    if "parsed_documents" in st.session_state and st.session_state.parsed_documents:
        num_forms = len(st.session_state.parsed_documents)
        st.success(f"[OK] {num_forms} form(s) parsed and ready")
        
        # Show form summary
        for idx, doc in enumerate(st.session_state.parsed_documents, 1):
            doc_type = doc.get("document_type", "Unknown")
            extracted_fields = doc.get("result", {}).get("extracted_fields", {})
            st.caption(f"  {idx}. {doc_type}")
    else:
        st.warning("⚠ No parsed forms found. Please parse forms on the LandingAI Parse page.")

with col2:
    st.subheader("[OK] Personal Details")
    if "tax_details" in st.session_state and st.session_state.tax_details:
        tax_details = st.session_state.tax_details
        first_name = tax_details.get("first_name", "").strip()
        filing_status = tax_details.get("filing_status", "").strip()
        
        if first_name and filing_status:
            st.success(f"[OK] Details collected for {first_name}")
            st.caption(f"  Filing Status: {filing_status}")
        else:
            st.warning("⚠ Personal details incomplete.")
    else:
        st.warning("⚠ No personal details found. Please complete the Tax Details page.")

# ============================================================================
# SECTION 2: CALCULATION SETTINGS (Optional Overrides)
# ============================================================================

st.divider()
st.header("⚙ Step 2: Calculation Settings (Optional)")

calculation_mode = st.radio(
    "Select calculation mode:",
    options=["Use Personal Details", "Manual Override"],
    help="Use personal details from Tax Details page or manually override for this calculation"
)

if calculation_mode == "Manual Override":
    st.info("ℹ Manual mode: Settings below will override personal details for this calculation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        filing_status = st.selectbox(
            "Filing Status",
            options=[
                "single",
                "married_filing_jointly",
                "married_filing_separately",
                "head_of_household",
                "qualifying_widow"
            ],
            index=0
        )
        
        num_dependents = st.number_input(
            "Number of Dependents",
            min_value=0,
            max_value=20,
            value=0
        )
    
    with col2:
        deduction_type = st.radio(
            "Deduction Type",
            options=["standard", "itemized"]
        )
        
        if deduction_type == "itemized":
            itemized_amount = st.number_input(
                "Itemized Deduction Amount",
                min_value=0.0,
                step=100.0
            )
        else:
            itemized_amount = 0.0
            std_ded = STANDARD_DEDUCTION_2024.get(filing_status, 14600)
            st.caption(f"Standard Deduction: ${std_ded:,.0f}")
else:
    # Use settings from session state
    if "tax_details" in st.session_state and st.session_state.tax_details:
        tax_details = st.session_state.tax_details
        filing_status = tax_details.get("filing_status", "single").lower().replace(" ", "_")
        num_dependents = tax_details.get("num_dependents", 0)
        deduction_type = tax_details.get("deduction_type", "standard").lower()
        itemized_amount = tax_details.get("itemized_amount", 0.0) if deduction_type == "itemized" else 0.0
    else:
        filing_status = "single"
        num_dependents = 0
        deduction_type = "standard"
        itemized_amount = 0.0

# ============================================================================
# SECTION 3: CREDITS & ADJUSTMENTS
# ============================================================================

st.divider()
st.header("✨ Step 3: Credits & Adjustments")

col1, col2, col3, col4 = st.columns(4)

with col1:
    education_credits = st.number_input(
        "Education Credits",
        min_value=0.0,
        step=100.0,
        value=0.0
    )

with col2:
    earned_income_credit = st.number_input(
        "Earned Income Credit",
        min_value=0.0,
        step=100.0,
        value=0.0
    )

with col3:
    child_tax_credit = st.number_input(
        "Child Tax Credit",
        min_value=0.0,
        step=100.0,
        value=float(num_dependents * 2000)
    )

with col4:
    other_credits = st.number_input(
        "Other Credits",
        min_value=0.0,
        step=100.0,
        value=0.0
    )

# ============================================================================
# SECTION 4: CALCULATE TAX
# ============================================================================

st.divider()
st.header("🧮 Step 4: Calculate Tax")

calculate_button_col, reset_button_col = st.columns(2)

with calculate_button_col:
    calculate_clicked = st.button("🧮 Calculate Tax", type="primary", use_container_width=True)

with reset_button_col:
    if st.button("🔄 Clear Results", use_container_width=True):
        if "tax_calculation_result" in st.session_state:
            del st.session_state.tax_calculation_result
        st.rerun()

# ============================================================================
# SECTION 5: CALCULATION RESULTS
# ============================================================================

if calculate_clicked:
    # Validate data sources
    if "parsed_documents" not in st.session_state or not st.session_state.parsed_documents:
        st.error("[FAIL] No parsed forms found. Please parse forms on the LandingAI Parse page first.")
    else:
        try:
            with st.spinner("🧮 Calculating tax..."):
                # Prepare normalized documents
                parsed_forms = st.session_state.parsed_documents
                
                # Normalize each document
                normalized_docs = []
                for form in parsed_forms:
                    extracted_fields = form.get("result", {}).get("extracted_fields", {})
                    normalized = normalize_extracted_data(extracted_fields)
                    normalized_docs.append(normalized)
                
                # Calculate tax
                tax_result = calculate_tax(
                    docs=normalized_docs,
                    filing_status=filing_status,
                    num_dependents=num_dependents,
                    education_credits=education_credits,
                    child_tax_credit=child_tax_credit,
                    earned_income_credit=earned_income_credit,
                    other_credits=other_credits,
                    deduction_type=deduction_type,
                    itemized_amount=itemized_amount,
                )
                
                # Store result in session state
                st.session_state.tax_calculation_result = tax_result
                
        except Exception as e:
            st.error(f"[FAIL] Error calculating tax: {str(e)}")
            st.exception(e)

# Display results if available
if "tax_calculation_result" in st.session_state:
    result = st.session_state.tax_calculation_result
    
    st.success("[YES] Tax Calculation Complete!")
    
    # ====================================================================
    # RESULT SUMMARY - BIG CARD
    # ====================================================================
    st.divider()
    
    # Result card - large display
    refund_amount = result.get("refund_or_due", 0)
    result_type = result.get("result_type", "Unknown")
    
    if refund_amount > 0:
        color = "green"
        emoji = "🎉"
        message = f"{emoji} YOU GET A REFUND"
        bg_color = "e8f5e9"
        border_color = "4caf50"
        text_color = "2e7d32"
    elif refund_amount < 0:
        color = "red"
        emoji = "💸"
        message = f"{emoji} YOU OWE TAX"
        bg_color = "ffebee"
        border_color = "f44336"
        text_color = "c62828"
    else:
        color = "blue"
        emoji = "⚖️"
        message = f"{emoji} ZERO BALANCE"
        bg_color = "e3f2fd"
        border_color = "2196f3"
        text_color = "1565c0"
    
    html_card = f"""
        <div style="background-color: #{bg_color}; 
                    border-radius: 10px; 
                    padding: 30px; 
                    border-left: 5px solid #{border_color};
                    text-align: center;">
            <h2 style="margin: 0; color: #{text_color};">{message}</h2>
            <h1 style="margin: 10px 0 0 0; color: #{text_color}; font-size: 3em;">
                ${abs(refund_amount):,.2f}
            </h1>
        </div>
    """
    st.markdown(html_card, unsafe_allow_html=True)
    
    # ====================================================================
    # INCOME SUMMARY
    # ====================================================================
    st.divider()
    st.header("[CHART] Income Summary")
    
    income = result.get("income", {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "W-2 Wages",
            f"${income.get('wages', 0):,.2f}"
        )
    
    with col2:
        st.metric(
            "1099-NEC",
            f"${income.get('nonemployee_compensation', 0):,.2f}"
        )
    
    with col3:
        st.metric(
            "1099-INT",
            f"${income.get('interest_income', 0):,.2f}"
        )
    
    with col4:
        st.metric(
            "1099-DIV",
            f"${income.get('dividend_income', 0):,.2f}"
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Total Income",
            f"${income.get('total_income', 0):,.2f}",
            delta=None
        )
    
    with col2:
        deduction_info = result.get("deduction", {})
        st.metric(
            f"Deduction ({deduction_info.get('type', 'standard').title()})",
            f"${deduction_info.get('amount', 0):,.2f}",
            delta=None
        )
    
    # ====================================================================
    # TAX CALCULATION BREAKDOWN
    # ====================================================================
    st.divider()
    st.header("💼 Tax Calculation Breakdown")
    
    tab1, tab2, tab3 = st.tabs(["Income & Deductions", "Taxes", "Credits & Withholding"])
    
    with tab1:
        st.subheader("Taxable Income Calculation")
        
        data = {
            "Gross Income": f"${income.get('total_income', 0):,.2f}",
            "Deduction": f"-${deduction_info.get('amount', 0):,.2f}",
            "Taxable Income": f"${result.get('taxable_income', 0):,.2f}",
        }
        
        for label, value in data.items():
            st.text(f"{label:.<40} {value:>20}")
    
    with tab2:
        st.subheader("Tax Liability Calculation")
        
        taxes = result.get("taxes", {})
        
        data = {
            "Federal Income Tax": f"${taxes.get('federal_income_tax', 0):,.2f}",
            "Self-Employment Tax": f"${taxes.get('self_employment_tax', 0):,.2f}",
            "Total Tax (before credits)": f"${taxes.get('total_tax_before_credits', 0):,.2f}",
        }
        
        for label, value in data.items():
            st.text(f"{label:.<40} {value:>20}")
        
        st.divider()
        
        credits = result.get("credits", {})
        st.text(f"{'Total Credits':.<40} -${credits.get('total_credits', 0):,.2f}")
        
        st.divider()
        
        st.text(
            f"{'Total Tax Liability':.<40} ${result.get('total_tax_liability', 0):,.2f}",
            help="After all credits and adjustments"
        )
    
    with tab3:
        st.subheader("Withholding & Credits")
        
        # Withholding summary
        st.markdown("**Tax Withholding**")
        withholding = result.get("withholding", {})
        
        with_data = {
            "Federal Withholding": f"${withholding.get('federal_withheld', 0):,.2f}",
            "Social Security Withholding": f"${withholding.get('ss_withheld', 0):,.2f}",
            "Medicare Withholding": f"${withholding.get('medicare_withheld', 0):,.2f}",
            "Total Withholding": f"${withholding.get('total_withheld', 0):,.2f}",
        }
        
        for label, value in with_data.items():
            st.text(f"{label:.<40} {value:>20}")
        
        st.divider()
        
        # Credits breakdown
        st.markdown("**Tax Credits Applied**")
        
        for credit_name, credit_value in credits.items():
            if credit_name != "total_credits" and credit_value > 0:
                st.text(f"{credit_name.replace('_', ' ').title():.<40} ${credit_value:,.2f}")
        
        if credits.get("total_credits", 0) == 0:
            st.caption("No credits applied")
    
    # ====================================================================
    # REFUND VS TAX DUE
    # ====================================================================
    st.divider()
    st.header("[TARGET] Final Result")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Tax Liability",
            f"${result.get('total_tax_liability', 0):,.2f}"
        )
    
    with col2:
        st.metric(
            "Total Tax Withheld",
            f"${withholding.get('total_withheld', 0):,.2f}"
        )
    
    with col3:
        st.metric(
            result_type,
            f"${abs(refund_amount):,.2f}"
        )
    
    # ====================================================================
    # GENERATE FORM 1040 PDF
    # ====================================================================
    st.divider()
    st.markdown("---")
    st.header("📄 GENERATE FORM 1040 PDF")
    st.markdown("**Download a professional Form 1040 PDF based on your tax calculation above.**")
    
    # Define filing status mapping
    filing_status_map = {
        "single": "Single",
        "married_filing_jointly": "Married Filing Jointly",
        "married_filing_separately": "Married Filing Separately",
        "head_of_household": "Head of Household",
        "qualifying_widow": "Qualifying Widow(er)",
    }
    
    # Auto-populate from extracted data if available
    taxpayer_first = st.session_state.get("first_name", "Taxpayer")
    taxpayer_last = st.session_state.get("last_name", "")
    taxpayer_ssn = st.session_state.get("ssn", "XXX-XX-XXXX")
    
    # Try to extract personal info from parsed documents
    if "parsed_documents" in st.session_state and st.session_state.parsed_documents:
        for doc in st.session_state.parsed_documents:
            extracted = doc.get("result", {}).get("extracted_fields", {})
            if extracted:
                # Try to get name from extracted data
                if not taxpayer_first or taxpayer_first == "Taxpayer":
                    taxpayer_first = extracted.get("name", extracted.get("first_name", taxpayer_first))
                if not taxpayer_last:
                    taxpayer_last = extracted.get("last_name", taxpayer_last)
                if taxpayer_ssn == "XXX-XX-XXXX":
                    taxpayer_ssn = extracted.get("ssn", extracted.get("tax_id", taxpayer_ssn))
                break
    
    # Display extracted personal info
    st.markdown("### 📋 Personal Information from Extracted Data")
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.markdown(f"**Name:** {taxpayer_first} {taxpayer_last}")
        st.markdown(f"**SSN:** {taxpayer_ssn}")
    
    with info_col2:
        st.markdown(f"**Tax Year:** 2024")
        st.markdown(f"**Filing Status:** {filing_status_map.get(filing_status.lower(), 'Single')}")
    
    # Display tax calculation results
    st.markdown("### 💰 Tax Calculation Results")
    tax_result_col1, tax_result_col2, tax_result_col3 = st.columns(3)
    
    with tax_result_col1:
        st.metric("Total Income", f"${income.get('total_income', 0):,.2f}")
        st.metric("Deductions", f"${deduction_info.get('amount', 0):,.2f}")
    
    with tax_result_col2:
        st.metric("Taxable Income", f"${result.get('taxable_income', 0):,.2f}")
        st.metric("Total Tax", f"${result.get('total_tax_liability', 0):,.2f}")
    
    with tax_result_col3:
        st.metric("Fed. Withheld", f"${withholding.get('federal_withheld', 0):,.2f}")
        if result_type.lower() == "refund":
            st.metric("Refund Amount", f"${refund_amount:,.2f}", delta="✓", delta_color="off")
        else:
            st.metric("Amount Owed", f"${refund_amount:,.2f}", delta="!", delta_color="inverse")
    
    # Import requests for API call
    import requests
    
    # Get data for Form 1040 generation
    api_base_url = "http://localhost:8000"
    
    # Extract income components from result
    w2_wages = income.get('wages', 0.0)
    nec_income = income.get('nonemployee_compensation', 0.0)
    int_income = income.get('interest_income', 0.0)
    fed_withheld_w2 = withholding.get('federal_withheld', 0.0)
    fed_withheld_1099 = withholding.get('self_employment_tax_withheld', 0.0)
    
    if st.button("📥 Generate & Download Form 1040 PDF", use_container_width=True, type="primary", key="form_1040_btn"):
        with st.spinner("🔄 Generating Form 1040 PDF..."):
            try:
                taxpayer_filing_status = filing_status_map.get(filing_status.lower(), "Single")
                taxpayer_year = 2024
                taxpayer_dependents = num_dependents
                
                response = requests.post(
                    f"{api_base_url}/tax/generate-form-1040",
                    params={
                        "first_name": taxpayer_first,
                        "last_name": taxpayer_last,
                        "ssn": taxpayer_ssn,
                        "filing_status": taxpayer_filing_status,
                        "tax_year": int(taxpayer_year),
                        "dependent_count": int(taxpayer_dependents),
                        "w2_wages": float(w2_wages),
                        "nec_income": float(nec_income),
                        "interest_income": float(int_income),
                        "federal_withheld_w2": float(fed_withheld_w2),
                        "federal_withheld_1099": float(fed_withheld_1099),
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    st.success("✅ Form 1040 generated successfully!")
                    st.download_button(
                        label="📥 Download Form 1040 PDF",
                        data=response.content,
                        file_name=f"Form1040_{taxpayer_first}_{taxpayer_last}_{taxpayer_year}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="form_1040_download"
                    )
                else:
                    error_detail = response.json().get('detail', 'Unknown error') if response.text else 'No error details'
                    st.error(f"[FAIL] Error generating form: {error_detail}")
            
            except requests.exceptions.ConnectionError:
                st.error("[FAIL] Cannot connect to API. Please ensure the backend is running on port 8000")
            except requests.exceptions.Timeout:
                st.error("[FAIL] Form generation timed out. Please try again.")
            except Exception as e:
                st.error(f"[FAIL] Error: {str(e)}")
    
    st.markdown("---")
    st.info("ℹ️ Note: This is a demonstration form. For official tax filing, consult a tax professional or IRS e-file services.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # JSON export
        json_str = json.dumps(result, indent=2)
        st.download_button(
            label="📄 JSON Report",
            data=json_str,
            file_name=f"tax_calculation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col2:
        # Summary text export
        summary_text = f"""TAX CALCULATION SUMMARY - 2024
========================================
Filing Status: {filing_status.replace('_', ' ').title()}
Number of Dependents: {num_dependents}

INCOME SUMMARY
========================================
W-2 Wages:                ${income.get('wages', 0):>12,.2f}
1099-NEC (Self-Employment): ${income.get('nonemployee_compensation', 0):>12,.2f}
1099-INT (Interest):        ${income.get('interest_income', 0):>12,.2f}
1099-DIV (Dividends):       ${income.get('dividend_income', 0):>12,.2f}
TOTAL INCOME:             ${income.get('total_income', 0):>12,.2f}

DEDUCTIONS
========================================
{deduction_info.get('type', 'Standard').title()} Deduction: ${deduction_info.get('amount', 0):>12,.2f}
TAXABLE INCOME:           ${result.get('taxable_income', 0):>12,.2f}

TAX CALCULATION
========================================
Federal Income Tax:       ${taxes.get('federal_income_tax', 0):>12,.2f}
Self-Employment Tax:      ${taxes.get('self_employment_tax', 0):>12,.2f}
Total Tax (before credits): ${taxes.get('total_tax_before_credits', 0):>12,.2f}
Total Tax Credits:        -${credits.get('total_credits', 0):>11,.2f}
TOTAL TAX LIABILITY:      ${result.get('total_tax_liability', 0):>12,.2f}

WITHHOLDING & RESULT
========================================
Federal Tax Withheld:     ${withholding.get('federal_withheld', 0):>12,.2f}
BALANCE:
{result_type.upper()}: ${abs(refund_amount):>28,.2f}

Calculated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        st.download_button(
            label="📋 Text Report",
            data=summary_text,
            file_name=f"tax_calculation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col3:
        # CSV export (for spreadsheet import)
        csv_data = "Field,Value\n"
        
        # Flatten result for CSV
        def flatten_dict(d, parent_key=''):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}_{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key).items())
                else:
                    items.append((new_key, v))
            return dict(items)
        
        flat_result = flatten_dict(result)
        for key, value in flat_result.items():
            csv_data += f'"{key}","{value}"\n'
        
        st.download_button(
            label="[CHART] CSV Export",
            data=csv_data,
            file_name=f"tax_calculation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# ============================================================================
# HELP & INFO
# ============================================================================

st.divider()
with st.expander("ℹ️ How Tax Calculator Works"):
    st.markdown("""
    ### Tax Calculation Pipeline
    
    1. **Parse Forms** (Page 3: LandingAI Parse)
       - Upload W-2, 1099-NEC, 1099-INT, 1099-DIV forms
       - LandingAI extracts fields automatically
       - Validation ensures data quality
    
    2. **Collect Personal Details** (Page 4: Tax Details)
       - Name, SSN, DOB, contact info
       - Filing status (Single, MFJ, HOH, etc.)
       - Number of dependents
       - Deductions and credits
       - Address information
    
    3. **Calculate Tax** (This Page)
       - **Step 1**: Validate parsed forms and personal details
       - **Step 2**: Configure calculation settings
       - **Step 3**: Add credits and adjustments
       - **Step 4**: Run complete tax calculation
       - **Step 5**: Review results and export
    
    ### IRS 2024 Rules Applied
    
    [OK] Standard deductions (single: $14,600 | MFJ: $29,200 | HOH: $21,900)
    [OK] Tax brackets (10% → 37%)
    [OK] Self-employment tax on 1099-NEC (15.3%)
    [OK] Tax credits (Child Tax, EITC, Education, etc.)
    [OK] Withholding calculations
    
    ### Exports
    
    - **JSON**: Complete calculation breakdown for system integration
    - **Text**: Human-readable report for review
    - **CSV**: Spreadsheet-compatible format for analysis
    """)

st.divider()
st.caption("💡 Tax calculations based on 2024 IRS rules and rates. For audit purposes, cross-reference official IRS guidance.")

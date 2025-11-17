import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json
import os

# Page configuration
st.set_page_config(page_title="AI Tax Return Agent", layout="wide", initial_sidebar_state="expanded")

# Custom CSS
st.markdown("""
<style>
    .main-header { text-align: center; color: #1f77b4; margin-bottom: 2rem; }
    .metric-card { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .success-box { background-color: #d4edda; border-left: 4px solid #28a745; padding: 15px; border-radius: 5px; }
    .warning-box { background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; border-radius: 5px; }
    .error-box { background-color: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

st.title("🤖 AI Tax Return Agent")
st.markdown("#### Automated Tax Document Processing & Form 1040 Generation")

# API endpoint
API_BASE_URL = "http://localhost:8000"

# Initialize session state
if "current_step" not in st.session_state:
    st.session_state.current_step = 1
if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None
if "tax_calculation" not in st.session_state:
    st.session_state.tax_calculation = None

# Sidebar - Navigation
with st.sidebar:
    st.header("📋 Navigation")
    current_step = st.radio(
        "Select Step:",
        ["Step 1: Upload", "Step 2: Extract", "Step 3: Calculate"],
        label_visibility="collapsed"
    )
    
    # Map step names to numbers
    step_map = {
        "Step 1: Upload": 1,
        "Step 2: Extract": 2,
        "Step 3: Calculate": 3,
    }
    st.session_state.current_step = step_map[current_step]
    
    st.divider()
    st.subheader("[CHART] Quick Stats")
    if st.session_state.extracted_data:
        st.metric("Documents Processed", st.session_state.extracted_data.get("summary", {}).get("successful_documents", 0))
    if st.session_state.tax_calculation:
        refund = st.session_state.tax_calculation.get("final_result", {}).get("refund", 0)
        owed = st.session_state.tax_calculation.get("final_result", {}).get("amount_owed", 0)
        if refund > 0:
            st.metric("Refund Amount", f"${refund:,.2f}", delta_color="inverse")
        elif owed > 0:
            st.metric("Amount Owed", f"${owed:,.2f}")

# ==================== STEP 1: UPLOAD ====================
if st.session_state.current_step == 1:
    st.header("📁 Step 1: Upload Tax Documents")
    st.markdown("Upload PDF copies of your tax documents (W-2, 1099-NEC, 1099-INT)")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Upload Documents")
        uploaded_files = st.file_uploader(
            "Select PDF tax documents",
            type=["pdf"],
            accept_multiple_files=True,
            help="Select one or multiple PDF files"
        )
        
        if uploaded_files:
            st.success(f"[YES] {len(uploaded_files)} file(s) selected")
            with st.expander("View uploaded files", expanded=False):
                for file in uploaded_files:
                    st.write(f"📄 {file.name} ({file.size / 1024:.1f} KB)")
    
    with col2:
        st.info("💡 Supported Formats:\n- W-2\n- 1099-NEC\n- 1099-INT")
    
    st.divider()
    
    st.subheader("👤 Personal Information")
    
    col_a, col_b = st.columns(2)
    with col_a:
        first_name = st.text_input("First Name *", key="first_name_step1")
        email = st.text_input("Email *", key="email_step1")
        filing_status = st.selectbox(
            "Filing Status *",
            ["Single", "Married Filing Jointly", "Married Filing Separately", "Head of Household", "Qualifying Widow(er)"],
            key="filing_status_step1"
        )
    
    with col_b:
        last_name = st.text_input("Last Name *", key="last_name_step1")
        ssn = st.text_input("SSN (XXX-XX-XXXX) *", key="ssn_step1", type="password")
        tax_year = st.number_input("Tax Year", value=2024, min_value=2000, max_value=2025)
    
    st.divider()
    
    st.subheader("👨‍👩‍👧‍👦 Dependents")
    num_dependents = st.number_input("Number of Dependents", min_value=0, max_value=10, value=0, key="num_dependents_step1")
    
    dependents = []
    if num_dependents > 0:
        for i in range(num_dependents):
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                dep_name = st.text_input(f"Dependent {i+1} Name", key=f"dep_name_s1_{i}")
            with col_d2:
                dep_ssn = st.text_input(f"Dependent {i+1} SSN", key=f"dep_ssn_s1_{i}", type="password")
            with col_d3:
                dep_relation = st.selectbox(
                    f"Relationship {i+1}",
                    ["Child", "Parent", "Sibling", "Other"],
                    key=f"dep_relation_s1_{i}"
                )
            
            dependents.append({
                "name": dep_name,
                "ssn": dep_ssn,
                "relationship": dep_relation
            })
    
    st.divider()
    
    # Upload button
    col_btn1, col_btn2 = st.columns([3, 1])
    
    with col_btn1:
        if st.button("🚀 Process Documents", use_container_width=True, type="primary"):
            if not uploaded_files:
                st.error("[FAIL] Please upload at least one PDF document")
            elif not first_name or not last_name or not email or not ssn:
                st.error("[FAIL] Please fill in all required fields (marked with *)")
            else:
                form_data = {
                    "first_name": first_name,
                    "last_name": last_name,
                    "ssn": ssn,
                    "email": email,
                    "filing_status": filing_status,
                    "tax_year": tax_year,
                    "dependents": dependents
                }
                
                with st.spinner("📤 Uploading and processing documents..."):
                    try:
                        files = []
                        for file in uploaded_files:
                            files.append(("files", (file.name, file.getbuffer(), "application/pdf")))
                        
                        response = requests.post(
                            f"{API_BASE_URL}/tax/upload",
                            files=files,
                            data=form_data,
                            timeout=300
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.session_state.extracted_data = result
                            st.session_state.personal_info = {
                                "first_name": first_name,
                                "last_name": last_name,
                                "ssn": ssn,
                                "filing_status": filing_status,
                                "tax_year": tax_year,
                                "dependent_count": num_dependents,
                            }
                            st.success("[YES] Documents processed successfully!")
                            st.balloons()
                        else:
                            st.error(f"[FAIL] Error: {response.json().get('detail', 'Unknown error')}")
                    
                    except requests.exceptions.ConnectionError:
                        st.error("[FAIL] Cannot connect to API. Ensure backend is running on port 8000")
                    except Exception as e:
                        st.error(f"[FAIL] Error: {str(e)}")

# ==================== STEP 2: EXTRACT ====================
elif st.session_state.current_step == 2:
    st.header("[CHART] Step 2: Extracted Data Review")
    
    if not st.session_state.extracted_data:
        st.warning("[WARN] Please upload documents in Step 1 first")
    else:
        extracted = st.session_state.extracted_data
        
        # Summary
        summary = extracted.get("summary", {})
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.metric("Documents Processed", summary.get("total_documents", 0))
        with col_s2:
            st.metric("[YES] Successful", summary.get("successful_documents", 0))
        with col_s3:
            st.metric("[FAIL] Failed", summary.get("failed_documents", 0))
        
        st.divider()
        
        # Document details
        st.subheader("Document Details")
        
        for doc in extracted.get("documents", []):
            with st.expander(f"📄 {doc.get('filename', 'Unknown')} - {doc.get('document_type', 'Unknown')}", expanded=True):
                if doc.get("status") == "success":
                    extracted_data = doc.get("extracted_data", {})
                    validation = doc.get("validation", {})
                    
                    # Display Validation Report
                    if validation:
                        st.subheader("✓ Validation Report")
                        
                        # Input Validation
                        input_val = validation.get("input_validation", {})
                        if input_val:
                            with st.expander("Input Validation", expanded=True):
                                status_color = "🟢" if input_val.get("status") == "valid" else "🟡" if input_val.get("status") == "warning" else "🔴"
                                st.write(f"{status_color} **Status**: {input_val.get('status', 'unknown').upper()}")
                                for check in input_val.get("checks", []):
                                    result_icon = "✓" if check["result"] == "PASSED" else "⚠" if check["result"] == "WARNING" else "✗"
                                    st.write(f"{result_icon} **{check['check']}**: {check['result']}")
                                    st.caption(f"└─ {check['message']}")
                        
                        # Extraction Validation
                        field_val = validation.get("field_validation", {})
                        if field_val:
                            with st.expander("Extraction Validation", expanded=True):
                                col_v1, col_v2 = st.columns(2)
                                with col_v1:
                                    st.metric("Fields Extracted", field_val.get('total_fields_extracted', 0))
                                with col_v2:
                                    missing = field_val.get('missing_fields', [])
                                    st.metric("Missing Fields", len(missing) if missing else 0)
                                
                                for check in field_val.get("checks", []):
                                    result_icon = "✓" if check["result"] == "PASSED" else "⚠" if check["result"] == "PARTIAL" else "✗"
                                    st.write(f"{result_icon} **{check['check']}**: {check['result']}")
                                    st.caption(f"└─ {check['message']}")
                        
                        # Normalization Validation
                        norm_val = validation.get("normalization_validation", {})
                        if norm_val:
                            with st.expander("Normalization Validation", expanded=True):
                                col_n1, col_n2 = st.columns(2)
                                with col_n1:
                                    st.metric("Fields with Values", norm_val.get('fields_with_values', 0))
                                with col_n2:
                                    st.metric("Fields with Zero", norm_val.get('fields_with_zero', 0))
                        
                        st.divider()
                    
                    # Extracted Values
                    st.subheader("Extracted Values")
                    
                    # Create columns for different document types
                    if doc.get("document_type") == "W-2":
                        col_w1, col_w2 = st.columns(2)
                        with col_w1:
                            st.metric("Wages (Box 1)", f"${extracted_data.get('wages', 0):,.2f}")
                            st.metric("Social Security Wages (Box 3)", f"${extracted_data.get('social_security_wages', 0):,.2f}")
                        with col_w2:
                            st.metric("Fed Income Tax Withheld (Box 2)", f"${extracted_data.get('federal_income_tax_withheld', 0):,.2f}")
                            st.metric("Medicare Wages (Box 5)", f"${extracted_data.get('medicare_wages', 0):,.2f}")
                    
                    elif doc.get("document_type") == "1099-NEC":
                        col_n1, col_n2 = st.columns(2)
                        with col_n1:
                            st.metric("Nonemployee Compensation (Box 1)", f"${extracted_data.get('nonemployee_compensation', 0):,.2f}")
                        with col_n2:
                            st.metric("Fed Income Tax Withheld (Box 4)", f"${extracted_data.get('federal_income_tax_withheld', 0):,.2f}")
                    
                    elif doc.get("document_type") == "1099-INT":
                        col_i1, col_i2 = st.columns(2)
                        with col_i1:
                            st.metric("Interest Income (Box 1)", f"${extracted_data.get('interest_income', 0):,.2f}")
                        with col_i2:
                            st.metric("Fed Income Tax Withheld (Box 4)", f"${extracted_data.get('federal_income_tax_withheld', 0):,.2f}")
                    
                    st.json(extracted_data)
                
                else:
                    st.error(f"Processing failed: {doc.get('error', 'Unknown error')}")
        
        # Validation issues
        if extracted.get("validation_issues"):
            st.warning("[WARN] Validation Issues Found")
            for issue in extracted["validation_issues"]:
                st.write(f"- {issue}")
        
        if st.button("[YES] Data Looks Good - Continue to Calculation", use_container_width=True, type="primary"):
            st.session_state.current_step = 3
            st.rerun()

# ==================== STEP 3: CALCULATE ====================
elif st.session_state.current_step == 3:
    st.header("[MONEY] Step 3: Tax Calculation")
    
    if not st.session_state.extracted_data or not st.session_state.personal_info:
        st.warning("[WARN] Please complete Steps 1 and 2 first")
    else:
        # Aggregate data from extracted documents
        w2_wages = 0.0
        nec_income = 0.0
        int_income = 0.0
        fed_withheld_w2 = 0.0
        fed_withheld_1099 = 0.0
        
        for doc in st.session_state.extracted_data.get("documents", []):
            if doc.get("status") == "success":
                data = doc.get("extracted_data", {})
                if doc.get("document_type") == "W-2":
                    w2_wages += data.get("wages", 0.0)
                    fed_withheld_w2 += data.get("federal_income_tax_withheld", 0.0)
                elif doc.get("document_type") == "1099-NEC":
                    nec_income += data.get("nonemployee_compensation", 0.0)
                    fed_withheld_1099 += data.get("federal_income_tax_withheld", 0.0)
                elif doc.get("document_type") == "1099-INT":
                    int_income += data.get("interest_income", 0.0)
                    fed_withheld_1099 += data.get("federal_income_tax_withheld", 0.0)
        
        personal_info = st.session_state.personal_info
        
        st.subheader("💳 Income Summary")
        col_inc1, col_inc2, col_inc3 = st.columns(3)
        with col_inc1:
            st.metric("W-2 Wages", f"${w2_wages:,.2f}")
        with col_inc2:
            st.metric("1099-NEC Income", f"${nec_income:,.2f}")
        with col_inc3:
            st.metric("Interest Income", f"${int_income:,.2f}")
        
        st.divider()
        
        st.subheader("🧾 Withholding Summary")
        col_with1, col_with2 = st.columns(2)
        with col_with1:
            st.metric("W-2 Federal Withheld", f"${fed_withheld_w2:,.2f}")
        with col_with2:
            st.metric("1099 Federal Withheld", f"${fed_withheld_1099:,.2f}")
        
        st.divider()
        
        # Allow manual adjustments
        st.subheader("🔧 Manual Adjustments")
        col_adj1, col_adj2 = st.columns(2)
        with col_adj1:
            other_income = st.number_input("Other Income (if any)", min_value=0.0, value=0.0)
        with col_adj2:
            st.info("ℹ️ Standard deduction and credits are calculated automatically")
        
        st.divider()
        
        # Calculate button
        if st.button("🧮 Calculate Tax", use_container_width=True, type="primary"):
            with st.spinner("Calculating tax liability..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/tax/calculate",
                        params={
                            "filing_status": personal_info["filing_status"],
                            "dependent_count": personal_info["dependent_count"],
                            "w2_wages": w2_wages,
                            "nec_income": nec_income,
                            "interest_income": int_income,
                            "other_income": other_income,
                            "federal_withheld_w2": fed_withheld_w2,
                            "federal_withheld_1099": fed_withheld_1099,
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.tax_calculation = result
                        st.success("[YES] Tax calculation completed!")
                    else:
                        st.error(f"[FAIL] Error: {response.json().get('detail', 'Unknown error')}")
                
                except Exception as e:
                    st.error(f"[FAIL] Error: {str(e)}")
        
        # Display tax results if calculation complete
        if st.session_state.tax_calculation:
            st.divider()
            st.subheader("📊 Tax Calculation Results")
            
            tax_calc = st.session_state.tax_calculation
            personal = st.session_state.personal_info
            
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1:
                income_data = tax_calc.get("income", {})
                st.metric("Total Income", f"${income_data.get('total_income', 0):,.2f}")
            with col_t2:
                deductions = tax_calc.get("deductions", {})
                st.metric("Standard Deduction", f"${deductions.get('standard_deduction', 0):,.2f}")
            with col_t3:
                deductions = tax_calc.get("deductions", {})
                st.metric("Taxable Income", f"${deductions.get('taxable_income', 0):,.2f}")
            
            st.divider()
            
            col_t4, col_t5, col_t6 = st.columns(3)
            with col_t4:
                tax_info = tax_calc.get("tax_calculation", {})
                st.metric("Tax Liability", f"${tax_info.get('total_tax_liability', 0):,.2f}")
            with col_t5:
                st.metric("Total Credits", f"${tax_info.get('total_credits', 0):,.2f}")
            with col_t6:
                withheld = tax_calc.get("withholding", {})
                st.metric("Total Withheld", f"${withheld.get('total_federal_withheld', 0):,.2f}")
            
            st.divider()
            
            # Final result
            st.subheader("✨ Final Result")
            final = tax_calc.get("final_result", {})
            refund = final.get("refund", 0.0)
            owed = final.get("amount_owed", 0.0)
            
            if refund > 0:
                st.success(f"### [MONEY] REFUND DUE: ${refund:,.2f}")
            elif owed > 0:
                st.error(f"### 🏦 AMOUNT OWED: ${owed:,.2f}")
            else:
                st.info("### [YES] NO REFUND OR AMOUNT OWED")
            
            st.divider()
            st.divider()
            
            # Generate Form 1040 - Make it VERY visible
            st.markdown("---")
            st.subheader("📄 GENERATE FORM 1040 PDF")
            st.markdown("**Generate a professional Form 1040 PDF based on your tax calculation above.**")
            st.markdown("")
            
            if st.button("📥 Generate & Download Form 1040 PDF", use_container_width=True, type="primary", key="form_1040_btn"):
                with st.spinner("🔄 Generating Form 1040 PDF..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/tax/generate-form-1040",
                            params={
                                "first_name": personal["first_name"],
                                "last_name": personal["last_name"],
                                "ssn": personal["ssn"],
                                "filing_status": personal["filing_status"],
                                "tax_year": personal["tax_year"],
                                "dependent_count": personal["dependent_count"],
                                "w2_wages": w2_wages,
                                "nec_income": nec_income,
                                "interest_income": int_income,
                                "federal_withheld_w2": fed_withheld_w2,
                                "federal_withheld_1099": fed_withheld_1099,
                            },
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            st.success("✅ Form 1040 generated successfully!")
                            st.download_button(
                                label="📥 Download Form 1040 PDF",
                                data=response.content,
                                file_name=f"Form1040_{personal['first_name']}_{personal['last_name']}_{personal['tax_year']}.pdf",
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
            st.divider()
            st.info("ℹ️ Note: This is a demonstration form. For official tax filing, consult a tax professional or IRS e-file services.")



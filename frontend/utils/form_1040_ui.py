"""
Streamlit UI Component for Form 1040 Generation and Download
Integrates with the tax calculation engine to generate and preview PDFs
"""

import streamlit as st
import tempfile
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Import tax engine and form generator
import sys
sys.path.insert(0, str(Path(__file__).parent))

from form_1040_generator import Form1040Generator
from tax_engine import calculate_tax


class Form1040UI:
    """Streamlit UI for Form 1040 generation"""
    
    @staticmethod
    def render_tax_summary(tax_result: Dict[str, Any]) -> None:
        """Render tax calculation summary"""
        st.subheader("📊 Tax Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Total Income",
                f"${tax_result['income']['total_income']:,.2f}",
                delta=None,
            )
        
        with col2:
            st.metric(
                "Taxable Income",
                f"${tax_result['taxable_income']:,.2f}",
                delta=f"After ${tax_result['deduction']['amount']:,.2f} deduction",
            )
        
        with col3:
            st.metric(
                "Total Tax",
                f"${tax_result['total_tax_liability']:,.2f}",
                delta=None,
            )
        
        # Show refund/amount owed
        refund_or_due = tax_result['refund_or_due']
        result_type = tax_result['result_type']
        
        if refund_or_due > 0:
            st.success(f"💰 **REFUND: ${refund_or_due:,.2f}**", icon="✅")
        elif refund_or_due < 0:
            st.warning(f"⚠️ **AMOUNT OWED: ${abs(refund_or_due):,.2f}**", icon="⚠️")
        else:
            st.info("**Break-even: No refund or amount owed**", icon="ℹ️")
    
    @staticmethod
    def render_detailed_breakdown(tax_result: Dict[str, Any]) -> None:
        """Render detailed tax breakdown"""
        st.subheader("📋 Detailed Breakdown")
        
        # Income section
        with st.expander("💵 Income Details", expanded=True):
            income = tax_result['income']
            income_items = [
                ("Wages", income.get('wages', 0)),
                ("1099-NEC (Self-Employment)", income.get('nonemployee_compensation', 0)),
                ("Interest Income", income.get('interest_income', 0)),
                ("Dividend Income", income.get('dividend_income', 0)),
            ]
            
            for label, value in income_items:
                if value > 0:
                    st.write(f"{label}: **${value:,.2f}**")
        
        # Deduction section
        with st.expander("📊 Deductions"):
            deduction = tax_result['deduction']
            st.write(f"Type: {deduction['type'].title()}")
            st.write(f"Amount: **${deduction['amount']:,.2f}**")
        
        # Tax section
        with st.expander("🧮 Tax Calculation", expanded=True):
            taxes = tax_result['taxes']
            st.write(f"Federal Income Tax: **${taxes['federal_income_tax']:,.2f}**")
            if taxes.get('self_employment_tax', 0) > 0:
                st.write(f"Self-Employment Tax: **${taxes['self_employment_tax']:,.2f}**")
            st.write(f"**Total Tax: ${tax_result['total_tax_liability']:,.2f}**")
        
        # Credits section
        with st.expander("🎁 Tax Credits"):
            credits = tax_result['credits']
            credit_items = [
                ("Education Credits", credits.get('education_credits', 0)),
                ("Child Tax Credit", credits.get('child_tax_credit', 0)),
                ("Earned Income Credit", credits.get('earned_income_credit', 0)),
            ]
            
            for label, value in credit_items:
                if value > 0:
                    st.write(f"{label}: **${value:,.2f}**")
            
            st.write(f"**Total Credits: ${credits['total_credits']:,.2f}**")
        
        # Withholding section
        with st.expander("💼 Withholding"):
            withholding = tax_result['withholding']
            st.write(f"Federal Income Tax Withheld: **${withholding['federal_withheld']:,.2f}**")
            if withholding.get('ss_withheld', 0) > 0:
                st.write(f"Social Security Tax Withheld: **${withholding['ss_withheld']:,.2f}**")
            if withholding.get('medicare_withheld', 0) > 0:
                st.write(f"Medicare Tax Withheld: **${withholding['medicare_withheld']:,.2f}**")
            st.write(f"**Total Withheld: ${withholding['total_withheld']:,.2f}**")
    
    @staticmethod
    def render_form_1040_section(tax_result: Dict[str, Any]) -> Optional[bytes]:
        """Render Form 1040 generation section"""
        st.subheader("📄 Form 1040 Generation")
        
        # Taxpayer information form
        with st.expander("👤 Taxpayer Information", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input("First Name", value="John")
                last_name = st.text_input("Last Name", value="Doe")
            
            with col2:
                ssn = st.text_input("Social Security Number (optional)", placeholder="XXX-XX-XXXX", value="")
            
            address = st.text_input("Address", value="")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                city = st.text_input("City", value="")
            with col2:
                state = st.text_input("State", value="", max_chars=2)
            with col3:
                zip_code = st.text_input("ZIP Code", value="")
            
            taxpayer_info = {
                "first_name": first_name,
                "last_name": last_name,
                "ssn": ssn,
                "address": address,
                "city": city,
                "state": state,
                "zip": zip_code,
            }
        else:
            taxpayer_info = {
                "first_name": "John",
                "last_name": "Doe",
                "ssn": "",
                "address": "",
                "city": "",
                "state": "",
                "zip": "",
            }
        
        # Generate button
        if st.button("📋 Generate Form 1040 PDF", use_container_width=True):
            try:
                with st.spinner("Generating Form 1040..."):
                    # Create temporary file for PDF
                    temp_dir = tempfile.gettempdir()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    pdf_path = os.path.join(temp_dir, f"Form_1040_{timestamp}.pdf")
                    
                    # Generate PDF
                    generator = Form1040Generator(pdf_path)
                    generated_path = generator.create_pdf(tax_result, taxpayer_info)
                    
                    # Read PDF file
                    with open(generated_path, "rb") as f:
                        pdf_bytes = f.read()
                    
                    # Store in session state for download
                    st.session_state.form_1040_pdf = pdf_bytes
                    st.session_state.form_1040_filename = f"Form_1040_{taxpayer_info['last_name']}_{timestamp}.pdf"
                    
                    st.success("✅ Form 1040 generated successfully!")
                    
                    # Show preview
                    st.info("📥 Click the 'Download PDF' button below to save the form")
                    
                    return pdf_bytes
                    
            except Exception as e:
                st.error(f"❌ Error generating Form 1040: {str(e)}")
                return None
        
        return None
    
    @staticmethod
    def render_download_button() -> None:
        """Render download button for generated PDF"""
        if "form_1040_pdf" in st.session_state:
            pdf_bytes = st.session_state.form_1040_pdf
            filename = st.session_state.form_1040_filename
            
            st.download_button(
                label="📥 Download Form 1040 PDF",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
            )
    
    @staticmethod
    def render_full_section(tax_result: Dict[str, Any]) -> None:
        """Render complete Form 1040 section"""
        st.markdown("---")
        
        # Tax summary
        Form1040UI.render_tax_summary(tax_result)
        
        st.markdown("---")
        
        # Detailed breakdown
        Form1040UI.render_detailed_breakdown(tax_result)
        
        st.markdown("---")
        
        # Form 1040 generation
        Form1040UI.render_form_1040_section(tax_result)
        
        # Download button
        Form1040UI.render_download_button()


def render_form_1040_page(tax_result: Dict[str, Any]) -> None:
    """
    Standalone page for Form 1040 generation
    Can be used in multi-page Streamlit apps
    """
    st.set_page_config(page_title="Form 1040 Generator", layout="wide")
    
    st.title("📋 Form 1040 Generator")
    st.markdown("Generate IRS Form 1040 from your tax calculation")
    
    if tax_result:
        Form1040UI.render_full_section(tax_result)
    else:
        st.warning("⚠️ No tax calculation results available. Please calculate taxes first.")


if __name__ == "__main__":
    # Example for testing
    st.title("Form 1040 Generator - Test")
    
    # Mock tax result for testing
    mock_result = {
        "status": "success",
        "tax_year": 2024,
        "filing_status": "single",
        "num_dependents": 0,
        "income": {
            "wages": 60250.0,
            "nonemployee_compensation": 0.0,
            "interest_income": 0.0,
            "dividend_income": 0.0,
            "total_income": 60250.0,
        },
        "deduction": {
            "type": "standard",
            "amount": 14600.0,
        },
        "taxable_income": 45650.0,
        "taxes": {
            "federal_income_tax": 5246.0,
            "self_employment_tax": 0.0,
            "total_tax_before_credits": 5246.0,
        },
        "credits": {
            "education_credits": 0.0,
            "child_tax_credit": 0.0,
            "earned_income_credit": 0.0,
            "other_credits": 0.0,
            "total_credits": 0.0,
        },
        "total_tax_liability": 5246.0,
        "withholding": {
            "federal_withheld": 7200.0,
            "ss_withheld": 0.0,
            "medicare_withheld": 0.0,
            "total_withheld": 7200.0,
        },
        "refund_or_due": 1954.0,
        "result_type": "Refund",
        "result_amount": 1954.0,
        "result_status": "Refund [OK]",
    }
    
    render_form_1040_page(mock_result)

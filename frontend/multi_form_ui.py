"""
Multi-Form Extraction UI Component for Streamlit

This module provides enhanced UI components for displaying and interacting
with multi-form extraction results.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any
import json


def display_multi_form_header():
    """Display header for multi-form extraction results"""
    st.markdown("## 📋 Multi-Form Extraction Results")
    st.markdown("---")


def display_extraction_summary(result: Dict[str, Any]):
    """
    Display summary statistics of extraction results
    
    Args:
        result: Result dictionary from parse_multi()
    """
    if result["status"] != "success":
        st.error(f"[FAIL] Extraction failed: {result.get('error', 'Unknown error')}")
        return
    
    # Create metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📄 Total Pages",
            result["total_pages"],
            delta=None
        )
    
    with col2:
        st.metric(
            "📑 Forms Extracted",
            result["forms_extracted"],
            delta=None
        )
    
    with col3:
        forms = result.get("forms", [])
        avg_quality = sum(f.get("data_quality_score", 0) for f in forms) / len(forms) if forms else 0
        st.metric(
            "⭐ Avg Quality",
            f"{avg_quality:.1f}%",
            delta=None
        )
    
    with col4:
        error_count = len(result.get("extraction_errors", []))
        error_status = "[YES]" if error_count == 0 else "[WARN]"
        st.metric(
            f"{error_status} Errors",
            error_count,
            delta=None
        )


def display_forms_by_tabs(result: Dict[str, Any]):
    """
    Display each form in a separate tab
    
    Args:
        result: Result dictionary from parse_multi()
    """
    forms = result.get("forms", [])
    
    if not forms:
        st.warning("No forms were extracted from the PDF.")
        return
    
    # Create tabs for each form
    tabs = st.tabs([f"Form {i+1}: {form['document_type']}" for i, form in enumerate(forms)])
    
    for idx, (tab, form) in enumerate(zip(tabs, forms)):
        with tab:
            display_form_details(form, idx + 1)


def display_forms_by_type(result: Dict[str, Any]):
    """
    Display forms grouped by document type
    
    Args:
        result: Result dictionary from parse_multi()
    """
    forms = result.get("forms", [])
    
    if not forms:
        st.warning("No forms were extracted from the PDF.")
        return
    
    # Group forms by type
    forms_by_type = {}
    for form in forms:
        form_type = form["document_type"]
        if form_type not in forms_by_type:
            forms_by_type[form_type] = []
        forms_by_type[form_type].append(form)
    
    # Create tabs for each form type
    tab_names = [f"{f_type} ({len(forms_list)})" for f_type, forms_list in forms_by_type.items()]
    tabs = st.tabs(tab_names)
    
    for tab, (form_type, forms_list) in zip(tabs, forms_by_type.items()):
        with tab:
            st.subheader(f"{form_type} Forms ({len(forms_list)})")
            
            for idx, form in enumerate(forms_list, 1):
                with st.expander(f"📄 {form_type} - Page {form['page_number']} (Quality: {form['data_quality_score']}%)", expanded=False):
                    display_form_details(form, idx)


def display_form_details(form: Dict[str, Any], form_number: int = 1):
    """
    Display detailed information for a single form
    
    Args:
        form: Single form result from parse_multi()
        form_number: Form sequence number for display
    """
    # Form header with metadata
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.write(f"**Page:** {form['page_number']}")
    with col2:
        st.write(f"**Type:** {form['document_type']}")
    with col3:
        st.write(f"**Method:** {form['extraction_method']}")
    with col4:
        quality = form['data_quality_score']
        quality_emoji = "[YES]" if quality >= 80 else "[WARN]" if quality >= 60 else "[FAIL]"
        st.write(f"**Quality:** {quality_emoji} {quality}%")
    
    st.markdown("---")
    
    # Extracted data section
    st.markdown("### [CHART] Extracted Data")
    
    extracted_data = form.get("extracted_data", {})
    
    if not extracted_data:
        st.info("No data extracted from this form.")
    else:
        # Display as key-value pairs
        col1, col2 = st.columns(2)
        
        for idx, (key, value) in enumerate(extracted_data.items()):
            if idx % 2 == 0:
                col = col1
            else:
                col = col2
            
            with col:
                # Format the key nicely
                display_key = key.replace("_", " ").title()
                
                # Format the value
                if isinstance(value, float) and value == int(value):
                    if "income" in key.lower() or "wage" in key.lower() or "compensation" in key.lower():
                        display_value = f"${value:,.2f}"
                    else:
                        display_value = f"{int(value)}"
                elif isinstance(value, (int, float)):
                    display_value = f"{value}"
                else:
                    display_value = str(value) if value else "N/A"
                
                st.metric(display_key, display_value)
    
    # Validation issues section
    st.markdown("### [OK] Validation")
    validation_issues = form.get("validation_issues", [])
    
    if not validation_issues:
        st.success("[YES] No validation issues found")
    else:
        for issue in validation_issues:
            st.warning(f"[WARN] {issue}")
    
    # Show raw data option
    with st.expander("🔍 View Raw Data (JSON)"):
        st.json(form)


def display_forms_summary_table(result: Dict[str, Any]):
    """
    Display forms as a summary table
    
    Args:
        result: Result dictionary from parse_multi()
    """
    forms = result.get("forms", [])
    
    if not forms:
        st.warning("No forms were extracted from the PDF.")
        return
    
    st.markdown("### [CHART] Forms Summary Table")
    
    # Prepare data for table
    table_data = []
    for idx, form in enumerate(forms, 1):
        extracted_data = form.get("extracted_data", {})
        
        # Get primary income field based on form type
        income_field = "N/A"
        if form["document_type"] == "W-2":
            income = extracted_data.get("wages", 0)
            income_field = f"${income:,.2f}" if income else "N/A"
        elif form["document_type"] == "1099-NEC":
            income = extracted_data.get("nonemployee_compensation", 0)
            income_field = f"${income:,.2f}" if income else "N/A"
        elif form["document_type"] == "1099-INT":
            income = extracted_data.get("interest_income", 0)
            income_field = f"${income:,.2f}" if income else "N/A"
        
        table_data.append({
            "Form #": idx,
            "Page": form["page_number"],
            "Type": form["document_type"],
            "Method": form["extraction_method"],
            "Income": income_field,
            "Quality": f"{form['data_quality_score']:.1f}%",
            "Issues": len(form.get("validation_issues", []))
        })
    
    df = pd.DataFrame(table_data)
    
    # Display with formatting
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Quality": st.column_config.ProgressColumn(
                "Quality",
                min_value=0,
                max_value=100,
            ),
        }
    )


def display_income_summary(result: Dict[str, Any]):
    """
    Display income summary from all extracted forms
    
    Args:
        result: Result dictionary from parse_multi()
    """
    forms = result.get("forms", [])
    
    if not forms:
        return
    
    st.markdown("### [MONEY] Income Summary")
    
    # Calculate totals by form type
    w2_income = 0
    nec_income = 0
    int_income = 0
    total_tax_withheld = 0
    
    w2_count = 0
    nec_count = 0
    int_count = 0
    
    for form in forms:
        data = form.get("extracted_data", {})
        
        if form["document_type"] == "W-2":
            w2_income += data.get("wages", 0)
            total_tax_withheld += data.get("federal_income_tax_withheld", 0)
            w2_count += 1
        elif form["document_type"] == "1099-NEC":
            nec_income += data.get("nonemployee_compensation", 0)
            total_tax_withheld += data.get("federal_income_tax_withheld", 0)
            nec_count += 1
        elif form["document_type"] == "1099-INT":
            int_income += data.get("interest_income", 0)
            total_tax_withheld += data.get("federal_income_tax_withheld", 0)
            int_count += 1
    
    total_income = w2_income + nec_income + int_income
    
    # Display in columns
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Income",
            f"${total_income:,.2f}",
            delta=None
        )
    
    with col2:
        st.metric(
            "W-2 Income",
            f"${w2_income:,.2f}",
            delta=f"{w2_count} forms" if w2_count > 0 else "0 forms"
        )
    
    with col3:
        st.metric(
            "1099-NEC Income",
            f"${nec_income:,.2f}",
            delta=f"{nec_count} forms" if nec_count > 0 else "0 forms"
        )
    
    with col4:
        st.metric(
            "1099-INT Income",
            f"${int_income:,.2f}",
            delta=f"{int_count} forms" if int_count > 0 else "0 forms"
        )
    
    with col5:
        st.metric(
            "Tax Withheld",
            f"${total_tax_withheld:,.2f}",
            delta=None
        )


def display_extraction_errors(result: Dict[str, Any]):
    """
    Display any extraction errors
    
    Args:
        result: Result dictionary from parse_multi()
    """
    errors = result.get("extraction_errors", [])
    
    if not errors:
        return
    
    st.markdown("---")
    st.markdown("### [WARN] Extraction Errors")
    
    for error in errors:
        st.error(error)


def display_multi_form_results(result: Dict[str, Any], view_type: str = "tabs"):
    """
    Main function to display multi-form extraction results
    
    Args:
        result: Result dictionary from parse_multi()
        view_type: How to display forms - "tabs", "grouped", or "table"
    """
    # Display header
    display_multi_form_header()
    
    # Display summary statistics
    display_extraction_summary(result)
    
    st.markdown("")
    
    # Display view type selector
    view_options = st.radio(
        "📺 Display Format:",
        options=["Individual Forms", "Grouped by Type", "Summary Table"],
        horizontal=True
    )
    
    st.markdown("")
    
    # Display based on selected view
    if view_options == "Individual Forms":
        display_forms_by_tabs(result)
    elif view_options == "Grouped by Type":
        display_forms_by_type(result)
    else:  # Summary Table
        display_forms_summary_table(result)
    
    st.markdown("")
    
    # Display income summary
    display_income_summary(result)
    
    st.markdown("")
    
    # Display extraction errors if any
    display_extraction_errors(result)
    
    # Add download button for results
    st.markdown("---")
    st.markdown("### 📥 Export Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Download as JSON
        json_str = json.dumps(result, indent=2, default=str)
        st.download_button(
            label="📄 Download as JSON",
            data=json_str,
            file_name="extraction_results.json",
            mime="application/json"
        )
    
    with col2:
        # Download as CSV (summary table)
        forms = result.get("forms", [])
        csv_data = []
        for form in forms:
            row = {
                "Page": form["page_number"],
                "Type": form["document_type"],
                "Method": form["extraction_method"],
                "Quality": form["data_quality_score"]
            }
            # Add extracted data as columns
            row.update(form.get("extracted_data", {}))
            csv_data.append(row)
        
        df = pd.DataFrame(csv_data)
        csv_str = df.to_csv(index=False)
        
        st.download_button(
            label="[CHART] Download as CSV",
            data=csv_str,
            file_name="extraction_results.csv",
            mime="text/csv"
        )
    
    with col3:
        # Download as markdown report
        markdown_report = generate_markdown_report(result)
        st.download_button(
            label="📝 Download as Report",
            data=markdown_report,
            file_name="extraction_report.md",
            mime="text/markdown"
        )


def generate_markdown_report(result: Dict[str, Any]) -> str:
    """
    Generate a markdown report of extraction results
    
    Args:
        result: Result dictionary from parse_multi()
    
    Returns:
        Markdown formatted report
    """
    report = f"""# Multi-Form Extraction Report

## Summary
- **Total Pages:** {result["total_pages"]}
- **Forms Extracted:** {result["forms_extracted"]}
- **Extraction Status:** {result["status"]}

## Forms Extracted

"""
    
    for idx, form in enumerate(result.get("forms", []), 1):
        report += f"### Form {idx}: {form['document_type']}\n"
        report += f"- **Page:** {form['page_number']}\n"
        report += f"- **Extraction Method:** {form['extraction_method']}\n"
        report += f"- **Data Quality:** {form['data_quality_score']}%\n\n"
        
        report += "#### Extracted Data\n"
        for key, value in form.get("extracted_data", {}).items():
            formatted_key = key.replace("_", " ").title()
            if isinstance(value, float) and "income" in key.lower() or "wage" in key.lower():
                report += f"- {formatted_key}: ${value:,.2f}\n"
            else:
                report += f"- {formatted_key}: {value}\n"
        
        report += "\n"
        
        if form.get("validation_issues"):
            report += "#### Validation Issues\n"
            for issue in form["validation_issues"]:
                report += f"- {issue}\n"
            report += "\n"
    
    if result.get("extraction_errors"):
        report += "## Extraction Errors\n"
        for error in result["extraction_errors"]:
            report += f"- {error}\n"
    
    return report

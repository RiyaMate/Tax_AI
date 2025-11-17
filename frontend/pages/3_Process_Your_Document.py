import streamlit as st
import json
import csv
import io
import pandas as pd
import tempfile
from pathlib import Path
from utils.state import init_session_state
from utils.landingai_utils import landingai_parse
from utils.styles import DARK_THEME_CSS

init_session_state()

# Apply shared dark theme
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

st.markdown("<h1 style='background: #1a1f3a; color: white !important; text-align: center; padding: 20px; border-radius: 8px; margin: 0; border: 2px solid #10b981; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);'>📄 PROCESS YOUR DOCUMENT</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #10b981 !important; text-align: center; opacity: 0.9; font-size: 0.95em;'>Upload and parse your tax documents with AI</p>", unsafe_allow_html=True)

# Initialize session state for multiple documents
if "parsed_documents" not in st.session_state:
    st.session_state.parsed_documents = []
if "current_uploads" not in st.session_state:
    st.session_state.current_uploads = []

# -----------------------
# HELPER FUNCTION - Define BEFORE using
# -----------------------
def _display_parsed_document(parsed_doc):
    """Helper function to display a single parsed document"""
    result = parsed_doc['result']
    
    # Check if parsing was successful
    if result.get("status") == "error":
        st.error(f"[FAIL] Error: {result.get('error')}")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Document Type", result.get("document_type", "UNKNOWN"))
    with col2:
        extracted_fields = result.get("extracted_fields", {})
        validation = extracted_fields.get("validation", {})
        completeness = validation.get("completeness_percentage", 0)
        st.metric("Completeness", f"{completeness}%")
    
    # Display Validation Summary
    st.markdown("### [CHART] Validation Summary")
    
    if validation:
        validation_cols = st.columns(4)
        with validation_cols[0]:
            st.metric("Valid Fields", f"{validation.get('valid_fields', 0)}/{validation.get('total_fields', 0)}")
        with validation_cols[1]:
            st.metric("Data Quality", validation.get("data_quality", "N/A"))
        with validation_cols[2]:
            st.metric("Missing Required", len(validation.get("missing_required", [])))
        with validation_cols[3]:
            st.metric("Invalid Fields", len(validation.get("invalid_fields", [])))
        
        # Display validation warnings
        if validation.get("validation_warnings"):
            st.warning("[WARN] **Validation Warnings:**")
            for warning in validation["validation_warnings"]:
                st.write(f"• {warning}")
    
    # Display Extracted Fields
    st.markdown("### 📋 Extracted Fields")
    
    fields_display = {k: v for k, v in extracted_fields.items() 
                     if k not in ["validation", "document_type"]}
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Field Values")
        for field_name, field_value in fields_display.items():
            status = "[YES]" if field_value else "[WARN]"
            st.write(f"{status} **{field_name}**: {field_value or '(empty)'}")
    
    with col2:
        if validation:
            st.subheader("Field Validation Details")
            field_validation = validation.get("field_validation", {})
            
            # Handle different validation formats
            if isinstance(field_validation, dict):
                for field_name, validation_result in field_validation.items():
                    # Skip non-dict entries
                    if not isinstance(validation_result, dict):
                        continue
                    
                    status = validation_result.get("status", "UNKNOWN")
                    if status == "VALID":
                        emoji = "[YES]"
                    elif status == "MISSING_REQUIRED":
                        emoji = "[FAIL]"
                    elif status == "MISSING_OPTIONAL":
                        emoji = "[WARN]"
                    else:
                        emoji = "[WARN]"
                    
                    st.write(f"{emoji} **{field_name}**: {status}")
                    if validation_result.get("error"):
                        st.caption(f"   ↳ {validation_result['error']}")
            else:
                st.info("Validation details not available in this format")
    
    # Download Options
    st.markdown("---")
    st.markdown("### 📥 Download Report")
    
    download_cols = st.columns(3)
    
    # Download as JSON
    with download_cols[0]:
        json_str = json.dumps(extracted_fields, indent=2)
        st.download_button(
            label="📄 JSON",
            data=json_str,
            file_name=f"{result.get('document_type', 'document')}_validation_report.json",
            mime="application/json",
            use_container_width=True,
            key=f"json_{parsed_doc['filename']}"
        )
    
    # Download as CSV
    with download_cols[1]:
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer)
        
        # Write header
        csv_writer.writerow(["Field Name", "Value", "Status", "Error Message"])
        
        # Write field data
        field_validation = validation.get("field_validation", {})
        if isinstance(field_validation, dict):
            for field_name, validation_result in field_validation.items():
                # Skip non-dict entries
                if not isinstance(validation_result, dict):
                    continue
                    
                csv_writer.writerow([
                    field_name,
                    validation_result.get("value", ""),
                    validation_result.get("status", ""),
                    validation_result.get("error", "")
                ])
        
        csv_data = csv_buffer.getvalue()
        st.download_button(
            label="[CHART] CSV",
            data=csv_data,
            file_name=f"{result.get('document_type', 'document')}_validation_report.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"csv_{parsed_doc['filename']}"
        )
    
    # Download as Text Report
    with download_cols[2]:
        text_report = f"""VALIDATION REPORT
Filename: {parsed_doc['filename']}
Document Type: {result.get('document_type', 'UNKNOWN')}
Generated: {parsed_doc['timestamp']}

=== VALIDATION SUMMARY ===
Total Fields: {validation.get('total_fields', 0)}
Valid Fields: {validation.get('valid_fields', 0)}
Completeness: {validation.get('completeness_percentage', 0)}%
Data Quality: {validation.get('data_quality', 'N/A')}
Missing Required: {len(validation.get('missing_required', []))}
Invalid Fields: {len(validation.get('invalid_fields', []))}

=== EXTRACTED FIELDS ===
"""
        for field_name, field_value in fields_display.items():
            text_report += f"{field_name}: {field_value or '(empty)'}\n"
        
        text_report += f"\n=== FIELD VALIDATION DETAILS ===\n"
        field_validation = validation.get("field_validation", {})
        if isinstance(field_validation, dict):
            for field_name, validation_result in field_validation.items():
                # Skip non-dict entries
                if not isinstance(validation_result, dict):
                    continue
                    
                text_report += f"\n{field_name}:\n"
                text_report += f"  Status: {validation_result.get('status', 'UNKNOWN')}\n"
                text_report += f"  Value: {validation_result.get('value', '(empty)')}\n"
                if validation_result.get("error"):
                    text_report += f"  Error: {validation_result['error']}\n"
        
        if validation.get("validation_warnings"):
            text_report += f"\n=== WARNINGS ===\n"
            for warning in validation["validation_warnings"]:
                text_report += f"• {warning}\n"
        
        st.download_button(
            label="📝 Text",
            data=text_report,
            file_name=f"{result.get('document_type', 'document')}_validation_report.txt",
            mime="text/plain",
            use_container_width=True,
            key=f"txt_{parsed_doc['filename']}"
        )
    
    # Full JSON View (Expandable)
    with st.expander("🔍 View Full JSON Response"):
        st.json(result)
    
    # Raw Data Display
    st.markdown("---")
    st.markdown("### 📦 Raw Extracted Data")
    
    if st.button("📋 Show Raw Data", key=f"raw_data_{parsed_doc['filename']}", use_container_width=True):
        st.markdown("#### Raw LandingAI API Response")
        raw_data = result.get("raw_data", {})
        if raw_data:
            st.json(raw_data)
        else:
            st.info("No raw data available")

# -----------------------
# MAIN UI
# -----------------------

st.subheader("📤 Upload Multiple Forms")
st.info("Upload multiple PDF forms (W-2, 1099-NEC, 1099-INT, etc.) in a single session!")

# File uploader for multiple files
uploaded_files = st.file_uploader(
    "Upload PDF forms",
    type=["pdf"],
    accept_multiple_files=True,
    key="batch_uploader"
)

if uploaded_files:
    st.session_state.current_uploads = uploaded_files
    st.success(f"[YES] Ready to process {len(uploaded_files)} document(s)")

# Display current uploads
if st.session_state.current_uploads:
    st.markdown("---")
    st.subheader("📋 Documents Ready for Processing")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.write("**File Name**")
    with col2:
        st.write("**Status**")
    with col3:
        st.write("**Action**")
    
    st.divider()
    
    # Display each file with individual parse button
    for idx, pdf_file in enumerate(st.session_state.current_uploads):
        col1, col2, col3 = st.columns([2, 1, 1], vertical_alignment="center")
        
        with col1:
            st.write(f"📄 {pdf_file.name}")
        
        with col2:
            # Check if already parsed
            already_parsed = any(doc["filename"] == pdf_file.name for doc in st.session_state.parsed_documents)
            if already_parsed:
                st.success("Parsed [OK]")
            else:
                st.info("Pending")
        
        with col3:
            parse_btn = st.button(f"Parse", key=f"parse_btn_{idx}")
            if parse_btn:
                with st.spinner(f"Processing {pdf_file.name}..."):
                    # Save PDF to temp path
                    pdf_file.seek(0)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(pdf_file.read())
                        tmp_path = tmp.name
                    
                    # Parse document
                    result = landingai_parse(Path(tmp_path))
                    
                    if result and result.get("status") == "success":
                        # Store parsed document
                        parsed_doc = {
                            "filename": pdf_file.name,
                            "document_type": result.get("document_type", "UNKNOWN"),
                            "result": result,
                            "timestamp": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        # Check if document already exists and update it
                        existing_idx = next((i for i, doc in enumerate(st.session_state.parsed_documents) 
                                           if doc["filename"] == pdf_file.name), None)
                        if existing_idx is not None:
                            st.session_state.parsed_documents[existing_idx] = parsed_doc
                        else:
                            st.session_state.parsed_documents.append(parsed_doc)
                        
                        st.success(f"[YES] Successfully parsed as {result.get('document_type')}")
                        st.rerun()
                    else:
                        error_msg = result.get("error") if result else "Unknown error"
                        st.error(f"[FAIL] Error: {error_msg}")

# Display parsed documents
if st.session_state.parsed_documents:
    st.markdown("---")
    st.subheader(f"[YES] Parsed Documents ({len(st.session_state.parsed_documents)})")
    
    # Create tabs for each parsed document
    if len(st.session_state.parsed_documents) == 1:
        _display_parsed_document(st.session_state.parsed_documents[0])
    else:
        # Use tabs for multiple documents
        tab_names = [f"{doc['document_type']} - {doc['filename'][:20]}" 
                    for doc in st.session_state.parsed_documents]
        tabs = st.tabs(tab_names)
        
        for tab, parsed_doc in zip(tabs, st.session_state.parsed_documents):
            with tab:
                _display_parsed_document(parsed_doc)
    
    # Batch download section
    st.markdown("---")
    st.subheader("📥 Download All Reports")
    
    download_cols = st.columns(3)
    
    # Download all as JSON
    with download_cols[0]:
        all_json = {
            "batch_info": {
                "total_documents": len(st.session_state.parsed_documents),
                "timestamp": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                "document_types": [doc['document_type'] for doc in st.session_state.parsed_documents]
            },
            "documents": [doc['result'] for doc in st.session_state.parsed_documents]
        }
        json_str = json.dumps(all_json, indent=2)
        st.download_button(
            label="📄 All as JSON",
            data=json_str,
            file_name="batch_validation_reports.json",
            mime="application/json",
            use_container_width=True
        )
    
    # Download all as CSV
    with download_cols[1]:
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer)
        
        # Write header
        csv_writer.writerow(["Filename", "Document Type", "Valid Fields", "Total Fields", 
                           "Completeness %", "Data Quality", "Missing Required", "Invalid Fields"])
        
        # Write data for each document
        for parsed_doc in st.session_state.parsed_documents:
            extracted_fields = parsed_doc['result'].get('extracted_fields', {})
            validation = extracted_fields.get('validation', {})
            
            csv_writer.writerow([
                parsed_doc['filename'],
                parsed_doc['document_type'],
                validation.get('valid_fields', 0),
                validation.get('total_fields', 0),
                validation.get('completeness_percentage', 0),
                validation.get('data_quality', 'N/A'),
                len(validation.get('missing_required', [])),
                len(validation.get('invalid_fields', []))
            ])
        
        csv_data = csv_buffer.getvalue()
        st.download_button(
            label="[CHART] Summary as CSV",
            data=csv_data,
            file_name="batch_summary.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    # Download all as Text
    with download_cols[2]:
        text_report = f"""BATCH VALIDATION REPORT
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Documents: {len(st.session_state.parsed_documents)}

DOCUMENT TYPES:
"""
        for doc in st.session_state.parsed_documents:
            text_report += f"• {doc['document_type']} - {doc['filename']}\n"
        
        text_report += f"\n{'='*80}\n"
        
        for i, parsed_doc in enumerate(st.session_state.parsed_documents, 1):
            text_report += f"\n[DOCUMENT {i}] {parsed_doc['filename']}\n"
            text_report += f"Document Type: {parsed_doc['document_type']}\n"
            text_report += f"Timestamp: {parsed_doc['timestamp']}\n\n"
            
            extracted_fields = parsed_doc['result'].get('extracted_fields', {})
            validation = extracted_fields.get('validation', {})
            
            text_report += "VALIDATION SUMMARY:\n"
            text_report += f"  Total Fields: {validation.get('total_fields', 0)}\n"
            text_report += f"  Valid Fields: {validation.get('valid_fields', 0)}\n"
            text_report += f"  Completeness: {validation.get('completeness_percentage', 0)}%\n"
            text_report += f"  Data Quality: {validation.get('data_quality', 'N/A')}\n"
            text_report += f"  Missing Required: {len(validation.get('missing_required', []))}\n"
            text_report += f"  Invalid Fields: {len(validation.get('invalid_fields', []))}\n"
            
            text_report += "\nEXTRACTED FIELDS:\n"
            fields_display = {k: v for k, v in extracted_fields.items() 
                            if k not in ["validation", "document_type"]}
            for field_name, field_value in fields_display.items():
                text_report += f"  {field_name}: {field_value or '(empty)'}\n"
            
            text_report += f"\n{'-'*80}\n"
        
        st.download_button(
            label="📝 All as Text",
            data=text_report,
            file_name="batch_validation_reports.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    # Clear all parsed documents
    st.markdown("---")
    if st.button("🗑️ Clear All Results", use_container_width=True):
        st.session_state.parsed_documents = []
        st.session_state.current_uploads = []
        st.rerun()

else:
    if not st.session_state.current_uploads:
        st.info("👆 Upload PDF forms above to get started!")

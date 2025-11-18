"""Validation Display Helper Module."""

import streamlit as st
import json
import csv
import io
from typing import Dict, Any, List, Tuple, Optional


def get_field_status(value: Any) -> Tuple[str, str]:
    """Determine field status emoji and label based on value."""
    if value is None or value == "":
        return "[WARN]", "EMPTY"
    return "[YES]", "VALID"


def format_field_name(field_name: str) -> str:
    """Format field name for display (snake_case to Title Case)."""
    return field_name.replace("_", " ").title()


def format_field_value(value: Any, max_length: int = 100) -> str:
    """Format field value for display with proper type handling."""
    if value is None:
        return "(empty)"
    
    if isinstance(value, float):
        return f"{value:,.2f}"
    
    if isinstance(value, dict):
        return "JSON object"
    
    if isinstance(value, list):
        if len(value) == 0:
            return "(empty list)"
        return f"List with {len(value)} items"
    
    str_value = str(value)
    if len(str_value) > max_length:
        return str_value[:max_length] + "..."
    
    return str_value


def display_validation_summary(
    validation: Dict[str, Any],
    columns: int = 4
) -> None:
    """Display validation summary metrics in columns."""
    if not validation:
        # Create placeholder metrics for better UX
        cols = st.columns(columns)
        with cols[0]:
            st.metric("Valid Fields", "0/0")
        with cols[1]:
            st.metric("Data Quality", "N/A")
        with cols[2]:
            st.metric("Missing Required", 0)
        with cols[3]:
            st.metric("Invalid Fields", 0)
        return
    
    cols = st.columns(columns)
    
    # Try to extract metrics from new validation structure
    if isinstance(validation, dict):
        # NEW STRUCTURE: Multi-section validation
        if 'field_validation' in validation and 'normalization_validation' in validation:
            field_val = validation.get('field_validation', {})
            norm_val = validation.get('normalization_validation', {})
            audit = validation.get('accuracy_audit', {})
            
            total_fields = field_val.get('total_fields_extracted', 0)
            fields_with_values = norm_val.get('fields_with_values', 0)
            missing_fields = len(field_val.get('missing_fields', []))
            confidence_score = audit.get('confidence_score', 0)
            
            with cols[0]:
                st.metric("Fields Extracted", f"{fields_with_values}/{total_fields}")
            
            with cols[1]:
                quality = "EXCELLENT" if confidence_score >= 0.9 else "GOOD" if confidence_score >= 0.7 else "FAIR" if confidence_score >= 0.5 else "LOW"
                st.metric("Data Quality", quality)
            
            with cols[2]:
                st.metric("Missing Fields", missing_fields)
            
            with cols[3]:
                suspicious = len(audit.get('suspicious_fields', []))
                st.metric("Flagged Fields", suspicious)
        else:
            # OLD STRUCTURE: Try to extract metrics
            valid = validation.get('valid_fields', 0)
            total = validation.get('total_fields', validation.get('field_count', 0))
            
            with cols[0]:
                st.metric("Valid Fields", f"{valid}/{total}" if total > 0 else "0/0")
            
            with cols[1]:
                quality = validation.get('data_quality', 'N/A')
                st.metric("Data Quality", quality)
            
            with cols[2]:
                missing = validation.get('missing_required', [])
                if isinstance(missing, (list, dict)):
                    missing_count = len(missing) if isinstance(missing, list) else len(missing)
                else:
                    missing_count = 0
                st.metric("Missing Required", missing_count)
            
            with cols[3]:
                invalid = validation.get('invalid_fields', [])
                if isinstance(invalid, (list, dict)):
                    invalid_count = len(invalid) if isinstance(invalid, list) else len(invalid)
                else:
                    invalid_count = 0
                st.metric("Invalid Fields", invalid_count)


def display_extracted_fields(
    extracted_fields: Dict[str, Any],
    validation: Optional[Dict[str, Any]] = None,
    columns: int = 2,
    exclude_keys: Optional[List[str]] = None
) -> None:
    """Display extracted fields with validation status in columns."""
    if exclude_keys is None:
        exclude_keys = ['validation', 'extraction', 'extraction_method', 
                       'document_type', 'raw_fields']
    
    display_fields = {
        k: v for k, v in extracted_fields.items()
        if k not in exclude_keys
    }
    
    if not display_fields:
        st.info("No fields to display")
        return
    
    cols = st.columns(columns)
    
    with cols[0]:
        st.subheader("📊 Field Values")
        for field_name, field_value in display_fields.items():
            status, _ = get_field_status(field_value)
            formatted_name = format_field_name(field_name)
            formatted_value = format_field_value(field_value)
            st.write(f"{status} **{formatted_name}**: {formatted_value}")
    
    with cols[1]:
        st.subheader("✓ Field Validation Details")
        
        # Handle NEW validation structure with multiple validation sections
        if validation and isinstance(validation, dict):
            shown_any = False
            
            # 1. Input Validation
            if 'input_validation' in validation:
                input_val = validation['input_validation']
                if isinstance(input_val, dict):
                    status = input_val.get('status', 'unknown')
                    st.write(f"**Input Status**: {status.upper() if status else 'VALID'}")
                    shown_any = True
            
            # 2. Field Validation Summary
            if 'field_validation' in validation:
                field_val = validation['field_validation']
                if isinstance(field_val, dict):
                    total = field_val.get('total_fields_extracted', 0)
                    missing = len(field_val.get('missing_fields', []))
                    if total > 0:
                        st.write(f"**Fields Extracted**: {total}")
                        if missing > 0:
                            st.write(f"**Missing Fields**: {missing}")
                        shown_any = True
            
            # 3. Normalization Summary
            if 'normalization_validation' in validation:
                norm_val = validation['normalization_validation']
                if isinstance(norm_val, dict):
                    with_values = norm_val.get('fields_with_values', 0)
                    with_zero = norm_val.get('fields_with_zero', 0)
                    if with_values > 0 or with_zero > 0:
                        st.write(f"**Fields with Values**: {with_values}")
                        st.write(f"**Zero/Empty Fields**: {with_zero}")
                        shown_any = True
            
            # 4. Accuracy Audit
            if 'accuracy_audit' in validation:
                audit = validation['accuracy_audit']
                if isinstance(audit, dict):
                    confidence = audit.get('confidence_score', 0)
                    suspicious = len(audit.get('suspicious_fields', []))
                    if confidence >= 0:
                        st.write(f"**Confidence Score**: {confidence:.0%}")
                        shown_any = True
                    if suspicious > 0:
                        st.warning(f"⚠️ {suspicious} field(s) flagged for review")
                        shown_any = True
            
            # Fallback if no detailed sections found
            if not shown_any:
                st.write(f"**Fields Extracted**: {len(display_fields)}")
                st.write("✓ **Status**: Successfully extracted")
        else:
            # No validation - show defaults
            st.write(f"**Fields Extracted**: {len(display_fields)}")
            st.write("✓ **Status**: Successfully extracted")


def display_field_validation(field_validation: Dict[str, Any]) -> None:
    """Display individual field validation details."""
    if not isinstance(field_validation, dict):
        st.info("Validation format not recognized")
        return
    
    for field_name, validation_result in field_validation.items():
        if not isinstance(validation_result, dict):
            continue
        
        status = validation_result.get('status', 'UNKNOWN')
        
        if status == 'VALID':
            emoji = "✓"
        elif status == 'MISSING_REQUIRED':
            emoji = "✗"
        elif status == 'MISSING_OPTIONAL':
            emoji = "⚠"
        else:
            emoji = "?"
        
        formatted_name = format_field_name(field_name)
        st.write(f"{emoji} **{formatted_name}**: {status}")
        
        if validation_result.get('error'):
            st.caption(f"   ↳ {validation_result['error']}")


def display_extraction_summary(result: Dict[str, Any]) -> None:
    """Display comprehensive extraction summary with all validation info."""
    if result.get('status') == 'error':
        st.error(f"[FAIL] Error: {result.get('error')}")
        return
    
    extracted_fields = result.get("extracted_fields", {})
    validation = extracted_fields.get("validation", {})
    
    st.metric("Document Type", result.get("document_type", "UNKNOWN"))
    
    st.markdown("---")
    
    st.markdown("### [CHART] Validation Summary")
    
    # DEBUG: Log what we're getting
    with st.expander("🔍 Debug Info"):
        st.write(f"**Validation dict**: {validation}")
        st.write(f"**Validation type**: {type(validation)}")
        st.write(f"**Validation keys**: {list(validation.keys()) if isinstance(validation, dict) else 'N/A'}")
        st.write(f"**Extracted fields count**: {len([k for k in extracted_fields.keys() if k not in ['validation', 'extraction', 'extraction_method', 'document_type', 'raw_fields']])}")
    
    # Display validation summary metrics (always show, even if empty)
    display_validation_summary(validation)
    
    st.markdown("---")
    
    st.markdown("### 📋 Extracted Fields")
    display_extracted_fields(extracted_fields, validation)
    
    st.markdown("---")
    
    # Show validation warnings if present
    if validation and validation.get("validation_warnings"):
        st.warning("**⚠️ Validation Warnings:**")
        warnings = validation.get("validation_warnings", [])
        if isinstance(warnings, list):
            for warning in warnings:
                st.write(f"• {warning}")
        else:
            st.write(str(warnings))
        st.markdown("---")


def validate_extraction_result(
    result: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """Validate extraction result structure."""
    errors = []
    
    if not isinstance(result, dict):
        errors.append("Result must be a dictionary")
        return False, errors
    
    if 'status' not in result:
        errors.append("Result missing 'status' field")
    
    if result.get('status') != 'error' and 'extracted_fields' not in result:
        errors.append("Result missing 'extracted_fields' field")
    
    if 'document_type' not in result:
        errors.append("Result missing 'document_type' field")
    
    return len(errors) == 0, errors


def create_validation_report(
    result: Dict[str, Any],
    format_type: str = "text"
) -> str:
    """Create a validation report in various formats (text, json, csv)."""
    extracted_fields = result.get("extracted_fields", {})
    validation = extracted_fields.get("validation", {})
    
    if format_type == "json":
        return json.dumps(extracted_fields, indent=2, default=str)
    
    elif format_type == "csv":
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer)
        csv_writer.writerow(["Field Name", "Value", "Status", "Error Message"])
        
        field_validation = validation.get("field_validation", {})
        if isinstance(field_validation, dict):
            for field_name, validation_result in field_validation.items():
                if not isinstance(validation_result, dict):
                    continue
                
                csv_writer.writerow([
                    field_name,
                    validation_result.get("value", ""),
                    validation_result.get("status", ""),
                    validation_result.get("error", "")
                ])
        else:
            # If no field_validation, write the extracted fields
            exclude_keys = ['validation', 'extraction', 'extraction_method', 
                           'document_type', 'raw_fields']
            for field_name, field_value in extracted_fields.items():
                if field_name not in exclude_keys:
                    csv_writer.writerow([field_name, field_value, "EXTRACTED", ""])
        
        return csv_buffer.getvalue()
    
    else:  # text format
        report = f"""VALIDATION REPORT
Document Type: {result.get('document_type', 'UNKNOWN')}

=== VALIDATION SUMMARY ===
Total Fields: {validation.get('total_fields', validation.get('field_count', 0))}
Valid Fields: {validation.get('valid_fields', 0)}
Completeness: {validation.get('completeness_percentage', 0)}%
Data Quality: {validation.get('data_quality', 'N/A')}
Missing Required: {len(validation.get('missing_required', []))}
Invalid Fields: {len(validation.get('invalid_fields', []))}

=== EXTRACTED FIELDS ===
"""
        exclude_keys = ['validation', 'extraction', 'extraction_method', 
                       'document_type', 'raw_fields']
        for field_name, field_value in extracted_fields.items():
            if field_name not in exclude_keys:
                report += f"{format_field_name(field_name)}: "
                report += f"{format_field_value(field_value)}\n"
        
        return report

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
import json
import re
from pydantic import BaseModel, Field
from enum import Enum
import time

# Ensure current directory is in path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import LLM Tax Agent (PRIMARY - Best for ANY format)
try:
    from llm_tax_agent import UniversalLLMTaxAgent, LLMProvider, DocumentType as AgentDocType
    LLM_TAX_AGENT_AVAILABLE = True
    print("[OK] Universal LLM Tax Agent loaded successfully")
except ImportError as e:
    LLM_TAX_AGENT_AVAILABLE = False
    print(f"[WARNING] LLM Tax Agent not available: {e}")
except Exception as e:
    LLM_TAX_AGENT_AVAILABLE = False
    print(f"[WARNING] Failed to load LLM Tax Agent: {e}")

# Import universal markdown numeric extractor (FALLBACK 1)
try:
    from universal_markdown_numeric_extractor import (
        UniversalMarkdownNumericExtractor,
        markdown_to_tax_fields
    )
    MARKDOWN_NUMERIC_EXTRACTOR_AVAILABLE = True
    print("[OK] Universal markdown numeric extractor loaded successfully")
except ImportError as e:
    MARKDOWN_NUMERIC_EXTRACTOR_AVAILABLE = False
    print(f"[WARNING] Markdown numeric extractor not available: {e}")
except Exception as e:
    MARKDOWN_NUMERIC_EXTRACTOR_AVAILABLE = False
    print(f"[WARNING] Failed to load markdown numeric extractor: {e}")

# Import legacy universal extractor (FALLBACK)
try:
    from universal_extractor_v2 import (
        extract_from_markdown,
        convert_to_dict,
        TaxUnifiedSchema,
        EMBEDDINGS_AVAILABLE
    )
    UNIVERSAL_EXTRACTOR_AVAILABLE = True
    print("[OK] Legacy universal extractor loaded successfully")
except ImportError as e:
    UNIVERSAL_EXTRACTOR_AVAILABLE = False
    print(f"[WARNING] Legacy universal extractor not available: {e}")
except Exception as e:
    UNIVERSAL_EXTRACTOR_AVAILABLE = False
    print(f"[WARNING] Failed to load legacy universal extractor: {e}")

# Ensure environment variables are loaded
load_dotenv(override=True)

# -----------------------
# DOCUMENT TYPE ENUM
# -----------------------
class DocumentType(str, Enum):
    W2 = "W-2"
    FORM_1099_NEC = "1099-NEC"
    FORM_1099_INT = "1099-INT"
    UNKNOWN = "UNKNOWN"
# -----------------------
# TAX-SPECIFIC VALIDATION SCHEMAS
# -----------------------
# These schemas define strict validation rules for tax calculation accuracy

VALIDATION_SCHEMAS = {
    "W-2": {
        "required_fields": ["wages", "federal_income_tax_withheld"],
        "optional_fields": ["social_security_wages", "medicare_wages", "employer_ein", "employee_ssn"],
        "field_rules": {
            "wages": {
                "type": "currency",
                "min": 0,
                "max": 10000000,
                "precision": 2,
                "regex": r'^\d+\.?\d{0,2}$'
            },
            "federal_income_tax_withheld": {
                "type": "currency",
                "min": 0,
                "max": 10000000,
                "precision": 2,
                "regex": r'^\d+\.?\d{0,2}$'
            },
            "social_security_wages": {
                "type": "currency",
                "min": 0,
                "max": 10000000,
                "precision": 2,
                "regex": r'^\d+\.?\d{0,2}$'
            },
            "medicare_wages": {
                "type": "currency",
                "min": 0,
                "max": 10000000,
                "precision": 2,
                "regex": r'^\d+\.?\d{0,2}$'
            },
            "employer_ein": {
                "type": "ein",
                "regex": r'^\d{2}-\d{7}$'
            },
            "employee_ssn": {
                "type": "ssn",
                "regex": r'^\d{3}-\d{2}-\d{4}$'
            }
        }
    },
    "1099-NEC": {
        "required_fields": ["nonemployee_compensation", "federal_income_tax_withheld"],
        "optional_fields": ["payer_ein", "recipient_tin"],
        "field_rules": {
            "nonemployee_compensation": {
                "type": "currency",
                "min": 0,
                "max": 10000000,
                "precision": 2,
                "regex": r'^\d+\.?\d{0,2}$'
            },
            "federal_income_tax_withheld": {
                "type": "currency",
                "min": 0,
                "max": 10000000,
                "precision": 2,
                "regex": r'^\d+\.?\d{0,2}$'
            },
            "payer_ein": {
                "type": "ein",
                "regex": r'^\d{2}-\d{7}$'
            },
            "recipient_tin": {
                "type": "ssn",
                "regex": r'^\d{3}-\d{2}-\d{4}$'
            }
        }
    },
    "1099-INT": {
        "required_fields": ["interest_income", "federal_income_tax_withheld"],
        "optional_fields": ["payer_tin", "recipient_tin"],
        "field_rules": {
            "interest_income": {
                "type": "currency",
                "min": 0,
                "max": 10000000,
                "precision": 2,
                "regex": r'^\d+\.?\d{0,2}$'
            },
            "federal_income_tax_withheld": {
                "type": "currency",
                "min": 0,
                "max": 10000000,
                "precision": 2,
                "regex": r'^\d+\.?\d{0,2}$'
            },
            "payer_tin": {
                "type": "ein",
                "regex": r'^\d{2}-\d{7}$'
            },
            "recipient_tin": {
                "type": "ssn",
                "regex": r'^\d{3}-\d{2}-\d{4}$'
            }
        }
    }
}

# -----------------------
# VALIDATION UTILITIES
# -----------------------
def validate_field(field_name: str, field_value: any, required: bool = False) -> dict:
    """
    Validate a single field
    Returns: {"valid": bool, "value": value, "error": error_msg}
    """
    if field_value is None or field_value == "":
        if required:
            return {
                "valid": False,
                "value": field_value,
                "status": "MISSING_REQUIRED",
                "error": f"Required field '{field_name}' is missing"
            }
        else:
            return {
                "valid": True,
                "value": field_value,
                "status": "MISSING_OPTIONAL",
                "error": f"Optional field '{field_name}' is missing"
            }
    
    # Validate currency fields (should be numeric)
    if "compensation" in field_name.lower() or "wages" in field_name.lower() or "income" in field_name.lower() or "withheld" in field_name.lower():
        try:
            amount = field_value.replace(",", "")
            float(amount)
            return {
                "valid": True,
                "value": field_value,
                "status": "VALID",
                "error": None
            }
        except (ValueError, AttributeError):
            return {
                "valid": False,
                "value": field_value,
                "status": "INVALID_FORMAT",
                "error": f"Invalid currency format for '{field_name}': {field_value}"
            }
    
    # Validate EIN/TIN fields (format: XX-XXXXXXX or XXX-XX-XXXX)
    if "ein" in field_name.lower() or "tin" in field_name.lower() or "ssn" in field_name.lower():
        if not re.match(r'^\d{2}-\d{6,7}$|^\d{3}-\d{2}-\d{4}$', field_value):
            return {
                "valid": False,
                "value": field_value,
                "status": "INVALID_FORMAT",
                "error": f"Invalid EIN/TIN/SSN format for '{field_name}': {field_value}"
            }
        return {
            "valid": True,
            "value": field_value,
            "status": "VALID",
            "error": None
        }
    
    # Generic validation: non-empty string
    if isinstance(field_value, str) and len(field_value.strip()) > 0:
        return {
            "valid": True,
            "value": field_value,
            "status": "VALID",
            "error": None
        }
    
    return {
        "valid": True,
        "value": field_value,
        "status": "VALID",
        "error": None
    }

def validate_field_with_schema(field_name: str, field_value: any, field_rule: dict) -> dict:
    """
    Validate a field against specific schema rules (for tax calculation accuracy)
    Returns detailed validation result for tax purposes
    """
    if field_value is None or field_value == "":
        return {
            "valid": False,
            "value": field_value,
            "status": "MISSING",
            "error": f"Field '{field_name}' is required but missing",
            "field_type": field_rule.get("type"),
            "is_tax_critical": True
        }
    
    field_type = field_rule.get("type", "string")
    
    # Currency validation (for tax amounts)
    if field_type == "currency":
        try:
            # Remove commas and convert to float
            clean_value = str(field_value).replace(",", "").strip()
            amount = float(clean_value)
            
            # Check range
            min_val = field_rule.get("min", 0)
            max_val = field_rule.get("max", float('inf'))
            
            if amount < min_val or amount > max_val:
                return {
                    "valid": False,
                    "value": field_value,
                    "status": "OUT_OF_RANGE",
                    "error": f"Currency value {amount} outside acceptable range [{min_val}, {max_val}]",
                    "field_type": field_type,
                    "is_tax_critical": True,
                    "parsed_value": amount
                }
            
            # Check precision (cents)
            precision = field_rule.get("precision", 2)
            if amount != round(amount, precision):
                return {
                    "valid": False,
                    "value": field_value,
                    "status": "PRECISION_ERROR",
                    "error": f"Currency value has more than {precision} decimal places",
                    "field_type": field_type,
                    "is_tax_critical": True,
                    "parsed_value": amount
                }
            
            return {
                "valid": True,
                "value": field_value,
                "status": "VALID",
                "error": None,
                "field_type": field_type,
                "is_tax_critical": True,
                "parsed_value": amount
            }
        except (ValueError, AttributeError) as e:
            return {
                "valid": False,
                "value": field_value,
                "status": "INVALID_FORMAT",
                "error": f"Invalid currency format: {str(e)}",
                "field_type": field_type,
                "is_tax_critical": True
            }
    
    # EIN validation (for tax identification)
    elif field_type == "ein":
        pattern = field_rule.get("regex", r'^\d{2}-\d{7}$')
        if not re.match(pattern, str(field_value)):
            return {
                "valid": False,
                "value": field_value,
                "status": "INVALID_FORMAT",
                "error": f"EIN must be in format XX-XXXXXXX",
                "field_type": field_type,
                "is_tax_critical": True
            }
        return {
            "valid": True,
            "value": field_value,
            "status": "VALID",
            "error": None,
            "field_type": field_type,
            "is_tax_critical": True
        }
    
    # SSN validation (for taxpayer identification)
    elif field_type == "ssn":
        pattern = field_rule.get("regex", r'^\d{3}-\d{2}-\d{4}$')
        if not re.match(pattern, str(field_value)):
            return {
                "valid": False,
                "value": field_value,
                "status": "INVALID_FORMAT",
                "error": f"SSN must be in format XXX-XX-XXXX",
                "field_type": field_type,
                "is_tax_critical": True
            }
        return {
            "valid": True,
            "value": field_value,
            "status": "VALID",
            "error": None,
            "field_type": field_type,
            "is_tax_critical": True
        }
    
    # Generic string validation
    return {
        "valid": True,
        "value": field_value,
        "status": "VALID",
        "error": None,
        "field_type": field_type,
        "is_tax_critical": False
    }

def generate_validation_report(fields: dict, required_fields: list = None) -> dict:
    """
    Generate comprehensive validation report for all fields
    Returns validation summary with detailed field-by-field results
    """
    if required_fields is None:
        required_fields = []
    
    validation_results = {}
    total_fields = 0
    valid_fields = 0
    missing_required = []
    missing_optional = []
    invalid_fields = []
    
    for field_name, field_value in fields.items():
        if field_name in ["document_type", "validation"]:
            continue
        
        is_required = field_name in required_fields
        validation = validate_field(field_name, field_value, is_required)
        validation_results[field_name] = validation
        total_fields += 1
        
        if validation["status"] == "VALID":
            valid_fields += 1
            print(f"[DEBUG] [OK] {field_name}: {validation['value']} - VALID")
        elif validation["status"] == "MISSING_REQUIRED":
            missing_required.append(field_name)
            print(f"[DEBUG] [NO] {field_name}: MISSING (REQUIRED)")
        elif validation["status"] == "MISSING_OPTIONAL":
            missing_optional.append(field_name)
            print(f"[DEBUG] ○ {field_name}: MISSING (OPTIONAL)")
        elif validation["status"] == "INVALID_FORMAT":
            invalid_fields.append(field_name)
            print(f"[DEBUG] [NO] {field_name}: INVALID FORMAT - {validation['error']}")
    
    completeness = round((valid_fields / total_fields * 100), 2) if total_fields > 0 else 0
    data_quality = "EXCELLENT" if completeness == 100 else "GOOD" if completeness >= 80 else "FAIR" if completeness >= 60 else "POOR"
    
    report = {
        "total_fields": total_fields,
        "valid_fields": valid_fields,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "invalid_fields": invalid_fields,
        "completeness_percentage": completeness,
        "data_quality": data_quality,
        "field_validation": validation_results,
        "validation_warnings": []
    }
    
    # Add warnings
    if len(missing_required) > 0:
        report["validation_warnings"].append(f"[WARN] {len(missing_required)} REQUIRED field(s) missing: {', '.join(missing_required)}")
    if len(invalid_fields) > 0:
        report["validation_warnings"].append(f"[WARN] {len(invalid_fields)} field(s) have invalid format: {', '.join(invalid_fields)}")
    if len(missing_optional) > 0:
        report["validation_warnings"].append(f"ℹ️ {len(missing_optional)} optional field(s) missing: {', '.join(missing_optional)}")
    
    print(f"\n[DEBUG] ===== VALIDATION REPORT =====")
    print(f"[DEBUG] Total Fields: {total_fields}")
    print(f"[DEBUG] Valid Fields: {valid_fields}")
    print(f"[DEBUG] Completeness: {completeness}%")
    print(f"[DEBUG] Data Quality: {data_quality}")
    print(f"[DEBUG] Missing Required: {len(missing_required)}")
    print(f"[DEBUG] Invalid Format: {len(invalid_fields)}")
    print(f"[DEBUG] ================================\n")
    
    return report

def generate_tax_validation_report(fields: dict, document_type: str) -> dict:
    """
    Generate tax-specific validation report using form-specific schemas
    HIGHLY PRECISE FOR TAX CALCULATION - Each form type has strict rules
    """
    doc_type_name = document_type.replace("-", "_").upper()
    if doc_type_name == "W_2":
        doc_type_name = "W-2"
    elif doc_type_name == "1099_NEC":
        doc_type_name = "1099-NEC"
    elif doc_type_name == "1099_INT":
        doc_type_name = "1099-INT"
    
    schema = VALIDATION_SCHEMAS.get(doc_type_name)
    if not schema:
        return {
            "status": "error",
            "message": f"No validation schema defined for document type: {document_type}",
            "document_type": document_type
        }
    
    print(f"\n[DEBUG] ===== TAX VALIDATION REPORT FOR {doc_type_name} =====")
    
    validation_results = {}
    tax_critical_fields = []
    total_fields = 0
    valid_fields = 0
    missing_required = []
    missing_optional = []
    invalid_fields = []
    precision_errors = []
    out_of_range_errors = []
    
    required_fields = schema.get("required_fields", [])
    optional_fields = schema.get("optional_fields", [])
    field_rules = schema.get("field_rules", {})
    
    # Validate each field in the document
    for field_name, field_value in fields.items():
        if field_name in ["document_type", "validation"]:
            continue
        
        total_fields += 1
        
        # Get field rule if exists
        field_rule = field_rules.get(field_name, {"type": "string"})
        
        # Validate using schema
        validation = validate_field_with_schema(field_name, field_value, field_rule)
        validation_results[field_name] = validation
        
        # Track results
        is_required = field_name in required_fields
        is_tax_critical = validation.get("is_tax_critical", False)
        
        if is_tax_critical:
            tax_critical_fields.append(field_name)
        
        status = validation.get("status")
        
        if status == "VALID":
            valid_fields += 1
            print(f"[DEBUG] [YES] TAX-VALID: {field_name} = {field_value} (parsed: {validation.get('parsed_value', field_value)})")
        elif status == "MISSING":
            if is_required:
                missing_required.append(field_name)
                print(f"[DEBUG] [FAIL] TAX-CRITICAL MISSING: {field_name} (REQUIRED)")
            else:
                missing_optional.append(field_name)
                print(f"[DEBUG] [WARN] OPTIONAL MISSING: {field_name}")
        elif status == "OUT_OF_RANGE":
            out_of_range_errors.append({
                "field": field_name,
                "value": field_value,
                "error": validation.get("error")
            })
            invalid_fields.append(field_name)
            print(f"[DEBUG] [FAIL] OUT OF RANGE: {field_name} = {field_value}")
        elif status == "PRECISION_ERROR":
            precision_errors.append({
                "field": field_name,
                "value": field_value,
                "error": validation.get("error")
            })
            invalid_fields.append(field_name)
            print(f"[DEBUG] [FAIL] PRECISION ERROR: {field_name} = {field_value}")
        elif status == "INVALID_FORMAT":
            invalid_fields.append(field_name)
            print(f"[DEBUG] [FAIL] INVALID FORMAT: {field_name} = {field_value}")
    
    completeness = round((valid_fields / total_fields * 100), 2) if total_fields > 0 else 0
    
    # Tax-specific data quality assessment
    if len(missing_required) > 0 or len(precision_errors) > 0 or len(out_of_range_errors) > 0:
        tax_ready = False
        data_quality = "REJECTED"  # Cannot use for tax calculation
    elif completeness == 100:
        tax_ready = True
        data_quality = "APPROVED"  # Ready for tax calculation
    elif completeness >= 90:
        tax_ready = True
        data_quality = "APPROVED_WITH_WARNINGS"
    elif completeness >= 70:
        tax_ready = False
        data_quality = "REVIEW_REQUIRED"
    else:
        tax_ready = False
        data_quality = "INSUFFICIENT_DATA"
    
    report = {
        "status": "success",
        "document_type": document_type,
        "schema_name": doc_type_name,
        "tax_ready": tax_ready,
        "tax_quality": data_quality,
        "completeness_percentage": completeness,
        "total_fields": total_fields,
        "valid_fields": valid_fields,
        "tax_critical_fields": tax_critical_fields,
        "required_fields": required_fields,
        "optional_fields": optional_fields,
        "field_validation": validation_results,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "invalid_fields": invalid_fields,
        "precision_errors": precision_errors,
        "out_of_range_errors": out_of_range_errors,
        "validation_warnings": []
    }
    
    # Build validation warnings
    if len(missing_required) > 0:
        report["validation_warnings"].append(f"[FAIL] CRITICAL: {len(missing_required)} required field(s) missing for tax calculation: {', '.join(missing_required)}")
    if len(out_of_range_errors) > 0:
        errors_str = "; ".join([f"{e['field']}: {e['error']}" for e in out_of_range_errors])
        report["validation_warnings"].append(f"[FAIL] CRITICAL: {len(out_of_range_errors)} field(s) out of range: {errors_str}")
    if len(precision_errors) > 0:
        errors_str = "; ".join([f"{e['field']}: {e['error']}" for e in precision_errors])
        report["validation_warnings"].append(f"[WARN] WARNING: {len(precision_errors)} field(s) have precision issues: {errors_str}")
    if len(invalid_fields) > 0:
        report["validation_warnings"].append(f"[WARN] WARNING: {len(invalid_fields)} field(s) have formatting issues")
    if not tax_ready and len(missing_optional) > 0:
        report["validation_warnings"].append(f"ℹ️ INFO: {len(missing_optional)} optional field(s) missing")
    
    print(f"\n[DEBUG] TAX VALIDATION SUMMARY FOR {doc_type_name}")
    print(f"[DEBUG] Tax Ready: {tax_ready}")
    print(f"[DEBUG] Data Quality: {data_quality}")
    print(f"[DEBUG] Valid Fields: {valid_fields}/{total_fields}")
    print(f"[DEBUG] Missing Required: {len(missing_required)}")
    print(f"[DEBUG] Precision Errors: {len(precision_errors)}")
    print(f"[DEBUG] Out of Range Errors: {len(out_of_range_errors)}")
    print(f"[DEBUG] ================================\n")
    
    return report

# -----------------------
# DOCUMENT TYPE DETECTION
# -----------------------
def detect_document_type(text: str) -> DocumentType:
    """Detect document type from extracted text"""
    text_lower = text.lower()
    
    if re.search(r'w[\s-]?2|form\s+w[\s-]?2|wage\s+and\s+tax|box\s+1[\s]*wages', text_lower):
        print("[DEBUG] Detected document type: W-2")
        return DocumentType.W2
    elif re.search(r'1099[\s-]?nec|nonemployee\s+compensation|form\s+1099[\s-]?nec', text_lower):
        print("[DEBUG] Detected document type: 1099-NEC")
        return DocumentType.FORM_1099_NEC
    elif re.search(r'1099[\s-]?int|interest\s+income|form\s+1099[\s-]?int', text_lower):
        print("[DEBUG] Detected document type: 1099-INT")
        return DocumentType.FORM_1099_INT
    
    print("[DEBUG] Could not determine document type, marking as UNKNOWN")
    return DocumentType.UNKNOWN

# -----------------------
# FIELD EXTRACTION BY DOCUMENT TYPE
# -----------------------
def extract_fields_w2(text: str) -> dict:
    """
    UNIVERSAL W-2 EXTRACTOR - Format-agnostic
    Works with ANY W-2 layout (ADP, Workday, custom, etc.)
    Extracts fields using semantic matching + lookahead for values
    """
    fields = {
        "document_type": "W-2",
        "wages": None,
        "federal_income_tax_withheld": None,
        "social_security_wages": None,
        "social_security_tax_withheld": None,
        "medicare_wages": None,
        "medicare_tax_withheld": None,
        "employer_ein": None,
        "employee_ssn": None,
    }
    
    def find_value_after_label(label_pattern: str, lookahead: int = 500) -> str:
        """Find currency value immediately after a label pattern"""
        try:
            match = re.search(label_pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                start_pos = match.end()
                lookahead_text = text[start_pos:start_pos + lookahead]
                
                # Find first currency value (handle various formats)
                value_match = re.search(r'[\$]?\s*([0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?)', lookahead_text)
                if value_match:
                    return value_match.group(1)
        except:
            pass
        return None
    
    # WAGES (Box 1) - Multiple label variations
    wages_patterns = [
        r'(?:Box\s*1|^1\.?)[\s:]*(?:Wages|tips|compensation)',
        r'Wages,\s*tips,\s*other\s*(?:compensation|comp)',
        r'Wages\s+(?:and\s+tips)?',
    ]
    for pattern in wages_patterns:
        value = find_value_after_label(pattern)
        if value:
            fields["wages"] = value
            print("[DEBUG] [OK] Found wages:", fields["wages"])
            break
    if not fields["wages"]:
        print("[DEBUG] [NO] Missing field: wages (Box 1)")
    
    # FEDERAL TAX WITHHELD (Box 2) - Multiple label variations
    fed_tax_patterns = [
        r'(?:Box\s*2|^2\.?)[\s:]*(?:Federal|income)',
        r'Federal\s+(?:income\s+)?tax\s+withheld',
    ]
    for pattern in fed_tax_patterns:
        value = find_value_after_label(pattern)
        if value:
            fields["federal_income_tax_withheld"] = value
            print("[DEBUG] [OK] Found federal_income_tax_withheld:", fields["federal_income_tax_withheld"])
            break
    if not fields["federal_income_tax_withheld"]:
        print("[DEBUG] [NO] Missing field: federal_income_tax_withheld (Box 2)")
    
    # SOCIAL SECURITY WAGES (Box 3) - Multiple label variations
    ss_wages_patterns = [
        r'(?:Box\s*3|^3\.?)[\s:]*(?:Social|Security)',
        r'Social\s+Security\s+wages\s+(?:and\s+tips)?',
    ]
    for pattern in ss_wages_patterns:
        value = find_value_after_label(pattern)
        if value:
            fields["social_security_wages"] = value
            print("[DEBUG] [OK] Found social_security_wages:", fields["social_security_wages"])
            break
    if not fields["social_security_wages"]:
        print("[DEBUG] [NO] Missing field: social_security_wages (Box 3)")
    
    # SOCIAL SECURITY TAX WITHHELD (Box 4) - Multiple label variations
    ss_tax_patterns = [
        r'(?:Box\s*4|^4\.?)[\s:]*(?:Social|Security.*?tax)',
        r'Social\s+Security\s+tax\s+withheld',
    ]
    for pattern in ss_tax_patterns:
        value = find_value_after_label(pattern)
        if value:
            fields["social_security_tax_withheld"] = value
            print("[DEBUG] [OK] Found social_security_tax_withheld:", fields["social_security_tax_withheld"])
            break
    if not fields["social_security_tax_withheld"]:
        print("[DEBUG] [NO] Missing field: social_security_tax_withheld (Box 4)")
    
    # MEDICARE WAGES (Box 5) - Multiple label variations
    medicare_wages_patterns = [
        r'(?:Box\s*5|^5\.?)[\s:]*(?:Medicare)',
        r'Medicare\s+wages\s+(?:and\s+tips)?',
    ]
    for pattern in medicare_wages_patterns:
        value = find_value_after_label(pattern)
        if value:
            fields["medicare_wages"] = value
            print("[DEBUG] [OK] Found medicare_wages:", fields["medicare_wages"])
            break
    if not fields["medicare_wages"]:
        print("[DEBUG] [NO] Missing field: medicare_wages (Box 5)")
    
    # MEDICARE TAX WITHHELD (Box 6) - Multiple label variations
    medicare_tax_patterns = [
        r'(?:Box\s*6|^6\.?)[\s:]*(?:Medicare.*?tax)',
        r'Medicare\s+tax\s+withheld',
    ]
    for pattern in medicare_tax_patterns:
        value = find_value_after_label(pattern)
        if value:
            fields["medicare_tax_withheld"] = value
            print("[DEBUG] [OK] Found medicare_tax_withheld:", fields["medicare_tax_withheld"])
            break
    if not fields["medicare_tax_withheld"]:
        print("[DEBUG] [NO] Missing field: medicare_tax_withheld (Box 6)")
    
    # EMPLOYER EIN - Standard format
    ein_match = re.search(r'EIN[:\s]*(\d{2}-\d{7})', text, re.IGNORECASE)
    if ein_match:
        fields["employer_ein"] = ein_match.group(1)
        print("[DEBUG] [OK] Found employer_ein:", fields["employer_ein"])
    else:
        print("[DEBUG] [NO] Missing field: employer_ein")
    
    # EMPLOYEE SSN - Standard format
    ssn_match = re.search(r'(?:Employee\s+)?SSN[:\s]*(\d{3}-\d{2}-\d{4})', text, re.IGNORECASE)
    if ssn_match:
        fields["employee_ssn"] = ssn_match.group(1)
        print("[DEBUG] [OK] Found employee_ssn:", fields["employee_ssn"])
    else:
        print("[DEBUG] [NO] Missing field: employee_ssn")
    
    # Generate TAX-SPECIFIC validation report for W-2 (precise for tax calculation)
    tax_validation_report = generate_tax_validation_report(fields, "W-2")
    fields["validation"] = tax_validation_report
    
    return fields

def extract_fields_1099_nec(text: str) -> dict:
    """
    UNIVERSAL 1099-NEC EXTRACTOR - Format-agnostic
    Works with ANY 1099-NEC layout (ADP, Workday, custom, etc.)
    """
    fields = {
        "document_type": "1099-NEC",
        "nonemployee_compensation": None,
        "federal_income_tax_withheld": None,
        "payer_ein": None,
        "recipient_tin": None,
    }
    
    def find_value_after_label(label_pattern: str, lookahead: int = 500) -> str:
        """Find currency value immediately after a label pattern"""
        try:
            match = re.search(label_pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                start_pos = match.end()
                lookahead_text = text[start_pos:start_pos + lookahead]
                value_match = re.search(r'[\$]?\s*([0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?)', lookahead_text)
                if value_match:
                    return value_match.group(1)
        except:
            pass
        return None
    
    # NONEMPLOYEE COMPENSATION (Box 1)
    nec_patterns = [
        r'(?:Box\s*1|^1\.?)[\s:]*(?:Nonemployee|compensation)',
        r'Nonemployee\s+compensation',
    ]
    for pattern in nec_patterns:
        value = find_value_after_label(pattern)
        if value:
            fields["nonemployee_compensation"] = value
            print("[DEBUG] [OK] Found nonemployee_compensation:", fields["nonemployee_compensation"])
            break
    if not fields["nonemployee_compensation"]:
        print("[DEBUG] [NO] Missing field: nonemployee_compensation (Box 1)")
    
    # FEDERAL TAX WITHHELD (Box 4)
    fed_tax_patterns = [
        r'(?:Box\s*4|^4\.?)[\s:]*(?:Federal|tax)',
        r'Federal\s+(?:income\s+)?tax\s+withheld',
    ]
    for pattern in fed_tax_patterns:
        value = find_value_after_label(pattern)
        if value:
            fields["federal_income_tax_withheld"] = value
            print("[DEBUG] [OK] Found federal_income_tax_withheld:", fields["federal_income_tax_withheld"])
            break
    if not fields["federal_income_tax_withheld"]:
        print("[DEBUG] [NO] Missing field: federal_income_tax_withheld (Box 4)")
    
    # PAYER EIN
    payer_ein_match = re.search(r'(?:Payer.*?EIN|PAYER\s+EIN)[:\s]*(\d{2}-\d{7})', text, re.IGNORECASE)
    if payer_ein_match:
        fields["payer_ein"] = payer_ein_match.group(1)
        print("[DEBUG] [OK] Found payer_ein:", fields["payer_ein"])
    else:
        print("[DEBUG] [NO] Missing field: payer_ein")
    
    # RECIPIENT TIN
    recipient_tin_match = re.search(r'(?:Recipient.*?TIN|RECIPIENT\s+TIN)[:\s]*(\d{3}-\d{2}-\d{4})', text, re.IGNORECASE)
    if recipient_tin_match:
        fields["recipient_tin"] = recipient_tin_match.group(1)
        print("[DEBUG] [OK] Found recipient_tin:", fields["recipient_tin"])
    else:
        print("[DEBUG] [NO] Missing field: recipient_tin")
    
    # Generate TAX-SPECIFIC validation report for 1099-NEC (precise for tax calculation)
    tax_validation_report = generate_tax_validation_report(fields, "1099-NEC")
    fields["validation"] = tax_validation_report
    
    return fields

def extract_fields_1099_int(text: str) -> dict:
    """
    UNIVERSAL 1099-INT EXTRACTOR - Format-agnostic
    Works with ANY 1099-INT layout (ADP, Workday, custom, etc.)
    """
    fields = {
        "document_type": "1099-INT",
        "interest_income": None,
        "federal_income_tax_withheld": None,
        "payer_tin": None,
        "recipient_tin": None,
    }
    
    def find_value_after_label(label_pattern: str, lookahead: int = 500) -> str:
        """Find currency value immediately after a label pattern"""
        try:
            match = re.search(label_pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                start_pos = match.end()
                lookahead_text = text[start_pos:start_pos + lookahead]
                value_match = re.search(r'[\$]?\s*([0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?)', lookahead_text)
                if value_match:
                    return value_match.group(1)
        except:
            pass
        return None
    
    # INTEREST INCOME (Box 1)
    interest_patterns = [
        r'(?:Box\s*1|^1\.?)[\s:]*(?:Interest|income)',
        r'Interest\s+income',
    ]
    for pattern in interest_patterns:
        value = find_value_after_label(pattern)
        if value:
            fields["interest_income"] = value
            print("[DEBUG] [OK] Found interest_income:", fields["interest_income"])
            break
    if not fields["interest_income"]:
        print("[DEBUG] [NO] Missing field: interest_income (Box 1)")
    
    # FEDERAL TAX WITHHELD (Box 4)
    fed_tax_patterns = [
        r'(?:Box\s*4|^4\.?)[\s:]*(?:Federal|tax)',
        r'Federal\s+(?:income\s+)?tax\s+withheld',
    ]
    for pattern in fed_tax_patterns:
        value = find_value_after_label(pattern)
        if value:
            fields["federal_income_tax_withheld"] = value
            print("[DEBUG] [OK] Found federal_income_tax_withheld:", fields["federal_income_tax_withheld"])
            break
    if not fields["federal_income_tax_withheld"]:
        print("[DEBUG] [NO] Missing field: federal_income_tax_withheld (Box 4)")
    
    # PAYER TIN
    payer_tin_match = re.search(r'(?:Payer.*?TIN|PAYER\s+TIN)[:\s]*(\d{2}-\d{7})', text, re.IGNORECASE)
    if payer_tin_match:
        fields["payer_tin"] = payer_tin_match.group(1)
        print("[DEBUG] [OK] Found payer_tin:", fields["payer_tin"])
    else:
        print("[DEBUG] [NO] Missing field: payer_tin")
    
    # RECIPIENT TIN
    recipient_tin_match = re.search(r'(?:Recipient.*?TIN|RECIPIENT\s+TIN)[:\s]*(\d{3}-\d{2}-\d{4})', text, re.IGNORECASE)
    if recipient_tin_match:
        fields["recipient_tin"] = recipient_tin_match.group(1)
        print("[DEBUG] [OK] Found recipient_tin:", fields["recipient_tin"])
    else:
        print("[DEBUG] [NO] Missing field: recipient_tin")
    
    # Generate TAX-SPECIFIC validation report for 1099-INT (precise for tax calculation)
    tax_validation_report = generate_tax_validation_report(fields, "1099-INT")
    fields["validation"] = tax_validation_report
    
    return fields

def extract_document_fields(text: str, doc_type: DocumentType) -> dict:
    """
    UNIVERSAL EXTRACTION INTERFACE
    
    Priority:
    1. LLM Tax Agent (Best for ANY format - handles messy OCR, tables, text)
    2. Pure Markdown Numeric Extractor (Fast, zero-schema)
    3. Legacy Universal Extractor (Hybrid semantic matching) 
    4. Legacy regex extractors (Final fallback)
    """
    
    # Map DocumentType to string
    doc_type_str = None
    if doc_type == DocumentType.W2:
        doc_type_str = "W-2"
    elif doc_type == DocumentType.FORM_1099_NEC:
        doc_type_str = "1099-NEC"
    elif doc_type == DocumentType.FORM_1099_INT:
        doc_type_str = "1099-INT"
    
    print(f"[EXTRACTION] Processing {doc_type_str}...")
    
    # ========================================================================
    # ONLY LLM TAX AGENT - NO FALLBACKS
    # ========================================================================
    if not LLM_TAX_AGENT_AVAILABLE:
        raise RuntimeError("[ERROR] LLM Tax Agent not available. Required for universal extraction.")
    
    print(f"[LLM] Using LLM Tax Agent (universal extraction)...")
    
    try:
        # Use LLM to extract from any format
        agent = UniversalLLMTaxAgent(llm_provider=LLMProvider.GEMINI)
        agent_result = agent.process_document(text)
        
        normalized = agent_result.get("normalized_fields", {})
        validation = agent_result.get("validation", {})
        extraction = agent_result.get("extraction", {})
        print(f"[LLM] Extraction successful")
        
        # Debug: Log what we got
        print(f"[DEBUG] Normalized fields count: {len(normalized)}")
        print(f"[DEBUG] Fields with values: {sum(1 for v in normalized.values() if v > 0)}")
        for key, value in normalized.items():
            if value > 0:
                print(f"[DEBUG]   {key}: {value}")
        
        # Convert to document-specific format
        if doc_type == DocumentType.W2:
            result = {
                "document_type": "W-2",
                "wages": normalized.get("wages", 0.0) or 0.0,
                "federal_income_tax_withheld": normalized.get("federal_income_tax_withheld", 0.0) or 0.0,
                "social_security_wages": normalized.get("social_security_wages", 0.0) or 0.0,
                "social_security_tax_withheld": normalized.get("social_security_tax_withheld", 0.0) or 0.0,
                "medicare_wages": normalized.get("medicare_wages", 0.0) or 0.0,
                "medicare_tax_withheld": normalized.get("medicare_tax_withheld", 0.0) or 0.0,
                "state_income_tax_withheld": normalized.get("state_income_tax_withheld", 0.0) or 0.0,
                "extraction_method": "llm_agent",
                "validation": validation,
                "extraction": extraction,
            }
            return result
        elif doc_type == DocumentType.FORM_1099_NEC:
            result = {
                "document_type": "1099-NEC",
                "nonemployee_compensation": normalized.get("nonemployee_compensation", 0.0) or 0.0,
                "federal_income_tax_withheld": normalized.get("federal_income_tax_withheld", 0.0) or 0.0,
                "extraction_method": "llm_agent",
                "validation": validation,
                "extraction": extraction,
            }
            return result
        elif doc_type == DocumentType.FORM_1099_INT:
            result = {
                "document_type": "1099-INT",
                "interest_income": normalized.get("interest_income", 0.0) or 0.0,
                "federal_income_tax_withheld": normalized.get("federal_income_tax_withheld", 0.0) or 0.0,
                "extraction_method": "llm_agent",
                "validation": validation,
                "extraction": extraction,
            }
            return result
        else:
            result = {
                "document_type": "UNKNOWN",
                "extraction_method": "llm_agent",
                "extracted_data": normalized,
                "validation": validation,
                "extraction": extraction,
            }
            return result
    except Exception as e:
        print(f"[LLM] Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"[ERROR] LLM extraction failed: {e}")


# -----------------------
# VERIFY API KEY
# -----------------------
def check_landingai_key():
    api = os.getenv("VISION_AGENT_API_KEY")
    if api:
        api = api.strip()
    return bool(api)

# -----------------------
# GET API KEY
# -----------------------
def get_api_key():
    api = os.getenv("VISION_AGENT_API_KEY")
    if api:
        api = api.strip()
    if not api:
        print(f"[DEBUG] API key is missing or empty")
        return None

    print(f"[DEBUG] Using LandingAI API key: {api[:50]}... (length: {len(api)})")
    return api

# -----------------------
# SCHEMAS
# -----------------------
class DocumentMetadata(BaseModel):
    title: str = Field(description="Document title")
    author: str = Field(description="Document author")
    creation_date: str = Field(description="Document creation date")

class Person(BaseModel):
    name: str = Field(description="Full name")
    age: int = Field(description="Age")

class CompanyInfo(BaseModel):
    company_name: str = Field(description="Name of company")
    address: str = Field(description="Company address")

schema_map = {
    "metadata": DocumentMetadata,
    "person": Person,
    "company": CompanyInfo
}

# -----------------------
# PARSE DOCUMENT (REST API)
# -----------------------
# -----------------------
# SCHEMA EXTRACTION (REST API)
# -----------------------
def _api_call_with_retry(url, headers, files=None, data=None, max_retries=3, timeout=300):
    """
    Make API call with retry logic for network timeouts.
    
    Args:
        url: API endpoint
        headers: Request headers
        files: Files to upload
        data: Data payload
        max_retries: Number of retries on timeout
        timeout: Request timeout in seconds (default 300 = 5 minutes)
    
    Returns:
        Response object if successful, None if failed
    """
    for attempt in range(max_retries):
        try:
            print(f"[INFO] API call attempt {attempt + 1}/{max_retries} to {url}")
            response = requests.post(
                url,
                headers=headers,
                files=files,
                data=data,
                timeout=timeout
            )
            print(f"[DEBUG] Response status: {response.status_code}")
            return response
        
        except requests.exceptions.Timeout as e:
            print(f"[WARN] Timeout on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)  # Exponential backoff: 5s, 10s, 15s
                print(f"[INFO] Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"[FAIL] Max retries exceeded for timeout")
                raise
        
        except requests.exceptions.ConnectionError as e:
            print(f"[WARN] Connection error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)
                print(f"[INFO] Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"[FAIL] Max retries exceeded for connection error")
                raise

def landingai_parse(path):
    api_key = get_api_key()
    if not api_key:
        return {"status": "error", "error": "LandingAI key missing"}

    try:
        # Convert string path to Path object if necessary
        if isinstance(path, str):
            path = Path(path)
        
        print(f"[DEBUG] Parsing document: {path}")
        print(f"[DEBUG] File exists: {path.exists()}")
        print(f"[DEBUG] File size: {path.stat().st_size if path.exists() else 'N/A'} bytes")
        
        # Use LandingAI ADE parse REST API endpoint
        url = "https://api.va.landing.ai/v1/ade/parse"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        with open(path, "rb") as f:
            files = {
                "document": f,
                "model": (None, "dpt-2-latest")
            }
            print(f"[DEBUG] Sending request to {url}")
            # Use 300 second (5 minute) timeout for parsing large documents
            response = _api_call_with_retry(url, headers, files=files, timeout=300)
        
        print(f"[DEBUG] Response status: {response.status_code}")
        print(f"[DEBUG] Response body: {response.text[:500]}")
        
        if response.status_code != 200:
            return {
                "status": "error",
                "error": f"API Error {response.status_code}: {response.text}"
            }
        
        result = response.json()
        
        # Extract text from markdown or chunks to detect document type
        extracted_text = ""
        if "markdown" in result:
            extracted_text = result.get("markdown", "")
        elif "chunks" in result:
            chunks = result.get("chunks", [])
            extracted_text = " ".join([chunk.get("text", "") for chunk in chunks])
        
        # Detect document type
        doc_type = detect_document_type(extracted_text)
        print(f"[DEBUG] Extracted text length: {len(extracted_text)}")
        
        # Extract specific fields based on document type
        extracted_fields = extract_document_fields(extracted_text, doc_type)
        
        # Return enriched result with document type and extracted fields
        return {
            "status": "success",
            "document_type": doc_type.value,
            "extracted_fields": extracted_fields,
            "raw_data": result
        }

    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": f"Network error: {str(e)}"}

    except Exception as e:
        print(f"[DEBUG] Exception in landingai_parse: {str(e)}")
        return {"status": "error", "error": str(e)}


def landingai_extract(path, schema_key: str):
    """Extract document fields using LandingAI API with retry logic."""
    api_key = get_api_key()
    if not api_key:
        return {"status": "error", "error": "LandingAI key missing"}

    try:
        if isinstance(path, str):
            path = Path(path)
        
        # Use LandingAI ADE REST API endpoint with schema
        url = "https://api.va.landing.ai/v1/tools/agentic-document-analysis"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        schema_class = schema_map.get(schema_key, DocumentMetadata)
        fields_schema = schema_class.model_json_schema()
        
        with open(path, "rb") as f:
            files = {
                "pdf": f,
                "include_marginalia": (None, "true"),
                "include_metadata_in_markdown": (None, "true"),
                "enable_rotation_detection": (None, "false"),
                "fields_schema": (None, json.dumps(fields_schema))
            }
            print(f"[DEBUG] Sending extraction request to {url}")
            # Use 300 second (5 minute) timeout with retry logic
            response = _api_call_with_retry(url, headers, files=files, timeout=300)
        
        print(f"[DEBUG] Extraction response status: {response.status_code}")
        
        if response.status_code != 200:
            return {
                "status": "error",
                "error": f"Extraction failed: {response.status_code}"
            }

        return {
            "status": "success",
            "data": response.json()
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}

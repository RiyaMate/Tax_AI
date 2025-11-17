"""
Test script to demonstrate the validation framework for form field extraction
This tests W-2, 1099-NEC, and 1099-INT form validation
"""

import sys
sys.path.insert(0, '../frontend/utils')

from landingai_utils import (
    extract_fields_w2,
    extract_fields_1099_nec,
    extract_fields_1099_int,
    detect_document_type,
    validate_field,
    generate_validation_report
)

# Test 1: W-2 Form Extraction and Validation
print("\n" + "="*80)
print("TEST 1: W-2 FORM VALIDATION")
print("="*80)

w2_text = """
FORM W-2 - WAGE AND TAX STATEMENT
Box 1 Wages, tips, other compensation: $85,000.50
Box 2 Federal income tax withheld: $12,500.00
Box 3 Social Security wages: $85,000.50
Box 5 Medicare wages: $85,000.50
EIN: 12-3456789
SSN: 123-45-6789
"""

w2_fields = extract_fields_w2(w2_text)
print("\n[EXTRACTION RESULT]")
print(f"Document Type: {w2_fields['document_type']}")
print(f"Wages: {w2_fields['wages']}")
print(f"Federal Tax Withheld: {w2_fields['federal_income_tax_withheld']}")
print(f"SS Wages: {w2_fields['social_security_wages']}")
print(f"Medicare Wages: {w2_fields['medicare_wages']}")
print(f"Employer EIN: {w2_fields['employer_ein']}")
print(f"Employee SSN: {w2_fields['employee_ssn']}")

print("\n[VALIDATION REPORT]")
validation_w2 = w2_fields['validation']
print(f"[OK] Valid Fields: {validation_w2['valid_fields']}/{validation_w2['total_fields']}")
print(f"[NO] Missing Required: {len(validation_w2['missing_required'])}")
print(f"○ Missing Optional: {len(validation_w2['missing_optional'])}")
print(f"[NO] Invalid Format: {len(validation_w2['invalid_fields'])}")
print(f"Completeness: {validation_w2['completeness_percentage']}%")
print(f"Data Quality: {validation_w2['data_quality']}")
if validation_w2['validation_warnings']:
    print(f"Warnings: {validation_w2['validation_warnings']}")

# Test 2: 1099-NEC Form Extraction and Validation
print("\n" + "="*80)
print("TEST 2: 1099-NEC FORM VALIDATION")
print("="*80)

nec_text = """
FORM 1099-NEC - NONEMPLOYEE COMPENSATION
Box 1 Nonemployee compensation: $25,000.00
Box 4 Federal income tax withheld: $3,750.00
Payer EIN: 98-7654321
Recipient TIN: 987-65-4321
"""

nec_fields = extract_fields_1099_nec(nec_text)
print("\n[EXTRACTION RESULT]")
print(f"Document Type: {nec_fields['document_type']}")
print(f"Nonemployee Compensation: {nec_fields['nonemployee_compensation']}")
print(f"Federal Tax Withheld: {nec_fields['federal_income_tax_withheld']}")
print(f"Payer EIN: {nec_fields['payer_ein']}")
print(f"Recipient TIN: {nec_fields['recipient_tin']}")

print("\n[VALIDATION REPORT]")
validation_nec = nec_fields['validation']
print(f"[OK] Valid Fields: {validation_nec['valid_fields']}/{validation_nec['total_fields']}")
print(f"[NO] Missing Required: {len(validation_nec['missing_required'])}")
print(f"○ Missing Optional: {len(validation_nec['missing_optional'])}")
print(f"[NO] Invalid Format: {len(validation_nec['invalid_fields'])}")
print(f"Completeness: {validation_nec['completeness_percentage']}%")
print(f"Data Quality: {validation_nec['data_quality']}")
if validation_nec['validation_warnings']:
    print(f"Warnings: {validation_nec['validation_warnings']}")

# Test 3: 1099-INT Form Extraction and Validation
print("\n" + "="*80)
print("TEST 3: 1099-INT FORM VALIDATION")
print("="*80)

int_text = """
FORM 1099-INT - INTEREST INCOME
Box 1 Interest income: $1,500.00
Box 4 Federal income tax withheld: $225.00
Payer TIN: 56-3456789
Recipient TIN: 456-78-9012
"""

int_fields = extract_fields_1099_int(int_text)
print("\n[EXTRACTION RESULT]")
print(f"Document Type: {int_fields['document_type']}")
print(f"Interest Income: {int_fields['interest_income']}")
print(f"Federal Tax Withheld: {int_fields['federal_income_tax_withheld']}")
print(f"Payer TIN: {int_fields['payer_tin']}")
print(f"Recipient TIN: {int_fields['recipient_tin']}")

print("\n[VALIDATION REPORT]")
validation_int = int_fields['validation']
print(f"[OK] Valid Fields: {validation_int['valid_fields']}/{validation_int['total_fields']}")
print(f"[NO] Missing Required: {len(validation_int['missing_required'])}")
print(f"○ Missing Optional: {len(validation_int['missing_optional'])}")
print(f"[NO] Invalid Format: {len(validation_int['invalid_fields'])}")
print(f"Completeness: {validation_int['completeness_percentage']}%")
print(f"Data Quality: {validation_int['data_quality']}")
if validation_int['validation_warnings']:
    print(f"Warnings: {validation_int['validation_warnings']}")

# Test 4: Document Type Detection
print("\n" + "="*80)
print("TEST 4: DOCUMENT TYPE DETECTION")
print("="*80)

doc_types = [
    ("This is a W-2 form showing wages and tax information", "W-2"),
    ("Form 1099-NEC for nonemployee compensation", "1099-NEC"),
    ("1099-INT form for interest income", "1099-INT"),
]

for text, expected in doc_types:
    detected = detect_document_type(text)
    print(f"Text: '{text[:50]}...'")
    print(f"Expected: {expected}, Detected: {detected.value}, Match: {'[OK]' if expected in detected.value else '[NO]'}\n")

# Test 5: Individual Field Validation
print("\n" + "="*80)
print("TEST 5: INDIVIDUAL FIELD VALIDATION")
print("="*80)

test_fields = [
    ("wages", "$85,000.50", True, "Valid currency"),
    ("wages", "invalid", True, "Invalid currency"),
    ("employer_ein", "12-3456789", False, "Valid EIN"),
    ("employer_ein", "invalid", False, "Invalid EIN"),
    ("employee_ssn", "123-45-6789", False, "Valid SSN"),
    ("employee_ssn", "", True, "Missing required field"),
    ("optional_field", "", False, "Missing optional field"),
]

for field_name, value, required, description in test_fields:
    result = validate_field(field_name, value, required)
    print(f"{description}:")
    print(f"  Field: {field_name}, Value: {value}, Required: {required}")
    print(f"  Status: {result['status']}, Valid: {result['valid']}")
    if result['error']:
        print(f"  Error: {result['error']}")
    print()

print("="*80)
print("VALIDATION FRAMEWORK TEST COMPLETE")
print("="*80)

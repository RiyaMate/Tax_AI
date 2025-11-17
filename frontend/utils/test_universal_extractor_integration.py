"""
Test the integrated universal extractor in landingai_utils.py
"""

import sys
import json
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from landingai_utils import extract_document_fields, DocumentType

# Example markdown outputs from LandingAI ADE

EXAMPLE_W2 = """
# FORM W-2

Box 1 | Wages, tips, other comp | $23,500.00
Box 2 | Federal income tax withheld | $1,500.00
Box 3 | Social Security wages and tips | $23,500.00
Box 4 | Social Security tax withheld | $1,457.00
Box 5 | Medicare wages and tips | $23,500.00
Box 6 | Medicare tax withheld | $340.75
Box 17 | State income tax withheld | $800.00

Employer EIN: 12-3456789
Employee SSN: 123-45-6789
"""

EXAMPLE_1099_NEC = """
# FORM 1099-NEC

Box 1 | Nonemployee Compensation | $12,000.00
Box 4 | Federal income tax withheld | $500.00

Payer EIN: 98-7654321
Recipient TIN: 987-65-4321
"""

EXAMPLE_1099_INT = """
# FORM 1099-INT

Box 1 | Interest Income | $233.51
Box 4 | Federal income tax withheld | $35.03

Payer TIN: 55-1234567
Recipient TIN: 555-55-5555
"""

def test_extraction(example_text: str, doc_type: DocumentType, expected_fields: dict):
    """Test extraction and validate results"""
    print(f"\n{'='*70}")
    print(f"Testing {doc_type.value}")
    print(f"{'='*70}")
    
    try:
        result = extract_document_fields(example_text, doc_type)
        
        print(f"\n[RESULT]")
        print(json.dumps(result, indent=2))
        
        # Validation
        print(f"\n[VALIDATION]")
        all_ok = True
        for field, expected_value in expected_fields.items():
            actual_value = result.get(field)
            match = str(actual_value) == str(expected_value)
            status = "[OK]" if match else "[FAIL]"
            if not match:
                all_ok = False
            print(f"  {status} {field}: expected {expected_value}, got {actual_value}")
        
        return all_ok
        
    except Exception as e:
        print(f"[ERROR] Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("="*70)
    print("UNIVERSAL EXTRACTOR INTEGRATION TEST")
    print("="*70)
    
    all_tests_pass = True
    
    # Test W-2
    w2_tests = test_extraction(
        EXAMPLE_W2,
        DocumentType.W2,
        {
            "document_type": "W-2",
            "wages": "23500.0",
            "federal_income_tax_withheld": "1500.0",
            "employer_ein": "12-3456789",
            "employee_ssn": "123-45-6789",
        }
    )
    all_tests_pass = all_tests_pass and w2_tests
    
    # Test 1099-NEC
    nec_tests = test_extraction(
        EXAMPLE_1099_NEC,
        DocumentType.FORM_1099_NEC,
        {
            "document_type": "1099-NEC",
            "nonemployee_compensation": "12000.0",
            "federal_income_tax_withheld": "500.0",
        }
    )
    all_tests_pass = all_tests_pass and nec_tests
    
    # Test 1099-INT
    int_tests = test_extraction(
        EXAMPLE_1099_INT,
        DocumentType.FORM_1099_INT,
        {
            "document_type": "1099-INT",
            "interest_income": "233.51",
            "federal_income_tax_withheld": "35.03",
        }
    )
    all_tests_pass = all_tests_pass and int_tests
    
    # Summary
    print(f"\n{'='*70}")
    if all_tests_pass:
        print("ALL TESTS PASSED [OK]")
    else:
        print("SOME TESTS FAILED [FAILED]")
    print(f"{'='*70}")

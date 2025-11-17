"""
INTEGRATION TEST: Universal Markdown Numeric Extractor
Tests extraction through landingai_utils.extract_document_fields()
"""

from landingai_utils import extract_document_fields, DocumentType

# Real markdown examples
W2_MARKDOWN = """
## W-2 Wage and Tax Statement

Box 1 - Wages, tips, other compensation: $23,500.00
Box 2 - Federal income tax withheld: $1,500.00
Box 3 - Social security wages: $23,500.00
Box 4 - Social security tax withheld: $1,457.00
Box 5 - Medicare wages and tips: $23,500.00
Box 6 - Medicare tax withheld: $340.75
"""

FORM_1099_NEC_MARKDOWN = """
## Form 1099-NEC Nonemployee Compensation

Box 1 - Nonemployee compensation: $12,000.00
Box 2 - Federal income tax withheld: $500.00
"""

FORM_1099_INT_MARKDOWN = """
## Form 1099-INT Interest Income

Box 1 - Interest income: $233.51
Box 3 - Federal income tax withheld: $35.03
"""


def test_w2_through_landingai_utils():
    """Test W-2 extraction through landingai_utils."""
    print("\n" + "=" * 70)
    print("TEST 1: W-2 Extraction Through landingai_utils")
    print("=" * 70)
    
    result = extract_document_fields(W2_MARKDOWN, DocumentType.W2)
    
    print(f"\nResult:")
    for key, value in result.items():
        print(f"  {key:40s} = {value}")
    
    # Verify
    assert result["document_type"] == "W-2", f"Expected W-2, got {result['document_type']}"
    assert result["wages"] == 23500.0, f"Expected wages=23500, got {result['wages']}"
    assert result["federal_income_tax_withheld"] == 1500.0, f"Expected fed_tax=1500, got {result['federal_income_tax_withheld']}"
    assert result["extraction_method"] == "markdown_numeric", f"Expected markdown_numeric method, got {result.get('extraction_method')}"
    
    print("\n[OK] W-2 extraction PASSED")
    return True


def test_1099_nec_through_landingai_utils():
    """Test 1099-NEC extraction through landingai_utils."""
    print("\n" + "=" * 70)
    print("TEST 2: 1099-NEC Extraction Through landingai_utils")
    print("=" * 70)
    
    result = extract_document_fields(FORM_1099_NEC_MARKDOWN, DocumentType.FORM_1099_NEC)
    
    print(f"\nResult:")
    for key, value in result.items():
        print(f"  {key:40s} = {value}")
    
    # Verify
    assert result["document_type"] == "1099-NEC", f"Expected 1099-NEC, got {result['document_type']}"
    assert result["nonemployee_compensation"] == 12000.0, f"Expected nec=12000, got {result['nonemployee_compensation']}"
    assert result["federal_income_tax_withheld"] == 500.0, f"Expected fed_tax=500, got {result['federal_income_tax_withheld']}"
    assert result["extraction_method"] == "markdown_numeric", f"Expected markdown_numeric method, got {result.get('extraction_method')}"
    
    print("\n[OK] 1099-NEC extraction PASSED")
    return True


def test_1099_int_through_landingai_utils():
    """Test 1099-INT extraction through landingai_utils."""
    print("\n" + "=" * 70)
    print("TEST 3: 1099-INT Extraction Through landingai_utils")
    print("=" * 70)
    
    result = extract_document_fields(FORM_1099_INT_MARKDOWN, DocumentType.FORM_1099_INT)
    
    print(f"\nResult:")
    for key, value in result.items():
        print(f"  {key:40s} = {value}")
    
    # Verify
    assert result["document_type"] == "1099-INT", f"Expected 1099-INT, got {result['document_type']}"
    assert result["interest_income"] == 233.51, f"Expected interest=233.51, got {result['interest_income']}"
    assert result["federal_income_tax_withheld"] == 35.03, f"Expected fed_tax=35.03, got {result['federal_income_tax_withheld']}"
    assert result["extraction_method"] == "markdown_numeric", f"Expected markdown_numeric method, got {result.get('extraction_method')}"
    
    print("\n[OK] 1099-INT extraction PASSED")
    return True


def run_all_integration_tests():
    """Run all integration tests."""
    print("\n" + "█" * 70)
    print("█ INTEGRATION TEST: Universal Markdown Numeric Extractor")
    print("█" * 70)
    
    tests = [
        ("W-2 through landingai_utils", test_w2_through_landingai_utils),
        ("1099-NEC through landingai_utils", test_1099_nec_through_landingai_utils),
        ("1099-INT through landingai_utils", test_1099_int_through_landingai_utils),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"\n[FAIL] {test_name}: {e}")
            failed += 1
        except Exception as e:
            print(f"\n[ERROR] {test_name}: {type(e).__name__}: {e}")
            failed += 1
    
    print("\n" + "█" * 70)
    print(f"█ RESULTS: {passed} PASSED, {failed} FAILED")
    print("█" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_integration_tests()
    exit(0 if success else 1)

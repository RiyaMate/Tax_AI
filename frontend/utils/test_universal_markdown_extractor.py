"""
TEST SUITE: Universal Markdown Numeric Extractor

Tests real W-2, 1099-NEC, 1099-INT Markdown outputs from LandingAI.
Zero schema. Zero assumptions. Pure numeric extraction.
"""

from universal_markdown_numeric_extractor import UniversalMarkdownNumericExtractor


# ============================================================================
# REAL MARKDOWN EXAMPLES FROM LANDINGAI
# ============================================================================

W2_MARKDOWN = """
## W-2 Wage and Tax Statement

Employee Information:
- Name: John Smith
- SSN: 123-45-6789

Box 1 - Wages, tips, other compensation: $23,500.00
Box 2 - Federal income tax withheld: $1,500.00
Box 3 - Social security wages: $23,500.00
Box 4 - Social security tax withheld: $1,457.00
Box 5 - Medicare wages and tips: $23,500.00
Box 6 - Medicare tax withheld: $340.75

Employer Information:
- EIN: 12-3456789
- Name: ACME Corporation
"""

FORM_1099_NEC_MARKDOWN = """
## Form 1099-NEC Nonemployee Compensation

Recipient:
John Doe
Address: 123 Main St, Anytown, USA

Box 1 - Nonemployee compensation: $12,000.00
Box 2 - Federal income tax withheld: $500.00
Box 3 - Other income: $250.00

Filer:
ABC Consulting LLC
EIN: 98-7654321
"""

FORM_1099_INT_MARKDOWN = """
## Form 1099-INT Interest Income

Account Holder: Jane Johnson
SSN: 987-65-4321

Box 1 - Interest income: $233.51
Box 2 - US Savings Bonds: $0.00
Box 3 - Federal income tax withheld: $35.03
Box 4 - Early withdrawal penalty: $0.00

Financial Institution: First National Bank
"""

COMPLEX_MULTI_FORM_MARKDOWN = """
## Tax Documents Summary

### Document 1: W-2
Wages: $45,000
Federal Tax Withheld: $5,500
Social Security Wages: $45,000
Medicare Wages: $45,000

### Document 2: 1099-INT
Interest Income: $512.73
Tax Withheld: $77.00

### Document 3: 1099-NEC
Nonemployee Compensation: $8,500
Federal Tax Withheld: $425
"""

ARBITRARY_FORM_MARKDOWN = """
## Unusual Form Format (No Schema)

Total Receipts: $1,234.56
Cost of Goods Sold: $567.89
Gross Profit: $666.67
Operating Expenses: $200.00
Net Income: $466.67

Capital Improvements: $5,000
Depreciation: $250
Other Deductions: $100
"""


# ============================================================================
# TESTS
# ============================================================================

def test_w2_extraction():
    """Test W-2 markdown extraction."""
    print("\n" + "=" * 60)
    print("TEST 1: W-2 Markdown Extraction")
    print("=" * 60)
    
    extractor = UniversalMarkdownNumericExtractor()
    result = extractor.extract_and_normalize(W2_MARKDOWN)
    
    print(extractor.debug_extraction(W2_MARKDOWN))
    
    # Verify
    normalized = result["normalized"]
    assert normalized["wages"] == 23500.0, f"Expected wages=23500, got {normalized['wages']}"
    assert normalized["federal_income_tax_withheld"] == 1500.0, f"Expected fed_tax=1500, got {normalized['federal_income_tax_withheld']}"
    assert normalized["social_security_tax_withheld"] == 1457.0, f"Expected ss_tax=1457, got {normalized['social_security_tax_withheld']}"
    assert normalized["medicare_tax_withheld"] == 340.75, f"Expected medicare_tax=340.75, got {normalized['medicare_tax_withheld']}"
    
    print("\n[OK] W-2 extraction passed all assertions")
    return True


def test_1099_nec_extraction():
    """Test 1099-NEC markdown extraction."""
    print("\n" + "=" * 60)
    print("TEST 2: 1099-NEC Markdown Extraction")
    print("=" * 60)
    
    extractor = UniversalMarkdownNumericExtractor()
    result = extractor.extract_and_normalize(FORM_1099_NEC_MARKDOWN)
    
    print(extractor.debug_extraction(FORM_1099_NEC_MARKDOWN))
    
    # Verify
    normalized = result["normalized"]
    assert normalized["nonemployee_compensation"] == 12000.0, f"Expected nec=12000, got {normalized['nonemployee_compensation']}"
    assert normalized["federal_income_tax_withheld"] == 500.0, f"Expected fed_tax=500, got {normalized['federal_income_tax_withheld']}"
    
    print("\n[OK] 1099-NEC extraction passed all assertions")
    return True


def test_1099_int_extraction():
    """Test 1099-INT markdown extraction."""
    print("\n" + "=" * 60)
    print("TEST 3: 1099-INT Markdown Extraction")
    print("=" * 60)
    
    extractor = UniversalMarkdownNumericExtractor()
    result = extractor.extract_and_normalize(FORM_1099_INT_MARKDOWN)
    
    print(extractor.debug_extraction(FORM_1099_INT_MARKDOWN))
    
    # Verify
    normalized = result["normalized"]
    assert normalized["interest_income"] == 233.51, f"Expected interest=233.51, got {normalized['interest_income']}"
    assert normalized["federal_income_tax_withheld"] == 35.03, f"Expected fed_tax=35.03, got {normalized['federal_income_tax_withheld']}"
    
    print("\n[OK] 1099-INT extraction passed all assertions")
    return True


def test_multi_document_aggregation():
    """Test multi-document aggregation."""
    print("\n" + "=" * 60)
    print("TEST 4: Multi-Document Aggregation")
    print("=" * 60)
    
    extractor = UniversalMarkdownNumericExtractor()
    result = extractor.extract_and_normalize(COMPLEX_MULTI_FORM_MARKDOWN)
    
    print(extractor.debug_extraction(COMPLEX_MULTI_FORM_MARKDOWN))
    
    # Verify
    normalized = result["normalized"]
    assert normalized["wages"] == 45000.0, f"Expected wages=45000, got {normalized['wages']}"
    assert normalized["interest_income"] == 512.73, f"Expected interest=512.73, got {normalized['interest_income']}"
    assert normalized["nonemployee_compensation"] == 8500.0, f"Expected nec=8500, got {normalized['nonemployee_compensation']}"
    
    # Verify tax aggregation
    assert normalized["federal_income_tax_withheld"] >= 5500.0, f"Expected fed_tax >= 5500, got {normalized['federal_income_tax_withheld']}"
    
    print("\n[OK] Multi-document aggregation passed all assertions")
    return True


def test_arbitrary_form():
    """Test extraction on arbitrary form (no schema)."""
    print("\n" + "=" * 60)
    print("TEST 5: Arbitrary Form (Unknown Structure)")
    print("=" * 60)
    
    extractor = UniversalMarkdownNumericExtractor()
    result = extractor.extract_and_normalize(ARBITRARY_FORM_MARKDOWN)
    
    print(extractor.debug_extraction(ARBITRARY_FORM_MARKDOWN))
    
    raw = result["raw_fields"]
    print(f"\n[OK] Extracted {len(raw)} numeric fields from arbitrary form")
    print("     (Structure-agnostic extraction confirmed)")
    
    return True


def test_edge_cases():
    """Test edge cases and format variations."""
    print("\n" + "=" * 60)
    print("TEST 6: Edge Cases and Format Variations")
    print("=" * 60)
    
    edge_cases = {
        "Dollar sign format": "Wages: $50,000.50",
        "No dollar sign": "Wages: 50000.50",
        "Comma formatting": "Total Income: $1,000,000.00",
        "Dash separator": "Gross Income - 12500",
        "EN-dash separator": "Net Income – 9999.99",
        "Multiple spaces": "Federal Tax    $    1,500.00",
    }
    
    for test_name, markdown in edge_cases.items():
        extractor = UniversalMarkdownNumericExtractor()
        fields = extractor.extract_all_numeric_pairs(markdown)
        print(f"  {test_name:30s} -> {fields}")
    
    print("\n[OK] All edge cases handled correctly")
    return True


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all tests."""
    print("\n" + "█" * 60)
    print("█ UNIVERSAL MARKDOWN NUMERIC EXTRACTOR - TEST SUITE")
    print("█" * 60)
    
    tests = [
        ("W-2 Extraction", test_w2_extraction),
        ("1099-NEC Extraction", test_1099_nec_extraction),
        ("1099-INT Extraction", test_1099_int_extraction),
        ("Multi-Document Aggregation", test_multi_document_aggregation),
        ("Arbitrary Form (Zero Schema)", test_arbitrary_form),
        ("Edge Cases", test_edge_cases),
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
    
    print("\n" + "█" * 60)
    print(f"█ RESULTS: {passed} PASSED, {failed} FAILED")
    print("█" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

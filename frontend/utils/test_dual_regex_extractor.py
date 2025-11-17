"""
TEST: Updated Universal Extractor with Table Pattern Support

Tests the dual-regex approach:
1. Colon/dash patterns (original)
2. Table patterns (new - for ADE table output)
"""

from universal_markdown_numeric_extractor import UniversalMarkdownNumericExtractor

# Test data with ACTUAL LandingAI table format (no colons)
LANDINGAI_W2_TABLE_FORMAT = """
W-2 Employee Reference Copy Wage and Tax 2020

1 Wages, tips, other comp. 23500.00
2 Federal income tax withheld 1500.00
3 Social security wages 23500.00
4 Social security tax withheld 1457.00
5 Medicare wages and tips 23500.00
6 Medicare tax withheld 340.75
17 State income tax 800.00
"""

EARNINGS_SUMMARY_TABLE = """
Gross Pay                          25,000.00
Less Other Cafe 125                 1,000.00
Less Cafe125 HSA (W-Box 12)           500.00
Reported W-2 Wages                 23,500.00
"""

# Test data with colon format (original style)
MARKDOWN_WITH_COLONS = """
Box 1 - Wages: $23,500.00
Box 2 - Federal income tax withheld: $1,500.00
Box 3 - Social security wages: $23,500.00
"""

# Mixed format (both colon and table)
MIXED_FORMAT = """
# W-2 Summary

Box 1 - Wages, tips, other comp.: $23,500.00
Box 2 - Federal income tax withheld: $1,500.00

Earnings Breakdown:
Gross Pay                    25,000.00
Less Deductions               1,500.00
Net W-2 Wages               23,500.00
"""


def test_table_format_extraction():
    """Test extraction from ADE table format (no colons)."""
    print("\n" + "=" * 70)
    print("TEST 1: ADE Table Format (no colons/dashes)")
    print("=" * 70)
    
    extractor = UniversalMarkdownNumericExtractor()
    fields = extractor.extract_all_numeric_pairs(LANDINGAI_W2_TABLE_FORMAT)
    
    print(f"\nExtracted {len(fields)} fields:")
    for label, value in sorted(fields.items()):
        print(f"  {label:40s} = {value:15.2f}")
    
    # Verify key values
    # The label "1 Wages, tips, other comp." becomes "1_wages_tips_other_comp"
    # Also "2 Federal income tax withheld" becomes "2_federal_income_tax_withheld"
    assert any(v == 23500.0 for k, v in fields.items() if "wage" in k.lower()), \
        f"Expected wages=23500 in {list(fields.keys())}"
    assert any(v == 1500.0 for k, v in fields.items() if "federal" in k.lower()), \
        f"Expected federal_tax=1500 in {list(fields.keys())}"
    assert any(v == 800.0 for k, v in fields.items() if "state" in k.lower()), \
        f"Expected state_tax=800 in {list(fields.keys())}"
    
    print("\n[OK] Table format extraction PASSED")
    return True


def test_earnings_summary_extraction():
    """Test extraction from earnings summary section."""
    print("\n" + "=" * 70)
    print("TEST 2: Earnings Summary Section (table with 2+ spaces)")
    print("=" * 70)
    
    extractor = UniversalMarkdownNumericExtractor()
    fields = extractor.extract_all_numeric_pairs(EARNINGS_SUMMARY_TABLE)
    
    print(f"\nExtracted {len(fields)} fields:")
    for label, value in sorted(fields.items()):
        print(f"  {label:40s} = {value:15.2f}")
    
    # Verify key values
    # The label key format includes the box number prefix, so check both variants
    assert fields.get("reported_w_2_wages") == 23500.0, f"Expected reported_w_2_wages=23500, got {fields.get('reported_w_2_wages')}"
    assert fields.get("gross_pay") == 25000.0, f"Expected gross_pay=25000, got {fields.get('gross_pay')}"
    
    print("\n[OK] Earnings summary extraction PASSED")
    return True


def test_colon_format_still_works():
    """Verify that original colon format still works."""
    print("\n" + "=" * 70)
    print("TEST 3: Original Colon Format (backward compatibility)")
    print("=" * 70)
    
    extractor = UniversalMarkdownNumericExtractor()
    fields = extractor.extract_all_numeric_pairs(MARKDOWN_WITH_COLONS)
    
    print(f"\nExtracted {len(fields)} fields:")
    for label, value in sorted(fields.items()):
        print(f"  {label:40s} = {value:15.2f}")
    
    # Verify key values
    # The colon format extracts labels like "box 1 wages..." but also picks up "Box 1 -" separately
    # Just verify main fields are present
    assert fields.get("wages_tips_other_comp") == 23500.0 or any(
        v == 23500.0 for k, v in fields.items() if "wage" in k.lower()
    ), "Expected wages around 23500"
    assert fields.get("federal_income_tax_withheld") == 1500.0 or any(
        v == 1500.0 for k, v in fields.items() if "federal" in k.lower()
    ), "Expected federal tax around 1500"
    
    print("\n[OK] Colon format extraction PASSED")
    return True


def test_mixed_format():
    """Test extraction from mixed format document."""
    print("\n" + "=" * 70)
    print("TEST 4: Mixed Format (colons + table)")
    print("=" * 70)
    
    extractor = UniversalMarkdownNumericExtractor()
    result = extractor.extract_and_normalize(MIXED_FORMAT)
    
    print(f"\nRaw fields extracted: {result['field_count']}")
    for label, value in sorted(result['raw_fields'].items()):
        print(f"  {label:40s} = {value:15.2f}")
    
    print(f"\nNormalized tax fields:")
    normalized = result['normalized']
    for key, value in sorted(normalized.items()):
        if value not in (0.0, None) or key in ['wages', 'federal_income_tax_withheld']:
            print(f"  {key:40s} = {value}")
    
    # Verify extraction
    assert result['field_count'] >= 3, f"Expected at least 3 fields, got {result['field_count']}"
    assert normalized['wages'] > 0, "Expected wages to be populated"
    
    print("\n[OK] Mixed format extraction PASSED")
    return True


def test_normalization_with_table_input():
    """Test that normalization works correctly with table input."""
    print("\n" + "=" * 70)
    print("TEST 5: Normalization with Table Input")
    print("=" * 70)
    
    extractor = UniversalMarkdownNumericExtractor()
    result = extractor.extract_and_normalize(LANDINGAI_W2_TABLE_FORMAT)
    
    normalized = result['normalized']
    
    print(f"\nNormalized output:")
    print(f"  wages                              = {normalized['wages']}")
    print(f"  federal_income_tax_withheld        = {normalized['federal_income_tax_withheld']}")
    print(f"  social_security_tax_withheld       = {normalized['social_security_tax_withheld']}")
    print(f"  medicare_tax_withheld              = {normalized['medicare_tax_withheld']}")
    print(f"  state_tax_withheld                 = {normalized['state_tax_withheld']}")
    
    # Verify normalization
    assert normalized['wages'] == 23500.0, f"Expected wages=23500, got {normalized['wages']}"
    assert normalized['federal_income_tax_withheld'] == 1500.0
    assert normalized['state_tax_withheld'] == 800.0
    
    print("\n[OK] Normalization with table input PASSED")
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "█" * 70)
    print("█ DUAL-REGEX EXTRACTOR TEST SUITE")
    print("█ Testing colon/dash AND table patterns")
    print("█" * 70)
    
    tests = [
        ("Table format extraction", test_table_format_extraction),
        ("Earnings summary extraction", test_earnings_summary_extraction),
        ("Colon format backward compatibility", test_colon_format_still_works),
        ("Mixed format extraction", test_mixed_format),
        ("Normalization with table input", test_normalization_with_table_input),
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
    success = run_all_tests()
    exit(0 if success else 1)

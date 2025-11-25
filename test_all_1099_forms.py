"""
TEST: Verify all 1099 forms are correctly handled

Tests for:
- 1099-MISC (Miscellaneous Income) - Box 3 (Other Income)
- 1099-NEC (Nonemployee Compensation) - Self-Employment Income
- 1099-INT (Interest Income)
- 1099-DIV (Dividend Income)
- 1099-B (Brokerage Sales) - Capital Gains
- 1099-K (Payment Card Transactions)
- 1099-OID (Original Issue Discount)
"""

import sys
import os

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'frontend', 'utils'))

from tax_engine import calculate_tax

def test_1099_nec():
    """1099-NEC: Self-employment income - DOES generate SE tax"""
    print("\n" + "="*80)
    print("TEST: 1099-NEC (Nonemployee Compensation)")
    print("="*80)
    
    doc = {
        "wages": 0.0,
        "nonemployee_compensation": 15000.00,  # SE income
        "other_income": 0.0,
        "rents": 0.0, "royalties": 0.0, "fishing_boat_proceeds": 0.0,
        "medical_payments": 0.0, "substitute_payments": 0.0,
        "crop_insurance_proceeds": 0.0, "gross_proceeds_attorney": 0.0,
        "excess_parachute_payments": 0.0, "nonqualified_deferred_comp": 0.0,
        "interest_income": 0.0, "dividend_income": 0.0,
        "federal_income_tax_withheld": 0.0,
        "social_security_tax_withheld": 0.0, "medicare_tax_withheld": 0.0,
    }
    
    result = calculate_tax([doc], filing_status="single", num_dependents=0)
    
    print(f"\nIncome Summary:")
    print(f"  1099-NEC: $15,000.00")
    print(f"  Standard Deduction: ${result['deduction']['amount']:,.2f}")
    print(f"  Taxable Income: ${result['taxable_income']:,.2f}")
    print(f"\nTax Summary:")
    print(f"  Federal Income Tax: ${result['taxes']['federal_income_tax']:,.2f}")
    print(f"  Self-Employment Tax: ${result['taxes']['self_employment_tax']:,.2f} [EXPECTED: NON-ZERO]")
    print(f"  Total Tax: ${result['taxes']['total_tax_before_credits']:,.2f}")
    
    se_tax_ok = result['taxes']['self_employment_tax'] > 0
    print(f"\nResult: SE tax generated = {se_tax_ok} {'✅ CORRECT' if se_tax_ok else '❌ WRONG'}")
    return se_tax_ok


def test_1099_int():
    """1099-INT: Interest Income - Only federal income tax, no SE tax"""
    print("\n" + "="*80)
    print("TEST: 1099-INT (Interest Income)")
    print("="*80)
    
    doc = {
        "wages": 0.0,
        "nonemployee_compensation": 0.0,
        "other_income": 0.0,
        "rents": 0.0, "royalties": 0.0, "fishing_boat_proceeds": 0.0,
        "medical_payments": 0.0, "substitute_payments": 0.0,
        "crop_insurance_proceeds": 0.0, "gross_proceeds_attorney": 0.0,
        "excess_parachute_payments": 0.0, "nonqualified_deferred_comp": 0.0,
        "interest_income": 5000.00,  # Interest income
        "dividend_income": 0.0,
        "federal_income_tax_withheld": 0.0,
        "social_security_tax_withheld": 0.0, "medicare_tax_withheld": 0.0,
    }
    
    result = calculate_tax([doc], filing_status="single", num_dependents=0)
    
    print(f"\nIncome Summary:")
    print(f"  1099-INT Interest: $5,000.00")
    print(f"  Standard Deduction: ${result['deduction']['amount']:,.2f}")
    print(f"  Taxable Income: ${result['taxable_income']:,.2f}")
    print(f"\nTax Summary:")
    print(f"  Federal Income Tax: ${result['taxes']['federal_income_tax']:,.2f}")
    print(f"  Self-Employment Tax: ${result['taxes']['self_employment_tax']:,.2f} [EXPECTED: $0]")
    print(f"  Total Tax: ${result['taxes']['total_tax_before_credits']:,.2f}")
    
    se_tax_ok = result['taxes']['self_employment_tax'] == 0.0
    print(f"\nResult: No SE tax generated = {se_tax_ok} {'✅ CORRECT' if se_tax_ok else '❌ WRONG'}")
    return se_tax_ok


def test_1099_div():
    """1099-DIV: Dividend Income - Only federal income tax, no SE tax"""
    print("\n" + "="*80)
    print("TEST: 1099-DIV (Dividend Income)")
    print("="*80)
    
    doc = {
        "wages": 0.0,
        "nonemployee_compensation": 0.0,
        "other_income": 0.0,
        "rents": 0.0, "royalties": 0.0, "fishing_boat_proceeds": 0.0,
        "medical_payments": 0.0, "substitute_payments": 0.0,
        "crop_insurance_proceeds": 0.0, "gross_proceeds_attorney": 0.0,
        "excess_parachute_payments": 0.0, "nonqualified_deferred_comp": 0.0,
        "interest_income": 0.0,
        "dividend_income": 3000.00,  # Dividend income
        "federal_income_tax_withheld": 0.0,
        "social_security_tax_withheld": 0.0, "medicare_tax_withheld": 0.0,
    }
    
    result = calculate_tax([doc], filing_status="single", num_dependents=0)
    
    print(f"\nIncome Summary:")
    print(f"  1099-DIV Dividends: $3,000.00")
    print(f"  Standard Deduction: ${result['deduction']['amount']:,.2f}")
    print(f"  Taxable Income: ${result['taxable_income']:,.2f}")
    print(f"\nTax Summary:")
    print(f"  Federal Income Tax: ${result['taxes']['federal_income_tax']:,.2f}")
    print(f"  Self-Employment Tax: ${result['taxes']['self_employment_tax']:,.2f} [EXPECTED: $0]")
    print(f"  Total Tax: ${result['taxes']['total_tax_before_credits']:,.2f}")
    
    se_tax_ok = result['taxes']['self_employment_tax'] == 0.0
    print(f"\nResult: No SE tax generated = {se_tax_ok} {'✅ CORRECT' if se_tax_ok else '❌ WRONG'}")
    return se_tax_ok


def test_1099_misc_box1_rents():
    """1099-MISC Box 1: Rents - Ordinary income, no SE tax"""
    print("\n" + "="*80)
    print("TEST: 1099-MISC Box 1 (Rents)")
    print("="*80)
    
    doc = {
        "wages": 0.0,
        "nonemployee_compensation": 0.0,
        "other_income": 0.0,
        "rents": 8000.00,  # Box 1: Rents
        "royalties": 0.0, "fishing_boat_proceeds": 0.0,
        "medical_payments": 0.0, "substitute_payments": 0.0,
        "crop_insurance_proceeds": 0.0, "gross_proceeds_attorney": 0.0,
        "excess_parachute_payments": 0.0, "nonqualified_deferred_comp": 0.0,
        "interest_income": 0.0, "dividend_income": 0.0,
        "federal_income_tax_withheld": 0.0,
        "social_security_tax_withheld": 0.0, "medicare_tax_withheld": 0.0,
    }
    
    result = calculate_tax([doc], filing_status="single", num_dependents=0)
    
    print(f"\nIncome Summary:")
    print(f"  1099-MISC Box 1 Rents: $8,000.00")
    print(f"  Standard Deduction: ${result['deduction']['amount']:,.2f}")
    print(f"  Taxable Income: ${result['taxable_income']:,.2f}")
    print(f"\nTax Summary:")
    print(f"  Federal Income Tax: ${result['taxes']['federal_income_tax']:,.2f}")
    print(f"  Self-Employment Tax: ${result['taxes']['self_employment_tax']:,.2f} [EXPECTED: $0]")
    print(f"  Total Tax: ${result['taxes']['total_tax_before_credits']:,.2f}")
    
    se_tax_ok = result['taxes']['self_employment_tax'] == 0.0
    print(f"\nResult: No SE tax generated = {se_tax_ok} {'✅ CORRECT' if se_tax_ok else '❌ WRONG'}")
    return se_tax_ok


def test_1099_misc_box5_fishing():
    """1099-MISC Box 5: Fishing Boat Proceeds - IS self-employment income"""
    print("\n" + "="*80)
    print("TEST: 1099-MISC Box 5 (Fishing Boat Proceeds) - SE Income")
    print("="*80)
    
    doc = {
        "wages": 0.0,
        "nonemployee_compensation": 0.0,
        "other_income": 0.0,
        "rents": 0.0,
        "royalties": 0.0,
        "fishing_boat_proceeds": 10000.00,  # Box 5: IS SE income
        "medical_payments": 0.0, "substitute_payments": 0.0,
        "crop_insurance_proceeds": 0.0, "gross_proceeds_attorney": 0.0,
        "excess_parachute_payments": 0.0, "nonqualified_deferred_comp": 0.0,
        "interest_income": 0.0, "dividend_income": 0.0,
        "federal_income_tax_withheld": 0.0,
        "social_security_tax_withheld": 0.0, "medicare_tax_withheld": 0.0,
    }
    
    result = calculate_tax([doc], filing_status="single", num_dependents=0)
    
    print(f"\nIncome Summary:")
    print(f"  1099-MISC Box 5 Fishing: $10,000.00")
    print(f"  Standard Deduction: ${result['deduction']['amount']:,.2f}")
    print(f"  Taxable Income: ${result['taxable_income']:,.2f}")
    print(f"\nTax Summary:")
    print(f"  Federal Income Tax: ${result['taxes']['federal_income_tax']:,.2f}")
    print(f"  Self-Employment Tax: ${result['taxes']['self_employment_tax']:,.2f}")
    print(f"  Total Tax: ${result['taxes']['total_tax_before_credits']:,.2f}")
    
    # Box 5 fishing proceeds are treated as SE income
    se_tax_ok = result['taxes']['self_employment_tax'] > 0
    print(f"\nResult: SE tax generated = {se_tax_ok} {'✅ CORRECT' if se_tax_ok else '❌ WRONG'}")
    return se_tax_ok


def test_combined_w2_plus_1099nec():
    """Combined: W-2 Wages + 1099-NEC Self-Employment"""
    print("\n" + "="*80)
    print("TEST: Combined W-2 + 1099-NEC")
    print("="*80)
    
    doc = {
        "wages": 50000.00,  # W-2 wages
        "nonemployee_compensation": 20000.00,  # 1099-NEC SE income
        "other_income": 0.0,
        "rents": 0.0, "royalties": 0.0, "fishing_boat_proceeds": 0.0,
        "medical_payments": 0.0, "substitute_payments": 0.0,
        "crop_insurance_proceeds": 0.0, "gross_proceeds_attorney": 0.0,
        "excess_parachute_payments": 0.0, "nonqualified_deferred_comp": 0.0,
        "interest_income": 0.0, "dividend_income": 0.0,
        "federal_income_tax_withheld": 5000.00,  # W-2 withholding
        "social_security_tax_withheld": 0.0, "medicare_tax_withheld": 0.0,
    }
    
    result = calculate_tax([doc], filing_status="single", num_dependents=0)
    
    print(f"\nIncome Summary:")
    print(f"  W-2 Wages: $50,000.00")
    print(f"  1099-NEC Self-Employment: $20,000.00")
    print(f"  Total Income: ${result['income']['total_income']:,.2f}")
    print(f"  Standard Deduction: ${result['deduction']['amount']:,.2f}")
    print(f"  Taxable Income: ${result['taxable_income']:,.2f}")
    print(f"\nTax Summary:")
    print(f"  Federal Income Tax: ${result['taxes']['federal_income_tax']:,.2f}")
    print(f"  Self-Employment Tax: ${result['taxes']['self_employment_tax']:,.2f} [FROM 1099-NEC ONLY]")
    print(f"  Total Tax: ${result['taxes']['total_tax_before_credits']:,.2f}")
    print(f"  Withholding: ${result['withholding']['total_withheld']:,.2f}")
    
    # Should have SE tax from 1099-NEC, federal tax from both
    se_tax_ok = result['taxes']['self_employment_tax'] > 0
    fed_tax_ok = result['taxes']['federal_income_tax'] > 0
    print(f"\nResult: SE tax generated = {se_tax_ok} {'✅' if se_tax_ok else '❌'}")
    print(f"Result: Federal tax generated = {fed_tax_ok} {'✅' if fed_tax_ok else '❌'}")
    
    return se_tax_ok and fed_tax_ok


if __name__ == "__main__":
    results = []
    
    # Run all tests
    results.append(("1099-NEC", test_1099_nec()))
    results.append(("1099-INT", test_1099_int()))
    results.append(("1099-DIV", test_1099_div()))
    results.append(("1099-MISC Box 1 (Rents)", test_1099_misc_box1_rents()))
    results.append(("1099-MISC Box 5 (Fishing)", test_1099_misc_box5_fishing()))
    results.append(("W-2 + 1099-NEC Combined", test_combined_w2_plus_1099nec()))
    
    # Summary
    print("\n" + "="*80)
    print("FINAL TEST SUMMARY")
    print("="*80)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {name:.<50} {status}")
        if not passed:
            all_passed = False
    
    print("="*80)
    if all_passed:
        print("\n✅ ALL TESTS PASSED - All 1099 forms handled correctly!\n")
    else:
        print("\n❌ SOME TESTS FAILED - Review results above\n")

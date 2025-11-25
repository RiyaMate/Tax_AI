"""
TEST: Verify 1099-MISC Box 3 is calculated correctly

Key requirement: Box 3 (Other Income) should NOT generate self-employment tax
"""

import sys
import os

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'frontend', 'utils'))

from tax_engine import calculate_tax, normalize_extracted_data

def test_1099_misc_box3_no_se_tax():
    """
    Test: $6,750 in Box 3 should result in $0 tax (below standard deduction)
    AND should NOT generate self-employment tax
    """
    print("\n" + "="*80)
    print("TEST: 1099-MISC Box 3 (Other Income) - Correct Calculation")
    print("="*80)
    
    # EXTRACTED DATA FROM YOUR ACTUAL FORM
    extracted_data = {
        # 1099-MISC Box 3 only
        "other_income": 6750.00,  # Box 3: Other Income
        
        # All other fields are zero
        "wages": 0.0,
        "federal_income_tax_withheld": 0.0,
        "social_security_wages": 0.0,
        "social_security_tax_withheld": 0.0,
        "medicare_wages": 0.0,
        "medicare_tax_withheld": 0.0,
        "nonemployee_compensation": 0.0,  # NOT from 1099-NEC
        "interest_income": 0.0,
        "dividend_income": 0.0,
    }
    
    # Normalize the data
    normalized = normalize_extracted_data(extracted_data)
    
    print(f"\n✓ Normalized Data:")
    print(f"  - Other Income (Box 3): ${normalized.get('other_income', 0.0):,.2f}")
    print(f"  - All other fields: $0.00")
    
    # Calculate tax
    # The tax_engine.py needs to handle other_income in 1099-MISC
    # Let's test with a mock document that includes the other_income field
    
    doc = {
        "wages": 0.0,
        "nonemployee_compensation": 0.0,  # KEY: This is $0 (no 1099-NEC)
        "other_income": 6750.00,  # Box 3 from 1099-MISC
        "rents": 0.0,
        "royalties": 0.0,
        "fishing_boat_proceeds": 0.0,
        "medical_payments": 0.0,
        "substitute_payments": 0.0,
        "crop_insurance_proceeds": 0.0,
        "gross_proceeds_attorney": 0.0,
        "excess_parachute_payments": 0.0,
        "nonqualified_deferred_comp": 0.0,
        "interest_income": 0.0,
        "dividend_income": 0.0,
        "federal_income_tax_withheld": 0.0,
        "social_security_tax_withheld": 0.0,
        "medicare_tax_withheld": 0.0,
    }
    
    # Calculate taxes
    result = calculate_tax([doc], filing_status="single", num_dependents=0)
    
    print(f"\n✓ Tax Calculation Results:")
    print(f"  - Total Income: ${result['income']['total_income']:,.2f}")
    print(f"  - Standard Deduction: ${result['deduction']['amount']:,.2f}")
    print(f"  - Taxable Income: ${result['taxable_income']:,.2f}")
    print(f"  - Federal Income Tax: ${result['taxes']['federal_income_tax']:,.2f}")
    print(f"  - Self-Employment Tax: ${result['taxes']['self_employment_tax']:,.2f}")
    print(f"  - Total Tax: ${result['taxes']['total_tax_before_credits']:,.2f}")
    print(f"  - Federal Withholding: ${result['withholding']['total_withheld']:,.2f}")
    if 'result' in result:
        print(f"  - Result: {result['result']['type']} - ${result['result']['amount']:,.2f}")
    else:
        refund_due = result['withholding']['total_withheld'] - result['total_tax_liability']
        result_type = "Refund" if refund_due > 0 else "Amount Due" if refund_due < 0 else "No Tax Due"
        print(f"  - Result: {result_type} - ${abs(refund_due):,.2f}")
    
    # VALIDATIONS
    print(f"\n✓ VALIDATIONS:")
    
    # Check 1: SE tax should be $0 (Box 3 is NOT SE income)
    se_tax_correct = result['taxes']['self_employment_tax'] == 0.0
    print(f"  ✓ SE Tax is $0: {se_tax_correct} {'✅' if se_tax_correct else '❌'}")
    
    # Check 2: Taxable income should be $0 (below $14,600 standard deduction)
    taxable_correct = result['taxable_income'] == 0.0
    print(f"  ✓ Taxable Income is $0: {taxable_correct} {'✅' if taxable_correct else '❌'}")
    
    # Check 3: Federal tax should be $0 (no taxable income)
    fed_tax_correct = result['taxes']['federal_income_tax'] == 0.0
    print(f"  ✓ Federal Tax is $0: {fed_tax_correct} {'✅' if fed_tax_correct else '❌'}")
    
    # Check 4: Total tax should be $0
    total_tax_correct = result['taxes']['total_tax_before_credits'] == 0.0
    print(f"  ✓ Total Tax is $0: {total_tax_correct} {'✅' if total_tax_correct else '❌'}")
    
    # Check 5: Result should be "No Tax Due"
    result_type = result.get('result', {}).get('type') or "No Tax Due"
    result_correct = result_type == "No Tax Due"
    print(f"  ✓ Result is 'No Tax Due': {result_correct} {'✅' if result_correct else '❌'}")
    
    # Check 6: Refund should be $0
    refund_amount = result.get('result', {}).get('amount', 0) if 'result' in result else (result['withholding']['total_withheld'] - result['total_tax_liability'])
    refund_correct = abs(refund_amount) < 0.01
    print(f"  ✓ Refund is $0: {refund_correct} {'✅' if refund_correct else '❌'}")
    
    all_correct = (se_tax_correct and taxable_correct and fed_tax_correct and 
                   total_tax_correct and result_correct and refund_correct)
    
    print(f"\n{'='*80}")
    if all_correct:
        print("✅ ALL TESTS PASSED - 1099-MISC Box 3 correctly handled!")
    else:
        print("❌ TESTS FAILED - Issues with 1099-MISC Box 3 calculation")
    print(f"{'='*80}\n")
    
    return all_correct


def test_1099_nec_with_se_tax():
    """
    Test: Verify that 1099-NEC DOES generate SE tax (for comparison)
    """
    print("\n" + "="*80)
    print("TEST: 1099-NEC (Self-Employment) - For Comparison")
    print("="*80)
    
    doc = {
        "wages": 0.0,
        "nonemployee_compensation": 6750.00,  # This DOES generate SE tax
        "other_income": 0.0,  # Box 3 is $0
        "rents": 0.0,
        "royalties": 0.0,
        "fishing_boat_proceeds": 0.0,
        "medical_payments": 0.0,
        "substitute_payments": 0.0,
        "crop_insurance_proceeds": 0.0,
        "gross_proceeds_attorney": 0.0,
        "excess_parachute_payments": 0.0,
        "nonqualified_deferred_comp": 0.0,
        "interest_income": 0.0,
        "dividend_income": 0.0,
        "federal_income_tax_withheld": 0.0,
        "social_security_tax_withheld": 0.0,
        "medicare_tax_withheld": 0.0,
    }
    
    result = calculate_tax([doc], filing_status="single", num_dependents=0)
    
    print(f"\n✓ Tax Calculation Results:")
    print(f"  - Total Income: ${result['income']['total_income']:,.2f}")
    print(f"  - Taxable Income: ${result['taxable_income']:,.2f}")
    print(f"  - Federal Income Tax: ${result['taxes']['federal_income_tax']:,.2f}")
    print(f"  - Self-Employment Tax: ${result['taxes']['self_employment_tax']:,.2f}")
    
    se_tax_nonzero = result['taxes']['self_employment_tax'] > 0
    print(f"\n✓ SE Tax is non-zero (as expected): {se_tax_nonzero} {'✅' if se_tax_nonzero else '❌'}")
    
    return se_tax_nonzero


if __name__ == "__main__":
    # Test 1: 1099-MISC Box 3 should NOT generate SE tax
    test1_passed = test_1099_misc_box3_no_se_tax()
    
    # Test 2: 1099-NEC should generate SE tax (for comparison)
    test2_passed = test_1099_nec_with_se_tax()
    
    print(f"\n{'='*80}")
    print("FINAL RESULTS:")
    print(f"  Test 1 (1099-MISC Box 3 - NO SE tax): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"  Test 2 (1099-NEC - WITH SE tax): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"{'='*80}\n")

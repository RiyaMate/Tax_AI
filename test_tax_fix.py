"""
Test script to verify the tax calculation fix
Testing with: $60,250 wages, Single filer, $7,200 withheld
Expected: $5,246 tax, $1,954 refund
"""

import sys
sys.path.insert(0, r'c:\Users\riyam\PDF_GREEN\LiteLLM_SummaryGenerator_with_Q-A\frontend\utils')

from tax_engine import calculate_tax

# Test case: $60,250 wages, Single filer
test_docs = [
    {
        "wages": 60250.00,
        "federal_income_tax_withheld": 7200.00,
        "social_security_wages": 60250.00,
        "social_security_tax_withheld": 0.0,
        "medicare_wages": 60250.00,
        "medicare_tax_withheld": 0.0,
        "nonemployee_compensation": 0.0,
        "interest_income": 0.0,
        "dividend_income": 0.0,
    }
]

print("="*80)
print("TEST: IRS 2024 Tax Calculation Fix")
print("="*80)
print("\nInput:")
print(f"  Wages: $60,250.00")
print(f"  Filing Status: Single")
print(f"  Standard Deduction: $14,600")
print(f"  Taxable Income: 60,250 - 14,600 = $45,650")
print(f"  Federal Withheld: $7,200.00")

print("\n" + "-"*80)
print("Expected Calculation (IRS 2024 Single Brackets):")
print("-"*80)
print(f"  10% bracket: $0 - $11,600     = $1,160.00")
print(f"  12% bracket: $11,600 - $47,150 = {(47150 - 11600) * 0.12:,.2f}")
print(f"  Partial 22%: $45,650 is below $47,150, so NO 22% bracket")
print(f"  TOTAL TAX: $1,160.00 + $4,086.00 = $5,246.00")
print(f"  Refund: $7,200.00 - $5,246.00 = $1,954.00")

print("\n" + "-"*80)
print("System Calculation:")
print("-"*80)

result = calculate_tax(
    test_docs,
    filing_status="single",
    num_dependents=0,
)

print("\n" + "="*80)
print("RESULTS COMPARISON")
print("="*80)

expected_tax = 5246.00
expected_refund = 1954.00

actual_tax = result["taxes"]["federal_income_tax"]
actual_refund = result["refund_or_due"]

print(f"\nFederal Tax:")
print(f"  Expected: ${expected_tax:,.2f}")
print(f"  Actual:   ${actual_tax:,.2f}")
print(f"  Match:    {'✅ CORRECT' if abs(actual_tax - expected_tax) < 0.01 else '❌ WRONG'}")

print(f"\nRefund Amount:")
print(f"  Expected: ${expected_refund:,.2f}")
print(f"  Actual:   ${actual_refund:,.2f}")
print(f"  Match:    {'✅ CORRECT' if abs(actual_refund - expected_refund) < 0.01 else '❌ WRONG'}")

print("\n" + "="*80)
if abs(actual_tax - expected_tax) < 0.01 and abs(actual_refund - expected_refund) < 0.01:
    print("✅ TAX ENGINE FIX VERIFIED - ALL TESTS PASSED!")
else:
    print("❌ TAX ENGINE STILL HAS ISSUES - REVIEW OUTPUT ABOVE")
print("="*80 + "\n")

# Print full result for detailed inspection
print("\nFull Result Dictionary:")
print("-"*80)
import json
print(json.dumps(result, indent=2, default=str))

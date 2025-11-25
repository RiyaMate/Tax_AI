"""
Test script to verify W-2 extraction from real LandingAI output
"""

import sys
import json
import requests

# Real LandingAI output from W2_Interactive.pdf
landingai_output = {
    "status": "success",
    "markdown": """<table id="0-1">
<tr><td id="0-2" colspan="4">W-2 Employee Reference Copy Wage and Tax 2020 Copy C for employee's records. OMB No. 1545-0008</td></tr>
<tr><td id="0-3">d Control number 000011 R#/123</td><td id="0-4">Dept.</td><td id="0-5">Corp.</td><td id="0-6">Employer use only A 22</td></tr>
<tr><td id="0-7" colspan="4">Employer's name, address, and ZIP code SAMPLE COMPANY INC 123 MAIN ST ANYWHERE, CA 123456 1234 BATCH #12345</td></tr>
<tr><td id="0-8" colspan="4">e/f Employee's name, address, and ZIP code JOHN SMITH 1234 S MAPLE ST ANYWHERE, CA 123456</td></tr>
<tr><td id="0-9" colspan="2">b Employer's FED ID number 12-3456789</td><td id="0-a" colspan="2">a Employee's SSA number XXX-XX-1234</td></tr>
<tr><td id="0-b" colspan="2">1 Wages, tips, other comp. 23500.00</td><td id="0-c" colspan="2">2 Federal income tax withheld 1500.00</td></tr>
<tr><td id="0-d" colspan="2">3 Social security wages 23500.00</td><td id="0-e" colspan="2">4 Social security tax withheld 1457.00</td></tr>
<tr><td id="0-f" colspan="2">5 Medicare wages and tips 23500.00</td><td id="0-g" colspan="2">6 Medicare tax withheld 340.75</td></tr>
</table>""",
    "extracted_values": [],
    "key_value_pairs": {}
}

print("=" * 80)
print("TEST: Real W-2 Extraction from LandingAI")
print("=" * 80)

print("\n📄 LandingAI Markdown (first 500 chars):")
print(landingai_output["markdown"][:500])

print("\n🔄 Sending to API endpoint...")
print(f"📍 Endpoint: http://localhost:8000/api/tax/process-with-llm")

try:
    response = requests.post(
        "http://localhost:8000/api/tax/process-with-llm",
        json={
            "landingai_output": landingai_output,
            "filing_status": "single",
            "num_dependents": 0,
        },
        timeout=60
    )
    
    print(f"\n✅ Response Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        print("\n" + "=" * 80)
        print("EXTRACTION RESULTS")
        print("=" * 80)
        
        print(f"\n📋 Document Type: {result.get('document_type', 'UNKNOWN')}")
        print(f"🔧 Extraction Method: {result.get('extraction_method', 'UNKNOWN')}")
        
        print(f"\n💰 INCOME BREAKDOWN:")
        print(f"  • Wages (Box 1): ${result.get('income_wages', 0):,.2f}")
        print(f"  • SS Wages (Box 3): ${result.get('income_ss_wages', 0):,.2f}")
        print(f"  • Medicare Wages (Box 5): ${result.get('income_medicare_wages', 0):,.2f}")
        
        print(f"\n📊 WITHHOLDING BREAKDOWN:")
        print(f"  • Federal Withheld (Box 2): ${result.get('withholding_federal_withheld', 0):,.2f}")
        print(f"  • SS Withheld (Box 4): ${result.get('withholding_ss_withheld', 0):,.2f}")
        print(f"  • Medicare Withheld (Box 6): ${result.get('withholding_medicare_withheld', 0):,.2f}")
        
        print(f"\n🧮 TAX CALCULATION:")
        print(f"  • Total Income: ${result.get('income_total_income', 0):,.2f}")
        print(f"  • Deduction: ${result.get('deduction_amount', 0):,.2f}")
        print(f"  • Taxable Income: ${result.get('taxable_income', 0):,.2f}")
        print(f"  • Federal Tax: ${result.get('taxes_federal_income_tax', 0):,.2f}")
        print(f"  • Total Tax: ${result.get('total_tax_liability', 0):,.2f}")
        
        print(f"\n📈 RESULT:")
        result_type = result.get('result_type', 'Unknown')
        result_amount = result.get('result_amount', 0)
        if result_type == 'Refund':
            print(f"  • 💰 REFUND: ${result_amount:,.2f}")
        elif result_type == 'Amount Due':
            print(f"  • 💳 AMOUNT DUE: ${result_amount:,.2f}")
        else:
            print(f"  • ➖ BREAK EVEN")
        
        # Verification
        print("\n" + "=" * 80)
        print("VERIFICATION")
        print("=" * 80)
        
        checks_passed = 0
        checks_total = 4
        
        if result.get('income_wages') == 23500.0:
            print("✅ PASS: Wages correctly extracted ($23,500.00)")
            checks_passed += 1
        else:
            print(f"❌ FAIL: Wages = ${result.get('income_wages', 0):.2f} (expected $23,500.00)")
        
        if result.get('withholding_federal_withheld') == 1500.0:
            print("✅ PASS: Federal withheld correctly extracted ($1,500.00)")
            checks_passed += 1
        else:
            print(f"❌ FAIL: Federal withheld = ${result.get('withholding_federal_withheld', 0):.2f} (expected $1,500.00)")
        
        if result.get('withholding_ss_withheld') == 1457.0:
            print("✅ PASS: SS withheld correctly extracted ($1,457.00)")
            checks_passed += 1
        else:
            print(f"❌ FAIL: SS withheld = ${result.get('withholding_ss_withheld', 0):.2f} (expected $1,457.00)")
        
        if result.get('withholding_medicare_withheld') == 340.75:
            print("✅ PASS: Medicare withheld correctly extracted ($340.75)")
            checks_passed += 1
        else:
            print(f"❌ FAIL: Medicare withheld = ${result.get('withholding_medicare_withheld', 0):.2f} (expected $340.75)")
        
        print(f"\n📊 SCORE: {checks_passed}/{checks_total} checks passed")
        
        if checks_passed == checks_total:
            print("\n🎉 ALL TESTS PASSED - W-2 Extraction Working Correctly!")
        else:
            print(f"\n⚠️  {checks_total - checks_passed} test(s) failed")
        
        # Full JSON output
        print("\n" + "=" * 80)
        print("FULL RESPONSE JSON")
        print("=" * 80)
        print(json.dumps(result, indent=2))
    
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"\n❌ Exception: {str(e)}")
    print("\nMake sure:")
    print("  1. API is running: python -m uvicorn main:app --reload")
    print("  2. Correct endpoint: http://localhost:8000")

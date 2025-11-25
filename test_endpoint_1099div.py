#!/usr/bin/env python3
"""
Test /process-with-llm endpoint with real 1099-DIV data
"""

import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Real LandingAI 1099-DIV extraction
test_payload = {
    "landingai_output": {
        "status": "success",
        "markdown": """<table id="0-1">
<tr><td id="0-3" colspan="2">1a Total ordinary dividends $ 1601.60</td><td id="0-4" rowspan="2">OMB No. 1545-0110 2020 Form 1099-DIV</td><td id="0-5" rowspan="2" colspan="2">Dividends and Distributions</td></tr>
<tr><td id="0-6" colspan="2">1b Qualified dividends $ 785.30</td></tr>
<tr><td id="0-7" colspan="2">2a Total capital gain distr.$ 271.79</td><td id="0-8" colspan="2">2b Unrecap. Sec. 1250 gain</td></tr>
<tr><td id="0-a">PAYER'S TIN 746552769</td><td id="0-b" colspan="2">RECIPIENT'S TIN 554-03-0876</td><td id="0-c" colspan="2">2c Section 1202 gain $ 32</td><td id="0-d" colspan="2">2d Collectibles (28%) gain</td></tr>
<tr><td id="0-g" colspan="2">4 Federal income tax withheld $ 54.28</td></tr>
</table>
Form 1099-DIV""",
        "extracted_values": [],
        "key_value_pairs": {}
    },
    "filing_status": "single",
    "num_dependents": 0,
    "llm_provider": "gemini"
}

print("=" * 80)
print("Testing /api/tax/process-with-llm with 1099-DIV")
print("=" * 80)

print("\n[TEST DATA]")
print("  Form: 1099-DIV (2020)")
print("  Dividend Income: $1,601.60")
print("  Capital Gains: $271.79")
print("  Federal Withheld: $54.28")

print("\n[SENDING REQUEST TO ENDPOINT]")
try:
    response = requests.post(
        "http://localhost:8000/api/tax/process-with-llm",
        json=test_payload,
        timeout=60
    )
    
    print(f"  Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        print("\n[EXTRACTED VALUES]")
        print(f"  Dividend Income: ${result.get('income_dividend_income', 0):,.2f}")
        print(f"  Capital Gains: ${result.get('income_capital_gains', 0):,.2f}")
        print(f"  Federal Withheld: ${result.get('withholding_federal_withheld', 0):,.2f}")
        
        print("\n[TAX CALCULATION]")
        print(f"  Total Income: ${result.get('income_total_income', 0):,.2f}")
        print(f"  Taxable Income: ${result.get('taxable_income', 0):,.2f}")
        print(f"  Federal Tax: ${result.get('taxes_federal_income_tax', 0):,.2f}")
        print(f"  Refund/Due: ${result.get('refund_or_due', 0):,.2f}")
        print(f"  Status: {result.get('result_status', 'N/A')}")
        
        # Verify values
        print("\n[VERIFICATION]")
        errors = []
        
        if result.get('income_dividend_income', 0) != 1601.60:
            errors.append(f"Dividend mismatch: {result.get('income_dividend_income')}")
        
        if result.get('income_capital_gains', 0) != 271.79:
            errors.append(f"Capital gains mismatch: {result.get('income_capital_gains')}")
        
        if result.get('withholding_federal_withheld', 0) != 54.28:
            errors.append(f"Withheld mismatch: {result.get('withholding_federal_withheld')}")
        
        if errors:
            print("  ❌ FAILED:")
            for e in errors:
                print(f"    - {e}")
        else:
            print("  ✓ All values correct!")
            print("  ✓ ENDPOINT WORKING!")
    
    else:
        print(f"\n  ERROR: {response.status_code}")
        print(f"  {response.json()}")

except Exception as e:
    print(f"\n  CONNECTION ERROR: {e}")
    print("  Make sure backend is running: cd api && python -m uvicorn main:app --reload --port 8000")

print("\n" + "=" * 80)

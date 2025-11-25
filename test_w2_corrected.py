"""
Test W-2 extraction with corrected regex patterns
"""
import requests
import json
import os
from dotenv import load_dotenv
import sys

load_dotenv(override=True)

# Add backend to path
sys.path.insert(0, r"C:\Users\riyam\PDF_GREEN\LiteLLM_SummaryGenerator_with_Q-A\backend")

from llm_tax_agent import map_w2

# Test data - simulated LandingAI output from W-2
test_markdown = """
<tr><td id="0-b" colspan="2">1 Wages, tips, other comp. 23500.00</td><td id="0-c" colspan="2">2 Federal income tax withh</td></tr>
<tr><td id="0-d" colspan="2">3 Social security wages 23500.00</td><td id="0-e" colspan="2">4 Social security tax withheld</td></tr>
<tr><td id="0-f" colspan="2">5 Medicare wages and tips 23500.00</td><td id="0-g" colspan="2">6 Medicare tax withheld 340</td></tr>
"""

# Simulate Federal and Medicare withheld
test_markdown_full = """
1 Wages, tips, other comp. 23500.00
2 Federal income tax withholding 1500.00
3 Social security wages 23500.00
4 Social security tax withheld 1457.00
5 Medicare wages and tips 23500.00
6 Medicare tax withheld 340.75
"""

test_output = {
    "markdown": test_markdown_full,
    "key_value_pairs": {},
    "extracted_values": []
}

print("[TEST] Testing corrected W-2 extraction...")
print("=" * 80)

result = map_w2(test_output)

print("\n[EXTRACTED VALUES]:")
for key, value in result.items():
    print(f"  {key}: ${value:,.2f}" if value > 0 else f"  {key}: {value}")

print("\n[VERIFICATION]:")
expected = {
    "income_wages": 23500.00,
    "withholding_federal_withheld": 1500.00,
    "withholding_ss_withheld": 1457.00,
    "withholding_medicare_withheld": 340.75,
}

all_correct = True
for key, expected_value in expected.items():
    actual_value = result.get(key, 0.0)
    match = "✓" if actual_value == expected_value else "✗"
    print(f"  {match} {key}: {actual_value} (expected {expected_value})")
    if actual_value != expected_value:
        all_correct = False

if all_correct:
    print("\n✓ All values extracted correctly!")
else:
    print("\n✗ Some values are still incorrect")

print("\n" + "=" * 80)

# Now test the full API
print("\n[TESTING WITH ACTUAL PDF]...")
pdf_path = r"C:\Users\riyam\Downloads\W2_Interactive.pdf"

if os.path.exists(pdf_path):
    try:
        with open(pdf_path, 'rb') as f:
            response = requests.post(
                "http://localhost:8000/api/tax/process-with-llm",
                json={
                    "landingai_output": {
                        "markdown": test_markdown_full,
                        "key_value_pairs": {},
                        "extracted_values": []
                    },
                    "filing_status": "single",
                    "num_dependents": 0
                },
                timeout=60
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n[API RESULT]:")
            print(f"  Income Wages: ${result.get('income_wages', 0):,.2f}")
            print(f"  Taxable Income: ${result.get('taxable_income', 0):,.2f}")
            print(f"  Federal Tax: ${result.get('taxes_federal_income_tax', 0):,.2f}")
            print(f"  Federal Withheld: ${result.get('withholding_federal_withheld', 0):,.2f}")
            print(f"  Refund: ${result.get('result_amount', 0):,.2f}")
            print(f"  Expected Refund: $610.00")
            print(f"  Status: {result.get('status')}")
        else:
            print(f"[ERROR] API failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"[ERROR] {str(e)}")
else:
    print(f"[WARNING] PDF not found at {pdf_path}")

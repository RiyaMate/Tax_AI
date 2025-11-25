"""
Quick test to verify the API endpoint is working with UniversalLLMTaxAgent
"""

import requests
import json

# Test the updated /api/tax/process-with-llm endpoint
BASE_URL = "http://localhost:8000"

# Simulate LandingAI output for a W-2 (HTML table format)
w2_test_data = {
    "markdown": """
<table>
<tr><td>Box</td><td>Description</td><td>Amount</td></tr>
<tr><td>1</td><td>Wages, tips, other comp.</td><td>$23,500.00</td></tr>
<tr><td>2</td><td>Federal income tax withheld</td><td>$1,500.00</td></tr>
<tr><td>3</td><td>Social Security wages</td><td>$23,500.00</td></tr>
<tr><td>4</td><td>Social Security tax withheld</td><td>$1,457.00</td></tr>
<tr><td>5</td><td>Medicare wages and tips</td><td>$23,500.00</td></tr>
<tr><td>6</td><td>Medicare tax withheld</td><td>$340.75</td></tr>
</table>
""",
    "extracted_values": [],
    "key_value_pairs": {}
}

print("=" * 80)
print("TEST: UniversalLLMTaxAgent Processing W-2")
print("=" * 80)

try:
    print("\n[TEST] Sending W-2 to /api/tax/process-with-llm...")
    
    response = requests.post(
        f"{BASE_URL}/api/tax/process-with-llm",
        json={
            "landingai_output": w2_test_data,
            "filing_status": "single",
            "num_dependents": 0,
        },
        timeout=60
    )
    
    print(f"[TEST] Response Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        print("\n✅ SUCCESS - Tax Calculation Complete!")
        print(f"\nExtraction Method: {result.get('extraction_method')}")
        print(f"Document Type: {result.get('document_type')}")
        print(f"Total Income: ${result.get('income_total_income', 0):,.2f}")
        print(f"Federal Withheld: ${result.get('withholding_federal_withheld', 0):,.2f}")
        print(f"Taxable Income: ${result.get('taxable_income', 0):,.2f}")
        print(f"Federal Tax: ${result.get('taxes_federal_income_tax', 0):,.2f}")
        print(f"Total Tax Liability: ${result.get('total_tax_liability', 0):,.2f}")
        print(f"\nResult: {result.get('result_type')} ${result.get('result_amount', 0):,.2f}")
        
        # Verify it extracted correctly
        if result.get('income_wages', 0) == 23500.0:
            print("\n✅ VERIFIED: Wages correctly extracted ($23,500.00)")
        else:
            print(f"\n❌ ERROR: Wages = {result.get('income_wages', 0)} (expected $23,500.00)")
            
        if result.get('withholding_federal_withheld', 0) == 1500.0:
            print("✅ VERIFIED: Federal withheld correctly extracted ($1,500.00)")
        else:
            print(f"❌ ERROR: Federal withheld = {result.get('withholding_federal_withheld', 0)} (expected $1,500.00)")
            
        if 600 < result.get('result_amount', 0) < 700:
            print("✅ VERIFIED: Refund in expected range (~$610)")
        else:
            print(f"❌ ERROR: Refund = {result.get('result_amount', 0)} (expected ~$610)")
            
    else:
        print(f"\n❌ ERROR: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

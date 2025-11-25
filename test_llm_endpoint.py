#!/usr/bin/env python3
"""
Test the new /api/tax/process-with-llm endpoint
"""

import requests
import json

# Sample LandingAI W-2 extraction output
landingai_w2_output = {
    "status": "success",
    "markdown": """<table id="0-5">
<tr><td id="0-6">1</td><td id="0-7">Wages, tips, other compensation 23,677.70</td></tr>
<tr><td id="0-8">3</td><td id="0-9">Social security wages 24,410.00</td></tr>
<tr><td id="0-a">5</td><td id="0-b">Medicare wages and tips 24,410.00</td></tr>
</table>

<table id="0-m">
<tr><td id="0-n">2</td><td id="0-o">Federal income tax withheld 2,841.32</td></tr>
<tr><td id="0-p">4</td><td id="0-q">Social security tax withheld 1,513.42</td></tr>
<tr><td id="0-r">6</td><td id="0-s">Medicare tax withheld 353.95</td></tr>
</table>""",
    "extracted_values": [],
    "key_value_pairs": {},
}

print("=" * 80)
print("TEST: /api/tax/process-with-llm Endpoint")
print("=" * 80)
print("\n1. Testing LLM agent endpoint with LandingAI W-2 output")
print("-" * 80)

request_body = {
    "landingai_output": landingai_w2_output,
    "filing_status": "single",
    "num_dependents": 0,
    "llm_provider": "gemini",  # or "openai", "claude", etc.
}

print("\nRequest:")
print(json.dumps(request_body, indent=2)[:500] + "...")

try:
    response = requests.post(
        "http://localhost:8000/api/tax/process-with-llm",
        json=request_body,
        timeout=60,  # 60 second timeout for LLM processing
    )
    
    print(f"\nResponse Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        print("\n✅ SUCCESS!")
        print("\nExtraction & Calculation Results:")
        print("-" * 80)
        
        # Show document type
        doc_type = result.get("document_type", "Unknown")
        print(f"Document Type: {doc_type}")
        
        # Show extracted fields
        if "normalized_fields" in result:
            print("\nNormalized Fields:")
            for key, value in result["normalized_fields"].items():
                if value > 0:
                    print(f"  {key:40s} = ${value:12,.2f}")
        
        # Show tax calculation
        if "tax_calculation" in result:
            tax_calc = result["tax_calculation"]
            print("\nTax Calculation (2024 IRS Standards):")
            print(f"  Total Income:     ${tax_calc.get('total_income', 0):12,.2f}")
            print(f"  Taxable Income:   ${tax_calc.get('taxable_income', 0):12,.2f}")
            print(f"  Federal Tax:      ${tax_calc.get('federal_tax', 0):12,.2f}")
            print(f"  Total Withholding:${tax_calc.get('total_withholding', 0):12,.2f}")
            if tax_calc.get('refund', 0) > 0:
                print(f"  💰 REFUND:        ${tax_calc.get('refund', 0):12,.2f}")
            else:
                print(f"  💸 AMOUNT DUE:    ${abs(tax_calc.get('due', 0)):12,.2f}")
        
        # Show summary
        if "summary" in result:
            print("\nSummary:")
            print(result["summary"][:500])
        
        print("\n" + "=" * 80)
        print("Full Response (JSON):")
        print("=" * 80)
        print(json.dumps(result, indent=2)[:2000])
        
    else:
        print(f"\n❌ ERROR")
        print(f"Response: {response.text}")

except requests.exceptions.ConnectionError:
    print("\n❌ ERROR: Could not connect to API")
    print("Make sure the API server is running on http://localhost:8000")
    print("\nTo start the API:")
    print("  cd api")
    print("  python main.py")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Test complete!")
print("=" * 80)

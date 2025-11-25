#!/usr/bin/env python3
"""
Test script to verify /process-with-llm endpoint works correctly
Tests the fix for 400 error
"""

import requests
import json
import sys

# Set UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')

# API endpoint
BASE_URL = "http://localhost:8000"
ENDPOINT = f"{BASE_URL}/api/tax/process-with-llm"

# Test data: Sample W-2 LandingAI extraction
test_payload = {
    "landingai_output": {
        "markdown": """
        FORM W-2 Wage and Tax Statement

        Box 1: Wages, tips, other compensation: $23,677.70
        Box 2: Federal income tax withheld: $2,841.32
        Box 3: Social Security wages: $23,677.70
        Box 4: Social Security tax withheld: $1,467.63
        Box 5: Medicare wages and tips: $23,677.70
        Box 6: Medicare tax withheld: $343.33
        """,
        "extracted_values": [],
        "key_value_pairs": {
            "box_1_wages": "$23,677.70",
            "box_2_federal_withheld": "$2,841.32",
            "box_3_ss_wages": "$23,677.70",
            "box_4_ss_tax": "$1,467.63",
            "box_5_medicare_wages": "$23,677.70",
            "box_6_medicare_tax": "$343.33",
        }
    },
    "filing_status": "single",
    "num_dependents": 0,
    "llm_provider": "gemini"
}

def test_endpoint():
    """Test the /process-with-llm endpoint"""
    print("=" * 80)
    print("Testing /api/tax/process-with-llm endpoint")
    print("=" * 80)
    
    print("\n📤 Sending request:")
    print(f"  URL: {ENDPOINT}")
    print(f"  Filing Status: {test_payload['filing_status']}")
    print(f"  Dependents: {test_payload['num_dependents']}")
    print(f"  LLM Provider: {test_payload['llm_provider']}")
    
    try:
        response = requests.post(
            ENDPOINT,
            json=test_payload,
            timeout=60
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS! Status 200")
            result = response.json()
            
            print("\n📊 Full Response:")
            print(json.dumps(result, indent=2)[:1000])  # Print first 1000 chars
            
            print("\n📊 Tax Calculation Results:")
            print(f"  Document Type: {result.get('document_type', 'N/A')}")
            print(f"  Status: {result.get('status', 'N/A')}")
            
            # Income
            income_total = result.get('income_total_income', 0)
            print(f"\n💰 Income:")
            print(f"  Total Income: ${income_total:,.2f}")
            
            # Withholding
            withholding = result.get('withholding_federal_withheld', 0)
            print(f"\n🧾 Withholding:")
            print(f"  Federal Withheld: ${withholding:,.2f}")
            
            # Taxes
            tax_liability = result.get('taxes_federal_income_tax', 0)
            print(f"\n📋 Tax Calculation:")
            print(f"  Federal Income Tax: ${tax_liability:,.2f}")
            
            # Result
            refund = result.get('refund_or_due', 0)
            result_status = result.get('result_status', 'UNKNOWN')
            print(f"\n💵 Result:")
            print(f"  Status: {result_status}")
            print(f"  Amount: ${abs(refund):,.2f}")
            
            print("\n✅ Test PASSED")
            return True
        else:
            print(f"❌ FAILED! Status {response.status_code}")
            print(f"\nError Response:")
            try:
                error = response.json()
                print(json.dumps(error, indent=2))
            except:
                print(response.text)
            return False
    
    except requests.exceptions.Timeout:
        print("❌ Request timed out (60 seconds)")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - Is the backend running?")
        print(f"   Make sure to run: cd api && python -m uvicorn main:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_endpoint()
    print("\n" + "=" * 80)
    if success:
        print("🎉 All tests PASSED!")
    else:
        print("⚠️  Tests FAILED - Check the error message above")
    print("=" * 80)

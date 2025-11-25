#!/usr/bin/env python3
"""
Test the LLM Tax Agent API
"""

import json
import requests
import sys

API_URL = "http://localhost:8000"

def test_single_1099_nec():
    """Test single 1099-NEC calculation"""
    
    print("\n" + "="*70)
    print("TEST: LLM Tax Agent - Single 1099-NEC")
    print("="*70)
    
    landingai_output = {
        "markdown": "Form 1099-NEC Nonemployee Compensation",
        "extracted_values": [
            {"text": "Box 1", "confidence": 0.95},
            {"text": "$6,750.00", "confidence": 0.98},
            {"text": "Box 4", "confidence": 0.92},
            {"text": "$1,550.00", "confidence": 0.97},
        ],
        "key_value_pairs": {
            "Box 1 (Nonemployee Compensation)": "$6,750.00",
            "Box 4 (Federal Withholding)": "$1,550.00",
        },
    }
    
    request_data = {
        "landingai_output": landingai_output,
        "filing_status": "single",
        "num_dependents": 0,
    }
    
    try:
        response = requests.post(
            f"{API_URL}/api/tax/calculate",
            json=request_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("status") == "success":
                print("\n✅ TEST PASSED\n")
                print("RESULTS:")
                print(f"  Income (1099-NEC): ${result['income_nonemployee_compensation']:,.2f}")
                print(f"  Taxable Income: ${result['taxable_income']:,.2f}")
                print(f"  Federal Tax: ${result['taxes_federal_income_tax']:,.2f}")
                print(f"  SE Tax: ${result['taxes_self_employment_tax']:,.2f}")
                print(f"  Total Tax: ${result['total_tax_liability']:,.2f}")
                print(f"  Federal Withheld: ${result['withholding_federal_withheld']:,.2f}")
                print(f"\n  {result['result_status']}")
                print(f"  Amount: ${result['result_amount']:,.2f}")
                
                # Validation
                expected_se_tax = 6750 * 0.9235 * 0.153
                actual_se_tax = result['taxes_self_employment_tax']
                
                if abs(expected_se_tax - actual_se_tax) < 0.01:
                    print(f"\n  ✅ SE Tax calculation correct: ${actual_se_tax:.2f}")
                else:
                    print(f"\n  ❌ SE Tax mismatch: expected ${expected_se_tax:.2f}, got ${actual_se_tax:.2f}")
                    return False
                
                return True
            else:
                print(f"\n❌ TEST FAILED")
                print(f"Error: {result.get('error_message')}")
                return False
        else:
            print(f"\n❌ API returned {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to API")
        print(f"Make sure FastAPI is running: python -m uvicorn api.main:app --reload")
        return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def test_w2_plus_1099():
    """Test combined W-2 + 1099-NEC"""
    
    print("\n" + "="*70)
    print("TEST: LLM Tax Agent - W-2 + 1099-NEC")
    print("="*70)
    
    landingai_output = {
        "markdown": "Form W-2 and 1099-NEC",
        "key_value_pairs": {
            "Box 1 (W-2 Wages)": "$50,000.00",
            "Box 2 (Federal Withholding W-2)": "$5,000.00",
            "Box 1 (1099-NEC)": "$20,000.00",
        },
    }
    
    request_data = {
        "landingai_output": landingai_output,
        "filing_status": "single",
        "num_dependents": 0,
    }
    
    try:
        response = requests.post(
            f"{API_URL}/api/tax/calculate",
            json=request_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("status") == "success":
                print("\n✅ TEST PASSED\n")
                print("RESULTS:")
                print(f"  W-2 Wages: ${result['income_wages']:,.2f}")
                print(f"  1099-NEC: ${result['income_nonemployee_compensation']:,.2f}")
                print(f"  Total Income: ${result['income_total_income']:,.2f}")
                print(f"  Taxable Income: ${result['taxable_income']:,.2f}")
                print(f"  Federal Tax: ${result['taxes_federal_income_tax']:,.2f}")
                print(f"  SE Tax: ${result['taxes_self_employment_tax']:,.2f}")
                print(f"  Total Tax: ${result['total_tax_liability']:,.2f}")
                
                # Validate SE tax on NEC only
                expected_se_tax = 20000 * 0.9235 * 0.153
                actual_se_tax = result['taxes_self_employment_tax']
                
                if abs(expected_se_tax - actual_se_tax) < 0.01:
                    print(f"\n  ✅ SE Tax calculated correctly on NEC only: ${actual_se_tax:.2f}")
                else:
                    print(f"\n  ❌ SE Tax mismatch: expected ${expected_se_tax:.2f}, got ${actual_se_tax:.2f}")
                    return False
                
                return True
            else:
                print(f"\n❌ TEST FAILED")
                print(f"Error: {result.get('error_message')}")
                return False
        else:
            print(f"\n❌ API returned {response.status_code}")
            return False
    
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to API")
        return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def test_api_health():
    """Test API health check"""
    
    print("\n" + "="*70)
    print("TEST: API Health Check")
    print("="*70)
    
    try:
        response = requests.get(
            f"{API_URL}/api/tax/health",
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ API is healthy")
            print(f"  Service: {result.get('service')}")
            print(f"  Status: {result.get('status')}")
            return True
        else:
            print(f"\n❌ API health check failed: {response.status_code}")
            return False
    
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to API at {API_URL}")
        print("\nTo start the API, run:")
        print("  cd api")
        print("  python -m uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def main():
    """Run all tests"""
    
    print("\n" + "="*70)
    print("LLM TAX AGENT - API TESTS")
    print("="*70)
    
    results = []
    
    # Test 1: Health check
    results.append(("API Health", test_api_health()))
    
    if not results[-1][1]:
        print("\n❌ API is not running. Please start it first:")
        print("  cd api")
        print("  python -m uvicorn main:app --reload")
        return 1
    
    # Test 2: Single 1099-NEC
    results.append(("Single 1099-NEC", test_single_1099_nec()))
    
    # Test 3: W-2 + 1099-NEC
    results.append(("W-2 + 1099-NEC", test_w2_plus_1099()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

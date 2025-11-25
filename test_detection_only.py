#!/usr/bin/env python3
"""
Simple test to verify all 1099 form type detection works
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'frontend', 'utils'))

from llm_tax_agent import detect_document_type, DocumentType

print("="*80)
print("[VERIFICATION] Document Type Detection for All Forms")
print("="*80)

# Test 1099-MISC specifically (the user's original problem)
print("\nTEST 1: 1099-MISC Detection (User's Original Issue)")
print("-" * 80)
misc_sample = """
Below is a Sample PDF 1099-MISC

FORM 1099-MISC - Miscellaneous Income

PAYER'S name: Sample Company 2012
RECIPIENT'S name: Doe, John

Box 1 Rents $0
Box 2 Royalties $0
Box 3 Other income $0
Box 7 Nonemployee compensation $5623.24
"""

detected = detect_document_type(misc_sample)
print(f"Detected: {detected.value}")
print(f"Expected: 1099-MISC")
status = "PASS" if detected == DocumentType.FORM_1099_MISC else "FAIL"
print(f"Status: [{status}]")

# Test all form types
print("\nTEST 2: All Form Types Detection")
print("-" * 80)

test_cases = [
    ("W-2", "Form W-2 Wage and Tax Statement Box 1 Wages: $50,000", DocumentType.W2),
    ("1099-NEC", "FORM 1099-NEC Nonemployee Compensation Box 1: $12,000", DocumentType.FORM_1099_NEC),
    ("1099-INT", "Form 1099-INT Interest Income Box 1 Interest: $500", DocumentType.FORM_1099_INT),
    ("1099-DIV", "FORM 1099-DIV Dividend Income Qualified Dividends: $1,000", DocumentType.FORM_1099_DIV),
    ("1099-B", "Form 1099-B Brokerage Transactions Total Proceeds: $50,000", DocumentType.FORM_1099_B),
    ("1099-MISC", "1099-MISC Miscellaneous Income Royalties: $2,000", DocumentType.FORM_1099_MISC),
    ("1099-K", "Form 1099-K Payment Card Transactions Card Not Present: $100,000", DocumentType.FORM_1099_K),
    ("1099-OID", "1099-OID Original Issue Discount Box 1: $500", DocumentType.FORM_1099_OID),
]

passed = 0
for form_name, sample, expected_type in test_cases:
    detected = detect_document_type(sample)
    if detected == expected_type:
        passed += 1
        print(f"  {form_name:12} -> {detected.value:15} [PASS]")
    else:
        print(f"  {form_name:12} -> {detected.value:15} [FAIL]")
        print(f"    Expected: {expected_type.value}")

print(f"\nResult: {passed}/{len(test_cases)} tests passed")

print("\n" + "="*80)
print("[SUMMARY]")
print("="*80)

# Check 1099-MISC detection from original sample
detected_misc = detect_document_type(misc_sample)
misc_status = "FIXED - Now detects as 1099-MISC" if detected_misc == DocumentType.FORM_1099_MISC else "NOT FIXED"

print(f"""
Detection Capability: {'VERIFIED' if passed == len(test_cases) else 'NEEDS FIX'}

System now supports:
  - W-2 (Wages and Tax Statement)
  - 1099-NEC (Nonemployee Compensation)
  - 1099-INT (Interest Income)
  - 1099-DIV (Dividend Income)
  - 1099-B (Brokerage Transactions)
  - 1099-MISC (Miscellaneous Income) <-- FIXED
  - 1099-K (Payment Card Transactions)
  - 1099-OID (Original Issue Discount)

Your 1099-MISC issue: {misc_status}
""")

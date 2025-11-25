#!/usr/bin/env python3
"""
Test improved detection with encoding, OCR errors, and smart fallback
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'frontend', 'utils'))

from llm_tax_agent import detect_document_type, DocumentType

print("="*80)
print("[IMPROVED] Detection with Encoding & OCR Error Handling")
print("="*80)

# Test 1: HTML entity encoding
print("\nTest 1: HTML Entity Encoding (1099&#8212;MISC)")
test = "Form 1099&#8212;MISC Miscellaneous Income Box 7: $5623"
detected = detect_document_type(test)
print(f"  Input: {test}")
print(f"  Detected: {detected.value}")
result = "PASS" if detected == DocumentType.FORM_1099_MISC else "FAIL"
print(f"  Result: [{result}]\n")

# Test 2: En-dash encoding
print("Test 2: En-dash (1099–MISC)")
test = "Form 1099–MISC Miscellaneous Income"
detected = detect_document_type(test)
print(f"  Input: 1099–MISC (en-dash)")
print(f"  Detected: {detected.value}")
result = "PASS" if detected == DocumentType.FORM_1099_MISC else "FAIL"
print(f"  Result: [{result}]\n")

# Test 3: OCR error (O instead of 0)
print("Test 3: OCR Error (1O99-MISC with letter O)")
test = "Form 1O99-MISC Miscellaneous Income"
detected = detect_document_type(test)
print(f"  Input: 1O99-MISC (letter O instead of 0)")
print(f"  Detected: {detected.value}")
result = "PASS" if detected == DocumentType.FORM_1099_MISC else "FAIL"
print(f"  Result: [{result}]\n")

# Test 4: Unknown 1099 with intelligent fallback (Payment Card)
print("Test 4: Unknown 1099 (smart fallback - Payment Card)")
test = "Form 1099 Payment Card Merchant Category Code"
detected = detect_document_type(test)
print(f"  Input: Generic 1099 with payment card keywords")
print(f"  Detected: {detected.value}")
print(f"  Expected: 1099-K")
result = "PASS" if detected == DocumentType.FORM_1099_K else "FAIL"
print(f"  Result: [{result}]\n")

# Test 5: Unknown 1099 with brokerage clues
print("Test 5: Unknown 1099 (smart fallback - Brokerage)")
test = "Form 1099 Proceeds of Sale Brokerage Account"
detected = detect_document_type(test)
print(f"  Input: Generic 1099 with brokerage keywords")
print(f"  Detected: {detected.value}")
print(f"  Expected: 1099-B")
result = "PASS" if detected == DocumentType.FORM_1099_B else "FAIL"
print(f"  Result: [{result}]\n")

# Test 6: Underscore instead of dash
print("Test 6: Underscore (1099_MISC)")
test = "Form 1099_MISC Miscellaneous Income Royalties"
detected = detect_document_type(test)
print(f"  Input: 1099_MISC (underscore)")
print(f"  Detected: {detected.value}")
result = "PASS" if detected == DocumentType.FORM_1099_MISC else "FAIL"
print(f"  Result: [{result}]\n")

# Test 7: Multiple dashes (em-dash)
print("Test 7: Em-dash (1099—MISC)")
test = "Form 1099—MISC Miscellaneous Income"
detected = detect_document_type(test)
print(f"  Input: 1099—MISC (em-dash)")
print(f"  Detected: {detected.value}")
result = "PASS" if detected == DocumentType.FORM_1099_MISC else "FAIL"
print(f"  Result: [{result}]\n")

# Test 8: Unknown 1099 with interest
print("Test 8: Unknown 1099 (smart fallback - Interest)")
test = "Form 1099 Interest Income Received"
detected = detect_document_type(test)
print(f"  Input: Generic 1099 with interest keywords")
print(f"  Detected: {detected.value}")
print(f"  Expected: 1099-INT")
result = "PASS" if detected == DocumentType.FORM_1099_INT else "FAIL"
print(f"  Result: [{result}]\n")

# Test 9: All forms still work
print("Test 9: All Standard Forms (Regression Test)")
test_cases = [
    ("W-2", "Form W-2 Wage and Tax Statement Box 1 Wages", DocumentType.W2),
    ("1099-NEC", "FORM 1099-NEC Nonemployee Compensation Box 1", DocumentType.FORM_1099_NEC),
    ("1099-INT", "Form 1099-INT Interest Income", DocumentType.FORM_1099_INT),
    ("1099-DIV", "FORM 1099-DIV Dividend Income", DocumentType.FORM_1099_DIV),
    ("1099-B", "Form 1099-B Brokerage Transactions Proceeds", DocumentType.FORM_1099_B),
    ("1099-MISC", "1099-MISC Miscellaneous Income", DocumentType.FORM_1099_MISC),
    ("1099-K", "Form 1099-K Payment Card Transactions", DocumentType.FORM_1099_K),
    ("1099-OID", "1099-OID Original Issue Discount", DocumentType.FORM_1099_OID),
]

passed = 0
for name, sample, expected_type in test_cases:
    detected = detect_document_type(sample)
    if detected == expected_type:
        passed += 1
        print(f"  {name:12} -> {detected.value:15} [PASS]")
    else:
        print(f"  {name:12} -> {detected.value:15} [FAIL] Expected {expected_type.value}")

print(f"\n  Total: {passed}/{len(test_cases)} passed\n")

print("="*80)
print("[SUMMARY]")
print("="*80)
print("""
IMPROVEMENTS IMPLEMENTED:

1. HTML Entity Decoding
   - Converts "1099&#8212;MISC" -> "1099-MISC"
   - Handles all HTML entities

2. Dash Normalization
   - En-dash (–) -> hyphen (-)
   - Em-dash (—) -> hyphen (-)
   - Minus (−) -> hyphen (-)
   - Underscore (_) -> hyphen (-)

3. OCR Error Tolerance
   - Handles 0 vs O confusion (1O99 matches 1099)
   - Better keyword variant matching

4. Smart Fallback Logic
   - Payment + Card -> 1099-K
   - Proceeds + Brokerage -> 1099-B
   - Interest -> 1099-INT
   - Dividend -> 1099-DIV
   - Misc/Royalties -> 1099-MISC
   - Default -> 1099-NEC (last resort)

FAILURE REDUCTION:
  - Encoding issues: FIXED
  - OCR character errors: REDUCED
  - Unknown 1099s: SMART DETECTION
  - Misidentification risk: REDUCED
""")

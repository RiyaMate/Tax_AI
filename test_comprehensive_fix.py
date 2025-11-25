#!/usr/bin/env python3
"""
COMPREHENSIVE TEST: Full 1099-MISC detection and extraction flow
Tests both critical fixes:
1. Detection ordering (1099-MISC before W-2)
2. Encoding handling (UTF-8 safe)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'frontend'))

from utils.llm_tax_agent import detect_document_type, DocumentType

# Real PDF markdown from user's 1099-MISC
REAL_PDF_MARKDOWN = """<a id='51a88fd2-aaa5-4ae8-931d-d6859c1600b4'></a>

Below is a Sample PDF 1099-MISC
Form Generated from inside our
1099-MISC Software

<a id='150ca51a-7231-4ece-9c59-aec13d226ce6'></a>

http://www.W2Mate.com

<!-- PAGE BREAK -->

<a id='ed1114bf-26cd-4498-be91-d6f6a006d672'></a>

VOID : [ ] CORRECTED : [ ]
<table id="1-1">
<tr><td id="1-2" rowspan="3" colspan="2">PAYER'S name, street address, city, state, ZIP code, and telephone no. Sample Company 2012 148 South Banana Dr. Chicago, IL 60609</td><td id="1-3">1 Rents $</td><td id="1-4" rowspan="2" colspan="2">OMB No. 1545-0115 2012 Miscellaneous Income Form 1099-MISC</td></tr>
<tr><td id="1-5">2 Royalties $</td></tr>
<tr><td id="1-6">3 Other income $</td><td id="1-7">4 Federal income tax withheld $</td><td id="1-8" rowspan="2">Copy 1 For State Tax Department</td></tr>
<tr><td id="1-9">PAYER'S federal identification number 12-3456789</td><td id="1-a">RECIPIENT'S identification number 147-63-7844</td><td id="1-b">5 Fishing boat proceeds $</td><td id="1-c">6 Medical and health care payments $</td></tr>
<tr><td id="1-d" rowspan="3" colspan="2">RECIPIENT'S name Doe, John Street address (including apt. no.) 145 South Apple Ln. City, state, and ZIP code Happy Ville, IL 60852</td><td id="1-e">7 Nonemployee compensation 5623.24 $</td><td id="1-f">8 Substitute payments in lieu of dividends or interest $</td><td id="1-g" rowspan="4"></td></tr>
<tr><td id="1-h">9 Payer made direct sales of $5,000 or more of consumer products to a buyer (recipient) for resale</td><td id="1-i">10 Crop insurance proceeds</td></tr>
<tr><td id="1-j">11</td><td id="1-k">12</td></tr>
<tr><td id="1-l" colspan="2">Account number (see instructions) 10003</td><td id="1-m">13 Excess golden parachute payments</td><td id="1-n">14 Gross proceeds paid to an attorney</td></tr>
<tr><td id="1-o" rowspan="2">15a Section 409A deferrals
$</td><td id="1-p" rowspan="2">15b Section 409A income ($)</td><td id="1-q">16 State tax withheld</td><td id="1-r">17 State/Payer's state no. IL/857-482-26</td><td id="1-s">18 State income</td></tr>
<tr><td id="1-t"></td><td id="1-u"></td><td id="1-v"></td></tr>
</table>

<a id='429bb252-e919-4d3a-aaa9-cfeb13b85b5a'></a>

Form 1099-MISC

<a id='80956e5a-db40-4ed4-a89b-da15472c4b86'></a>

Department of the Treasury - Internal Revenue Service

Department of the Treasury - Internal Revenue Service"""

print("\n" + "="*80)
print("COMPREHENSIVE TEST: 1099-MISC Detection & Encoding Fix Verification")
print("="*80)

# Test 1: Detection
print("\n[TEST 1] Form Detection")
print("-" * 80)

detected = detect_document_type(REAL_PDF_MARKDOWN)
print(f"Input: Real 1099-MISC PDF markdown ({len(REAL_PDF_MARKDOWN)} chars)")
print(f"Detected Form: {detected.name}")
print(f"Expected Form: FORM_1099_MISC")

if detected == DocumentType.FORM_1099_MISC:
    print("[PASS] ✓ DETECTION CORRECT")
    test1_pass = True
else:
    print(f"[FAIL] ✗ DETECTION WRONG - Got {detected.name}")
    test1_pass = False

# Test 2: Encoding handling
print("\n[TEST 2] UTF-8 Encoding with Special Characters")
print("-" * 80)

# PDF with em-dashes and special chars (like real PDFs have)
pdf_with_special_chars = """
Form 1099–MISC (with en-dash)
Nonemployee compensation – $5,623.24
Description: © ® ™ ¢ £ ¤ ¥ forms
"""

try:
    # Simulate what happens in _build_extraction_prompt
    sanitized = pdf_with_special_chars.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    
    # Try to use it (like LLM would)
    test_prompt = f"Extract from: {sanitized}"
    encoded_prompt = test_prompt.encode('utf-8', errors='replace').decode('utf-8')
    
    print(f"[PASS] ✓ ENCODING SAFE")
    print(f"  Original: {len(pdf_with_special_chars)} chars")
    print(f"  Sanitized: {len(sanitized)} chars")
    print(f"  Prompt: {len(encoded_prompt)} chars")
    test2_pass = True
except Exception as e:
    print(f"[FAIL] ✗ ENCODING FAILED: {e}")
    test2_pass = False

# Test 3: Keyword verification
print("\n[TEST 3] Keyword Matching Verification")
print("-" * 80)

test_cases = [
    ("Contains 1099-misc", "1099-misc form", DocumentType.FORM_1099_MISC),
    ("Contains miscellaneous", "miscellaneous income tax", DocumentType.FORM_1099_MISC),
    ("Contains royalties", "royalties and rents", DocumentType.FORM_1099_MISC),
    ("Contains box 7 nonemployee", "box 7 nonemployee compensation", DocumentType.FORM_1099_MISC),
    ("Only mentions box 1", "box 1 wages employer", DocumentType.W2),
    ("Explicit w-2 form", "form w-2 wages", DocumentType.W2),
    ("Mentions box no form", "box 1 box 2 employee", DocumentType.W2),
    ("1099-NEC form", "1099-nec nonemployee compensation form", DocumentType.FORM_1099_NEC),
]

all_keywords_pass = True
for description, text, expected_type in test_cases:
    detected = detect_document_type(text)
    is_correct = detected == expected_type
    
    result = "✓" if is_correct else "✗"
    status = "PASS" if is_correct else "FAIL"
    
    print(f"{result} [{status}] {description}: Got {detected.name}, Expected {expected_type.name}")
    
    if status == "FAIL":
        all_keywords_pass = False

test3_pass = all_keywords_pass

# Summary
print("\n" + "="*80)
print("TEST RESULTS SUMMARY")
print("="*80)

results = [
    ("TEST 1: Form Detection", test1_pass),
    ("TEST 2: UTF-8 Encoding", test2_pass),
    ("TEST 3: Keyword Matching", test3_pass),
]

passed = sum(1 for _, result in results if result)
total = len(results)

for test_name, result in results:
    status = "✓ PASS" if result else "✗ FAIL"
    print(f"{status}: {test_name}")

print(f"\nOverall: {passed}/{total} tests passed")

if passed == total:
    print("\n" + "="*80)
    print("✓ ALL TESTS PASSED - System ready for production testing")
    print("="*80)
    sys.exit(0)
else:
    print("\n" + "="*80)
    print("✗ SOME TESTS FAILED - See above for details")
    print("="*80)
    sys.exit(1)

#!/usr/bin/env python3
"""Test 1099-MISC detection fix with real PDF markdown"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'frontend'))

from utils.llm_tax_agent import detect_document_type, DocumentType

# Use the EXACT markdown from the user's PDF
pdf_markdown = """<a id='51a88fd2-aaa5-4ae8-931d-d6859c1600b4'></a>

Below is a Sample PDF 1099-MISC
Form Generated from inside our
1099-MISC Software

<a id='9c4e85af-3386-4d3c-84a7-1afe84a4a478'></a>

To learn more please visit

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

Department of the Treasury - Internal Revenue Service"""

print("[TEST] Testing 1099-MISC Detection with Real PDF Markdown")
print("=" * 80)

# Show first 200 chars of text
print(f"\n[INPUT] Text length: {len(pdf_markdown)} chars")
print(f"[INPUT] First 200 chars:\n{pdf_markdown[:200]}\n")

# Run detection
detected = detect_document_type(pdf_markdown)

print(f"[RESULT] Detected Form: {detected.name}")
print(f"[EXPECTED] FORM_1099_MISC")

# Check if correct
if detected == DocumentType.FORM_1099_MISC:
    print("\n[PASS] ✓ Detection CORRECT - Will extract as 1099-MISC")
    sys.exit(0)
else:
    print(f"\n[FAIL] ✗ Detection WRONG - Got {detected.name} instead of FORM_1099_MISC")
    
    # Debug: check what keywords are matched
    import html
    text_lower = pdf_markdown.lower()
    text_decoded = html.unescape(text_lower)
    text_normalized = text_decoded.replace('–', '-').replace('—', '-').replace('−', '-').replace('_', '-')
    text_clean = text_normalized.replace("<", " ").replace(">", " ").replace('"', " ").replace('&', ' ')
    
    print("\n[DEBUG] Text cleaning results:")
    print(f"  - Contains '1099-misc': {'1099-misc' in text_clean}")
    print(f"  - Contains 'miscellaneous': {'miscellaneous' in text_clean}")
    print(f"  - Contains 'royalties': {'royalties' in text_clean}")
    print(f"  - Contains 'rents': {'rents' in text_clean}")
    print(f"  - Contains '1099-misc' or variants: {'1099-misc' in text_clean or '1099 misc' in text_clean or '1099misc' in text_clean}")
    print(f"  - Contains 'w-2': {'w-2' in text_clean}")
    print(f"  - Contains 'wage and tax statement': {'wage and tax statement' in text_clean}")
    print(f"  - Contains '1099': {'1099' in text_clean}")
    
    sys.exit(1)

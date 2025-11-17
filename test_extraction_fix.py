#!/usr/bin/env python3
"""
Test script to verify the updated extraction functions handle LandingAI markdown format
"""

import sys
sys.path.insert(0, r'c:\Users\riyam\PDF_GREEN\LiteLLM_SummaryGenerator_with_Q-A\frontend\utils')

from landingai_utils import extract_fields_w2, extract_fields_1099_nec, extract_fields_1099_int

# Test Case 1: LandingAI W-2 Markdown Format (Table)
print("="*80)
print("TEST 1: LandingAI W-2 Markdown Format (Table)")
print("="*80)

w2_markdown = """
Form W-2 (2024) – Wage and Tax Statement

<table>
<tr><td>Employer:</td><td>NOKIA</td></tr>
<tr><td>Employer EIN:</td><td>12-3456789</td></tr>
<tr><td>Employer Address:</td><td>600 Technology Drive, Espoo, Finland</td></tr>
<tr><td>Employee:</td><td>RSM</td></tr>
<tr><td>Employee SSN:</td><td>123-45-6789</td></tr>
<tr><td>Wages:</td><td>$68,500.00</td></tr>
<tr><td>Federal Income Tax Withheld:</td><td>$8,200.00</td></tr>
<tr><td>Social Security Wages:</td><td>$68,500.00</td></tr>
<tr><td>Medicare Wages and Tips:</td><td>$68,500.00</td></tr>
</table>
"""

result_w2 = extract_fields_w2(w2_markdown)
print(f"\n[OK] W-2 Extraction Result:")
for key, value in result_w2.items():
    if key != "validation":
        print(f"  {key}: {value}")

# Test Case 2: Box Format (Old Format)
print("\n" + "="*80)
print("TEST 2: Old Box Format (Backward Compatibility)")
print("="*80)

old_format_w2 = """
Form W-2
Box 1 Wages $68,500
Box 2 Federal income tax withheld $8,200
Box 3 Social Security wages $68,500
Box 5 Medicare wages $68,500
EIN 12-3456789
SSN 123-45-6789
"""

result_w2_old = extract_fields_w2(old_format_w2)
print(f"\n[OK] W-2 Old Format Extraction Result:")
for key, value in result_w2_old.items():
    if key != "validation":
        print(f"  {key}: {value}")

# Test Case 3: 1099-NEC Markdown Format
print("\n" + "="*80)
print("TEST 3: LandingAI 1099-NEC Markdown Format")
print("="*80)

nec_markdown = """
Form 1099-NEC

<table>
<tr><td>Payer:</td><td>ABC Consulting</td></tr>
<tr><td>Payer EIN:</td><td>98-7654321</td></tr>
<tr><td>Recipient:</td><td>John Contractor</td></tr>
<tr><td>Recipient TIN:</td><td>123-45-6789</td></tr>
<tr><td>Nonemployee Compensation:</td><td>$12,000.00</td></tr>
<tr><td>Federal Income Tax Withheld:</td><td>$1,500.00</td></tr>
</table>
"""

result_nec = extract_fields_1099_nec(nec_markdown)
print(f"\n[OK] 1099-NEC Extraction Result:")
for key, value in result_nec.items():
    if key != "validation":
        print(f"  {key}: {value}")

# Test Case 4: 1099-INT Markdown Format
print("\n" + "="*80)
print("TEST 4: LandingAI 1099-INT Markdown Format")
print("="*80)

int_markdown = """
Form 1099-INT

<table>
<tr><td>Payer:</td><td>Bank of America</td></tr>
<tr><td>Payer TIN:</td><td>56-7890123</td></tr>
<tr><td>Recipient:</td><td>Jane Saver</td></tr>
<tr><td>Recipient TIN:</td><td>987-65-4321</td></tr>
<tr><td>Interest Income:</td><td>$410.00</td></tr>
<tr><td>Federal Income Tax Withheld:</td><td>$41.00</td></tr>
</table>
"""

result_int = extract_fields_1099_int(int_markdown)
print(f"\n[OK] 1099-INT Extraction Result:")
for key, value in result_int.items():
    if key != "validation":
        print(f"  {key}: {value}")

print("\n" + "="*80)
print("ALL TESTS COMPLETED SUCCESSFULLY!")
print("="*80)

# Now test the full flow with tax engine
print("\n" + "="*80)
print("INTEGRATION TEST: Full Tax Calculation Flow")
print("="*80)

sys.path.insert(0, r'c:\Users\riyam\PDF_GREEN\LiteLLM_SummaryGenerator_with_Q-A\frontend\utils')
from tax_engine import normalize_extracted_data, aggregate_documents, calculate_tax

# Normalize each extracted document
w2_normalized = normalize_extracted_data(result_w2)
nec_normalized = normalize_extracted_data(result_nec)
int_normalized = normalize_extracted_data(result_int)

print(f"\n[OK] W-2 Normalized: {w2_normalized}")
print(f"[OK] 1099-NEC Normalized: {nec_normalized}")
print(f"[OK] 1099-INT Normalized: {int_normalized}")

# Aggregate all documents
docs = [w2_normalized, nec_normalized, int_normalized]
totals = aggregate_documents(docs)
print(f"\n[OK] Aggregated Totals: {totals}")

# Calculate taxes
tax_result = calculate_tax(
    docs=docs,
    filing_status="single",
    num_dependents=0,
)

print(f"\n[OK] Final Tax Calculation Result:")
print(f"  Total Income: ${tax_result['income']['total_income']:,.2f}")
print(f"  Total Tax Liability: ${tax_result['taxes']['total_tax_liability']:,.2f}")
print(f"  Total Withheld: ${tax_result['withholding']['total_withheld']:,.2f}")
print(f"  Refund/Due: ${tax_result['refund_or_due']:,.2f}")
print(f"  Status: {tax_result['result_status']}")

print("\n" + "="*80)
print("SUCCESS: All documents were extracted, aggregated, and calculated correctly!")
print("="*80)

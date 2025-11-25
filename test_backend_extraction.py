#!/usr/bin/env python3
"""
Direct backend test to verify regex extraction works
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv(override=True)

# Test direct backend extraction
from llm_tax_agent import LLMTaxAgent, detect_document_type, DocumentType

# Test data with key-value pairs (best format for regex extraction)
test_data = {
    "markdown": """
    FORM W-2 Wage and Tax Statement 2024
    
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
}

print("=" * 80)
print("Direct Backend Test - W-2 Extraction")
print("=" * 80)

# Test document detection
print("\n[STEP 1] Detect Document Type")
doc_type = detect_document_type(test_data)
print(f"  Detected: {doc_type.value}")
assert doc_type == DocumentType.W2, f"Expected W2, got {doc_type}"
print("  ✓ Correct document type")

# Test processing
print("\n[STEP 2] Process LandingAI Output")
agent = LLMTaxAgent()
result = agent.process_landingai_output(
    test_data,
    filing_status="single",
    num_dependents=0
)

print("\n[STEP 3] Verify Results")
print(f"  Income (Wages): ${result['income_wages']:,.2f}")
print(f"  Expected: $23,677.70")
assert result['income_wages'] == 23677.70, f"Wages mismatch: {result['income_wages']}"
print("  ✓ Wages extracted correctly")

print(f"\n  Federal Withheld: ${result['withholding_federal_withheld']:,.2f}")
print(f"  Expected: $2,841.32")
assert result['withholding_federal_withheld'] == 2841.32, f"Withholding mismatch"
print("  ✓ Withholding extracted correctly")

print(f"\n  Total Income: ${result['income_total_income']:,.2f}")
print(f"  Taxable Income: ${result['taxable_income']:,.2f}")
print(f"  Federal Tax: ${result['taxes_federal_income_tax']:,.2f}")
print(f"  Refund/Due: ${result['refund_or_due']:,.2f}")

print("\n✓ All assertions passed!")
print("=" * 80)

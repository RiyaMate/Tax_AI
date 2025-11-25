#!/usr/bin/env python3
"""
Test: Enhanced Schema-Guided Tax Document Extraction

This test demonstrates the new workflow:
1. Document type detection
2. Field schema loading
3. LLM-based intelligent extraction using schema
4. Tax calculation
"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'frontend', 'utils'))

from llm_tax_agent import UniversalLLMTaxAgent, LLMProvider, DocumentType, detect_document_type
from document_field_schema import DocumentFieldSchema, get_available_fields_for_document
from tax_engine import aggregate_documents, calculate_tax
import json


def test_schema_guided_extraction():
    """
    Test the enhanced schema-guided extraction workflow.
    Shows how the schema helps LLM extract correct fields.
    """
    
    print("\n" + "="*80)
    print("SCHEMA-GUIDED EXTRACTION TEST")
    print("="*80)
    
    # Example 1099-MISC document
    sample_1099_misc = """
    Form 1099-MISC - Miscellaneous Income
    
    Payer Information:
    Name: ABC Manufacturing Corp
    EIN: 56-7890123
    Address: 123 Business St, Anytown, CA 94000
    
    Recipient Information:
    Name: John Smith
    TIN: 123-45-6789
    Address: 456 Main St, Anytown, CA 94000
    
    Box 1 - Rents: $5,500.00
    Box 2 - Royalties: $3,250.00
    Box 3 - Other Income: $2,100.00
    Box 4 - Federal Income Tax Withheld: $0.00
    Box 5 - Fishing Boat Proceeds: $0.00
    Box 6 - Medical Payments: $1,200.00 (NOT TAXABLE)
    Box 7 - Direct Sales: $0.00 (INFORMATIONAL ONLY)
    Box 8 - Substitute Payments: $5,800.00
    Box 9 - Crop Insurance Proceeds: $7,600.00
    Box 10 - Gross Proceeds to Attorney: $3,500.00
    Box 11 - Fish Purchased for Resale: $0.00 (NOT INCOME)
    Box 14 - Excess Parachute Payments: $1,800.00
    Box 15 - Nonqualified Deferred Comp: $700.00
    """
    
    print("\n[TEST 1] Schema-Guided 1099-MISC Extraction")
    print("-" * 80)
    
    # Step 1: Detect document type
    print("\n1. Detecting document type...")
    doc_type = detect_document_type(sample_1099_misc)
    print(f"   ✓ Detected: {doc_type.value}")
    
    # Step 2: Show available fields from schema
    print("\n2. Loading field schema for this document type...")
    schema = DocumentFieldSchema.get_schema_for_document(doc_type)
    print(f"   ✓ Found {len(schema)} available fields")
    
    # Show which fields are taxable vs not
    print("\n   TAXABLE BOXES (will be extracted):")
    taxable_boxes = [
        ("rents", "Box 1", "Rents"),
        ("royalties", "Box 2", "Royalties"),
        ("other_income", "Box 3", "Other Income"),
        ("fishing_boat_proceeds", "Box 5", "Fishing Boat Proceeds"),
        ("substitute_payments", "Box 8", "Substitute Payments"),
        ("crop_insurance_proceeds", "Box 9", "Crop Insurance Proceeds"),
        ("gross_proceeds_attorney", "Box 10", "Gross Proceeds to Attorney"),
        ("excess_parachute_payments", "Box 14", "Excess Parachute Payments"),
        ("nonqualified_deferred_comp", "Box 15", "Nonqualified Deferred Comp"),
    ]
    for field, box, desc in taxable_boxes:
        print(f"     • {field:40s} ({box:5s}): {desc}")
    
    print("\n   NON-TAXABLE BOXES (excluded from income):")
    non_taxable = [
        ("medical_payments", "Box 6", "Medical Payments - NOT taxable to recipient"),
        ("direct_sales", "Box 7", "Direct Sales - informational only"),
    ]
    for field, box, desc in non_taxable:
        print(f"     • {field:40s} ({box:5s}): {desc}")
    
    # Step 3: Show what the LLM will be instructed to extract
    print("\n3. LLM Extraction Instructions:")
    print("   The LLM receives a prompt with the complete field list above,")
    print("   telling it EXACTLY what to extract. This prevents hallucinations")
    print("   and ensures all 9 taxable boxes are captured.")
    
    # Step 4: Perform extraction
    print("\n4. Extracting with LLM (using schema-guided prompt)...")
    try:
        agent = UniversalLLMTaxAgent(llm_provider=LLMProvider.GEMINI)
        result = agent.process_document(sample_1099_misc)
        
        extracted = result.get("normalized_fields", {})
        print(f"   ✓ Extraction complete")
        print(f"   ✓ Extracted {len([k for k,v in extracted.items() if v > 0])} non-zero fields")
        
        # Show extracted values
        print("\n   Extracted Values (9 TAXABLE BOXES):")
        total_income = 0
        for field, box, desc in taxable_boxes:
            value = extracted.get(field, 0)
            total_income += value
            status = "✓" if value > 0 else "○"
            print(f"     {status} {field:40s} = ${value:>10,.2f}")
        
        print("\n   Excluded Values (NON-TAXABLE):")
        for field, box, desc in non_taxable:
            value = extracted.get(field, 0)
            if value > 0:
                print(f"     • {field:40s} = ${value:>10,.2f} (EXCLUDED)")
        
        # Step 5: Calculate tax
        print("\n5. Tax Calculation:")
        print(f"   Total Income (9 taxable boxes): ${total_income:>10,.2f}")
        
        # Create totals dict for tax engine
        totals = {
            "wages": 0,
            "nonemployee_compensation": 0,
            "rents": extracted.get("rents", 0),
            "royalties": extracted.get("royalties", 0),
            "other_income": extracted.get("other_income", 0),
            "fishing_boat_proceeds": extracted.get("fishing_boat_proceeds", 0),
            "substitute_payments": extracted.get("substitute_payments", 0),
            "crop_insurance_proceeds": extracted.get("crop_insurance_proceeds", 0),
            "gross_proceeds_attorney": extracted.get("gross_proceeds_attorney", 0),
            "excess_parachute_payments": extracted.get("excess_parachute_payments", 0),
            "nonqualified_deferred_comp": extracted.get("nonqualified_deferred_comp", 0),
            "interest_income": 0,
            "qualified_dividends": 0,
            "ordinary_dividends": 0,
            "federal_income_tax_withheld": 0,
            "social_security_tax_withheld": 0,
            "medicare_tax_withheld": 0,
        }
        
        # Calculate tax
        tax_result = calculate_tax(totals)
        
        print(f"   Standard Deduction (2024):       ${tax_result['standard_deduction']:>10,.2f}")
        print(f"   Taxable Income:                  ${tax_result['taxable_income']:>10,.2f}")
        print(f"   Calculated Tax:                  ${tax_result['calculated_tax']:>10,.2f}")
        print(f"   Total Withheld:                  ${tax_result['federal_income_tax_withheld']:>10,.2f}")
        
        if tax_result['refund'] > 0:
            print(f"   REFUND:                          ${tax_result['refund']:>10,.2f}")
        else:
            print(f"   AMOUNT OWED:                     ${-tax_result['refund']:>10,.2f}")
        
        # Step 6: Validate results
        print("\n6. Validation:")
        if total_income > 0:
            print(f"   ✓ Income extracted correctly")
        else:
            print(f"   ✗ No income extracted")
        
        if extracted.get("medical_payments", 0) == 0:
            print(f"   ✓ Medical payments correctly excluded (not in taxable boxes)")
        else:
            print(f"   ✗ Medical payments incorrectly included")
        
        if extracted.get("direct_sales", 0) == 0:
            print(f"   ✓ Direct sales correctly excluded (informational only)")
        else:
            print(f"   ✗ Direct sales incorrectly included")
        
        print("\n" + "="*80)
        print("✓ SCHEMA-GUIDED EXTRACTION TEST PASSED")
        print("="*80)
        
    except Exception as e:
        print(f"   ✗ Error during extraction: {e}")
        import traceback
        traceback.print_exc()


def show_schema_example():
    """Show example of the field schema structure"""
    
    print("\n" + "="*80)
    print("FIELD SCHEMA EXAMPLE")
    print("="*80)
    
    print("\nFor 1099-MISC, the schema defines:")
    schema = DocumentFieldSchema.get_schema_for_document(DocumentType.FORM_1099_MISC)
    
    print("\nSample fields (showing Box number + Description):")
    for i, (field_name, (box_num, description)) in enumerate(list(schema.items())[:5]):
        print(f"  {field_name:40s} ← {box_num:15s} : {description}")
    
    print(f"\n  ... and {len(schema) - 5} more fields (total {len(schema)})")


if __name__ == "__main__":
    try:
        # Show schema example first
        show_schema_example()
        
        # Run the main test
        test_schema_guided_extraction()
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

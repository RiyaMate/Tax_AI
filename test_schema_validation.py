"""
SCHEMA VALIDATION TEST - No LLM Required
Tests that DocumentFieldSchema has all required fields for all document types
"""

import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'frontend', 'utils'))

from llm_tax_agent import DocumentType
from document_field_schema import DocumentFieldSchema, get_available_fields_for_document


def test_schema_structure():
    """Test that schema has all required document types"""
    print("\n" + "="*80)
    print("TEST 1: SCHEMA STRUCTURE VALIDATION")
    print("="*80)
    
    required_docs = [
        DocumentType.W2,
        DocumentType.FORM_1099_NEC,
        DocumentType.FORM_1099_MISC,
        DocumentType.FORM_1099_INT,
        DocumentType.FORM_1099_DIV,
        DocumentType.FORM_1099_B,
        DocumentType.FORM_1099_K,
        DocumentType.FORM_1099_OID,
    ]
    
    print("\nChecking DocumentType coverage:")
    all_present = True
    for doc_type in required_docs:
        schema = DocumentFieldSchema.get_schema_for_document(doc_type)
        field_count = len(schema)
        status = "✓" if field_count > 0 else "✗"
        print(f"  {status} {doc_type.value:20} → {field_count:3} fields")
        if field_count == 0:
            all_present = False
    
    if all_present:
        print("\n✓ All required document types have schemas!")
    else:
        print("\n✗ Some document types are missing schemas!")
    
    return all_present


def test_w2_fields():
    """Test W-2 has all critical fields"""
    print("\n" + "="*80)
    print("TEST 2: W-2 FIELD COMPLETENESS")
    print("="*80)
    
    schema = DocumentFieldSchema.get_schema_for_document(DocumentType.W2)
    
    required_w2_fields = [
        "wages",
        "federal_income_tax_withheld",
        "social_security_wages",
        "social_security_tax_withheld",
        "medicare_wages",
        "medicare_tax_withheld",
    ]
    
    print(f"\nW-2 Schema has {len(schema)} total fields")
    print("\nChecking critical fields:")
    
    all_present = True
    for field in required_w2_fields:
        if field in schema:
            box, desc = schema[field]
            print(f"  ✓ {field:40} ({box:15}) {desc}")
        else:
            print(f"  ✗ {field:40} MISSING!")
            all_present = False
    
    if all_present:
        print("\n✓ All critical W-2 fields present!")
    else:
        print("\n✗ Some W-2 fields are missing!")
    
    return all_present


def test_1099_misc_fields():
    """Test 1099-MISC has all 10 boxes"""
    print("\n" + "="*80)
    print("TEST 3: 1099-MISC FIELD COMPLETENESS (10 BOXES)")
    print("="*80)
    
    schema = DocumentFieldSchema.get_schema_for_document(DocumentType.FORM_1099_MISC)
    
    # The 10 boxes on 1099-MISC
    boxes_on_form = {
        "Box 1": "rents",
        "Box 2": "royalties",
        "Box 3": "other_income",
        "Box 5": "fishing_boat_proceeds",
        "Box 6": "medical_payments",
        "Box 7": "direct_sales",
        "Box 8": "substitute_payments",
        "Box 9": "crop_insurance_proceeds",
        "Box 10": "gross_proceeds_attorney",
        "Box 14": "excess_parachute_payments",
        "Box 15": "nonqualified_deferred_comp",
    }
    
    print(f"\n1099-MISC Schema has {len(schema)} total fields")
    print("\nChecking all 10+ boxes:")
    
    all_present = True
    for box_label, field_name in boxes_on_form.items():
        if field_name in schema:
            box, desc = schema[field_name]
            print(f"  ✓ {box_label} → {field_name:40} {desc}")
        else:
            print(f"  ✗ {box_label} → {field_name:40} MISSING!")
            all_present = False
    
    if all_present:
        print("\n✓ All 1099-MISC boxes present!")
    else:
        print("\n✗ Some 1099-MISC boxes are missing!")
    
    return all_present


def test_1099_nec_fields():
    """Test 1099-NEC has all fields"""
    print("\n" + "="*80)
    print("TEST 4: 1099-NEC FIELD COMPLETENESS")
    print("="*80)
    
    schema = DocumentFieldSchema.get_schema_for_document(DocumentType.FORM_1099_NEC)
    
    required_fields = [
        "nonemployee_compensation",
        "federal_income_tax_withheld",
        "recipient_tin",
        "payer_ein",
    ]
    
    print(f"\n1099-NEC Schema has {len(schema)} total fields")
    print("\nChecking critical fields:")
    
    all_present = True
    for field in required_fields:
        if field in schema:
            box, desc = schema[field]
            print(f"  ✓ {field:40} ({box:15}) {desc}")
        else:
            print(f"  ✗ {field:40} MISSING!")
            all_present = False
    
    if all_present:
        print("\n✓ All critical 1099-NEC fields present!")
    else:
        print("\n✗ Some 1099-NEC fields are missing!")
    
    return all_present


def test_1099_int_fields():
    """Test 1099-INT has all fields"""
    print("\n" + "="*80)
    print("TEST 5: 1099-INT FIELD COMPLETENESS")
    print("="*80)
    
    schema = DocumentFieldSchema.get_schema_for_document(DocumentType.FORM_1099_INT)
    
    required_fields = [
        "interest_income",
        "federal_income_tax_withheld",
    ]
    
    print(f"\n1099-INT Schema has {len(schema)} total fields")
    print("\nChecking critical fields:")
    
    all_present = True
    for field in required_fields:
        if field in schema:
            box, desc = schema[field]
            print(f"  ✓ {field:40} ({box:15}) {desc}")
        else:
            print(f"  ✗ {field:40} MISSING!")
            all_present = False
    
    if all_present:
        print("\n✓ All critical 1099-INT fields present!")
    else:
        print("\n✗ Some 1099-INT fields are missing!")
    
    return all_present


def test_1099_div_fields():
    """Test 1099-DIV has all dividend types"""
    print("\n" + "="*80)
    print("TEST 6: 1099-DIV FIELD COMPLETENESS")
    print("="*80)
    
    schema = DocumentFieldSchema.get_schema_for_document(DocumentType.FORM_1099_DIV)
    
    required_fields = [
        "ordinary_dividends",
        "qualified_dividends",
        "capital_gain_distributions",
        "federal_income_tax_withheld",
    ]
    
    print(f"\n1099-DIV Schema has {len(schema)} total fields")
    print("\nChecking critical fields:")
    
    all_present = True
    for field in required_fields:
        if field in schema:
            box, desc = schema[field]
            print(f"  ✓ {field:40} ({box:15}) {desc}")
        else:
            print(f"  ✗ {field:40} MISSING!")
            all_present = False
    
    if all_present:
        print("\n✓ All critical 1099-DIV fields present!")
    else:
        print("\n✗ Some 1099-DIV fields are missing!")
    
    return all_present


def test_prompt_generation():
    """Test that prompts can be generated for all document types"""
    print("\n" + "="*80)
    print("TEST 7: LLM PROMPT GENERATION")
    print("="*80)
    
    doc_types = [
        DocumentType.W2,
        DocumentType.FORM_1099_MISC,
        DocumentType.FORM_1099_NEC,
    ]
    
    all_good = True
    for doc_type in doc_types:
        try:
            prompt = get_available_fields_for_document(doc_type)
            has_fields = "AVAILABLE FIELDS" in prompt and len(prompt) > 100
            status = "✓" if has_fields else "✗"
            field_count = prompt.count("•")  # Count bullet points
            print(f"  {status} {doc_type.value:20} → Generated prompt with {field_count} fields")
            if not has_fields:
                all_good = False
        except Exception as e:
            print(f"  ✗ {doc_type.value:20} → Error: {str(e)}")
            all_good = False
    
    if all_good:
        print("\n✓ All prompts generated successfully!")
    else:
        print("\n✗ Some prompts failed to generate!")
    
    return all_good


def test_taxable_status():
    """Test that non-taxable fields are marked correctly"""
    print("\n" + "="*80)
    print("TEST 8: TAXABLE STATUS MARKING")
    print("="*80)
    
    schema = DocumentFieldSchema.get_schema_for_document(DocumentType.FORM_1099_MISC)
    
    print("\nChecking non-taxable field markings in 1099-MISC:")
    
    nontaxable_fields = {
        "medical_payments": "Medical payments - NOT taxable to recipient",
        "direct_sales": "Direct sales - informational only",
        "fish_purchased_for_resale": "Fish purchased for resale - NOT income",
    }
    
    all_marked = True
    for field_name, expected_text in nontaxable_fields.items():
        if field_name in schema:
            box, desc = schema[field_name]
            has_marking = "NOT" in desc or "informational" in desc or "NOT income" in desc
            status = "✓" if has_marking else "✗"
            print(f"  {status} {field_name:35} → {desc}")
            if not has_marking:
                all_marked = False
        else:
            print(f"  ✗ {field_name:35} NOT FOUND IN SCHEMA")
            all_marked = False
    
    if all_marked:
        print("\n✓ All non-taxable fields properly marked!")
    else:
        print("\n✗ Some non-taxable fields not properly marked!")
    
    return all_marked


def test_integration_with_llm_agent():
    """Test that schema integrates properly with llm_tax_agent"""
    print("\n" + "="*80)
    print("TEST 9: INTEGRATION WITH LLM AGENT")
    print("="*80)
    
    try:
        # Check that schema import works
        from document_field_schema import DocumentFieldSchema, get_available_fields_for_document
        print("\n✓ Successfully imported DocumentFieldSchema")
        
        # Check that llm_tax_agent can be imported
        from llm_tax_agent import detect_document_type, DocumentType
        print("✓ Successfully imported llm_tax_agent functions")
        
        # Check that we can access schema from the agent's module
        schema = DocumentFieldSchema.get_schema_for_document(DocumentType.FORM_1099_MISC)
        print(f"✓ Can access schema from agent module: {len(schema)} fields for 1099-MISC")
        
        # Test that detect_document_type works
        test_text = "Form 1099-MISC"
        detected_type = detect_document_type(test_text)
        print(f"✓ Document type detection works: detected '{detected_type.value}'")
        
        # Test that we can get field list for extraction
        field_prompt = get_available_fields_for_document(detected_type)
        has_fields = "AVAILABLE FIELDS" in field_prompt
        if has_fields:
            print(f"✓ Can generate extraction prompt with schema guidance")
        
        print("\n✓ Integration test passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "SCHEMA VALIDATION TEST SUITE" + " "*30 + "║")
    print("║" + " "*15 + "Testing DocumentFieldSchema completeness" + " "*22 + "║")
    print("╚" + "="*78 + "╝")
    
    results = {}
    
    # Run all tests
    results['structure'] = test_schema_structure()
    results['w2'] = test_w2_fields()
    results['1099_misc'] = test_1099_misc_fields()
    results['1099_nec'] = test_1099_nec_fields()
    results['1099_int'] = test_1099_int_fields()
    results['1099_div'] = test_1099_div_fields()
    results['prompts'] = test_prompt_generation()
    results['taxable'] = test_taxable_status()
    results['integration'] = test_integration_with_llm_agent()
    
    # Summary
    print("\n\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*27 + "TEST SUMMARY" + " "*39 + "║")
    print("╠" + "="*78 + "╣")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"║  {status:8}  {test_name:35}" + " "*35 + "║")
    
    print("╠" + "="*78 + "╣")
    print(f"║  TOTAL: {passed}/{total} tests passed" + " "*51 + "║")
    print("╚" + "="*78 + "╝")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Schema is ready for production.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review above for details.")
        return 1


if __name__ == "__main__":
    exit(main())

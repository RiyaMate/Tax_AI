"""
COMPLETE WORKFLOW: Load Field Schema → LLM Extract → Calculate Tax
=====================================================================

This script demonstrates the complete pipeline:
1. Detect document type
2. Load field schema for that type
3. Use LLM to extract with schema guidance
4. Aggregate extracted fields
5. Calculate taxes using IRS rules

Usage:
    python complete_workflow_schema_to_tax.py <document_text>
"""

import json
import sys
import os
from typing import Dict, Any, Optional, Tuple

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'frontend', 'utils'))

from llm_tax_agent import (
    LLMTaxAgent, 
    DocumentType, 
    detect_document_type,
    normalize_fields
)
from tax_engine import TaxEngine
from document_field_schema import (
    DocumentFieldSchema, 
    get_available_fields_for_document
)


class CompleteWorkflow:
    """
    Complete workflow: Schema Load → LLM Extract → Tax Calculate
    """
    
    def __init__(self):
        self.llm_agent = LLMTaxAgent()
        self.tax_engine = TaxEngine()
        self.schema = DocumentFieldSchema()
    
    def step_1_detect_document_type(self, text: str) -> DocumentType:
        """STEP 1: Detect what type of tax document this is"""
        print("\n" + "="*70)
        print("STEP 1: DETECT DOCUMENT TYPE")
        print("="*70)
        
        doc_type = detect_document_type(text)
        print(f"✓ Document Type Detected: {doc_type.value}")
        return doc_type
    
    def step_2_load_field_schema(self, doc_type: DocumentType) -> Dict[str, Tuple[str, str]]:
        """STEP 2: Load field schema for this document type"""
        print("\n" + "="*70)
        print("STEP 2: LOAD FIELD SCHEMA")
        print("="*70)
        
        schema_dict = self.schema.get_schema_for_document(doc_type)
        
        print(f"✓ Schema Loaded for {doc_type.value}")
        print(f"✓ Total Fields Available: {len(schema_dict)}")
        print("\n📋 Available Fields:")
        print("-" * 70)
        
        for field_name, (box_number, description) in schema_dict.items():
            print(f"  • {field_name:40} ({box_number:15}) {description}")
        
        return schema_dict
    
    def step_3_build_llm_prompt(self, doc_type: DocumentType, text: str, schema: Dict) -> str:
        """STEP 3: Build LLM prompt with field schema"""
        print("\n" + "="*70)
        print("STEP 3: BUILD LLM PROMPT WITH SCHEMA")
        print("="*70)
        
        field_list_prompt = get_available_fields_for_document(doc_type)
        
        prompt = f"""
You are a tax document extraction expert. Your task is to extract fields from a {doc_type.value} document.

IMPORTANT: You MUST extract ONLY the fields listed below. Do NOT create or hallucinate fields.

AVAILABLE FIELDS FOR {doc_type.value.upper()}:
{'='*70}
{field_list_prompt}
{'='*70}

EXTRACTION RULES:
1. Extract ONLY fields from the list above
2. For each field found, return the value
3. If a field is not found in the document, omit it (do NOT include null values)
4. Return values as numbers (without $, %, or commas)
5. For text fields (names, IDs), return exactly as shown on document

DOCUMENT TEXT:
{text}

RESPONSE FORMAT:
Return ONLY valid JSON with extracted fields. Example:
{{
  "field_name": value,
  "another_field": value
}}

Do NOT include any explanation or text outside the JSON.
"""
        
        print("✓ LLM Prompt Built")
        print("✓ Schema fields included in prompt")
        print("✓ Extraction rules set to prevent hallucinations")
        return prompt
    
    def step_4_llm_extract(self, doc_type: DocumentType, text: str, prompt: str) -> Dict[str, Any]:
        """STEP 4: Use LLM to extract fields with schema guidance"""
        print("\n" + "="*70)
        print("STEP 4: LLM EXTRACTION")
        print("="*70)
        
        try:
            print("📡 Sending to LLM with schema guidance...")
            
            # Use the agent's extraction method which now includes schema
            extracted = self.llm_agent.extract_document_fields(
                markdown_text=text,
                document_type=doc_type,
                llm_provider="gemini"  # or your preferred provider
            )
            
            print(f"✓ Extraction Complete")
            print(f"✓ Fields Extracted: {len(extracted.get('raw_fields', {}))}")
            
            return extracted
            
        except Exception as e:
            print(f"✗ Extraction Error: {str(e)}")
            return {"raw_fields": {}}
    
    def step_5_normalize_fields(self, extracted: Dict, doc_type: DocumentType) -> Dict[str, float]:
        """STEP 5: Normalize extracted fields to standard tax format"""
        print("\n" + "="*70)
        print("STEP 5: NORMALIZE FIELDS")
        print("="*70)
        
        raw_fields = extracted.get("raw_fields", {})
        
        # Normalize to standard tax field names
        normalized = normalize_fields(raw_fields, doc_type)
        
        print(f"✓ Fields Normalized")
        print(f"✓ Standardized Fields: {len(normalized)}")
        print("\n📊 Normalized Fields:")
        print("-" * 70)
        
        for field_name, value in sorted(normalized.items()):
            if isinstance(value, (int, float)):
                print(f"  • {field_name:40} ${value:>12,.2f}")
            else:
                print(f"  • {field_name:40} {str(value):>12}")
        
        return normalized
    
    def step_6_aggregate_documents(self, documents: list) -> Dict[str, float]:
        """STEP 6: Aggregate multiple documents by type"""
        print("\n" + "="*70)
        print("STEP 6: AGGREGATE DOCUMENTS")
        print("="*70)
        
        aggregated = {}
        
        for doc in documents:
            doc_type = doc["document_type"]
            normalized = doc["normalized_fields"]
            
            print(f"\nProcessing: {doc_type.value}")
            
            for field_name, value in normalized.items():
                if field_name not in aggregated:
                    aggregated[field_name] = 0
                
                if isinstance(value, (int, float)):
                    aggregated[field_name] += value
                    print(f"  + {field_name:40} ${value:>12,.2f}")
        
        print(f"\n✓ Documents Aggregated")
        print(f"✓ Total Unique Fields: {len(aggregated)}")
        
        return aggregated
    
    def step_7_calculate_taxes(self, aggregated_fields: Dict[str, float]) -> Dict[str, Any]:
        """STEP 7: Calculate taxes using IRS 2024 rules"""
        print("\n" + "="*70)
        print("STEP 7: CALCULATE TAXES (IRS 2024 RULES)")
        print("="*70)
        
        # Prepare fields for tax engine
        tax_summary = self.tax_engine.calculate_tax(aggregated_fields)
        
        print("\n💰 TAX CALCULATION RESULTS:")
        print("-" * 70)
        
        if "error" in tax_summary:
            print(f"✗ Error: {tax_summary['error']}")
            return tax_summary
        
        # Display tax calculation breakdown
        print(f"\nGross Income:")
        print(f"  Total Wages:                        ${aggregated_fields.get('wages', 0):>12,.2f}")
        print(f"  Interest Income:                    ${aggregated_fields.get('interest_income', 0):>12,.2f}")
        print(f"  NEC Income:                         ${aggregated_fields.get('nonemployee_compensation', 0):>12,.2f}")
        print(f"  Dividend Income:                    ${aggregated_fields.get('dividend_income', 0):>12,.2f}")
        print(f"  Other Income:                       ${aggregated_fields.get('other_income', 0):>12,.2f}")
        
        total_income = sum(v for k, v in aggregated_fields.items() 
                          if k in ['wages', 'interest_income', 'nonemployee_compensation', 
                                  'dividend_income', 'other_income'])
        print(f"  {'─'*50}")
        print(f"  Total Gross Income:                 ${total_income:>12,.2f}")
        
        print(f"\nStandard Deduction (2024):          ${tax_summary.get('standard_deduction', 0):>12,.2f}")
        print(f"Taxable Income:                     ${tax_summary.get('taxable_income', 0):>12,.2f}")
        
        print(f"\nFederal Income Tax:                 ${tax_summary.get('federal_tax', 0):>12,.2f}")
        print(f"Social Security Tax:                ${tax_summary.get('social_security_tax', 0):>12,.2f}")
        print(f"Medicare Tax:                       ${tax_summary.get('medicare_tax', 0):>12,.2f}")
        print(f"  {'─'*50}")
        print(f"  Total Tax Liability:                ${tax_summary.get('total_tax', 0):>12,.2f}")
        
        federal_withheld = aggregated_fields.get('federal_income_tax_withheld', 0)
        print(f"\nFederal Tax Withheld:               ${federal_withheld:>12,.2f}")
        
        refund_or_owed = federal_withheld - tax_summary.get('federal_tax', 0)
        if refund_or_owed > 0:
            print(f"✓ REFUND:                            ${refund_or_owed:>12,.2f}")
        elif refund_or_owed < 0:
            print(f"✗ AMOUNT OWED:                       ${abs(refund_or_owed):>12,.2f}")
        else:
            print(f"✓ BREAK EVEN")
        
        return tax_summary
    
    def run_complete_workflow(self, documents_text: list) -> Dict[str, Any]:
        """
        Run complete workflow from document text to tax calculation
        
        Args:
            documents_text: List of document markdown texts
        
        Returns:
            Complete workflow results with tax summary
        """
        print("\n\n")
        print("╔" + "═"*68 + "╗")
        print("║" + " "*15 + "COMPLETE WORKFLOW: SCHEMA → EXTRACT → TAX" + " "*12 + "║")
        print("╚" + "═"*68 + "╝")
        
        all_documents = []
        
        # Process each document
        for i, doc_text in enumerate(documents_text, 1):
            print(f"\n\n{'='*70}")
            print(f"DOCUMENT {i}/{len(documents_text)}")
            print(f"{'='*70}")
            
            # STEP 1: Detect type
            doc_type = self.step_1_detect_document_type(doc_text)
            
            # STEP 2: Load schema
            schema = self.step_2_load_field_schema(doc_type)
            
            # STEP 3: Build prompt
            prompt = self.step_3_build_llm_prompt(doc_type, doc_text, schema)
            
            # STEP 4: Extract with LLM
            extracted = self.step_4_llm_extract(doc_type, doc_text, prompt)
            
            # STEP 5: Normalize fields
            normalized = self.step_5_normalize_fields(extracted, doc_type)
            
            all_documents.append({
                "document_type": doc_type,
                "extracted": extracted,
                "normalized_fields": normalized
            })
        
        # STEP 6: Aggregate all documents
        aggregated = self.step_6_aggregate_documents(all_documents)
        
        # STEP 7: Calculate taxes
        tax_results = self.step_7_calculate_taxes(aggregated)
        
        # Final Summary
        print("\n\n")
        print("╔" + "═"*68 + "╗")
        print("║" + " "*20 + "WORKFLOW COMPLETE" + " "*32 + "║")
        print("╚" + "═"*68 + "╝")
        
        return {
            "documents_processed": len(all_documents),
            "aggregated_fields": aggregated,
            "tax_summary": tax_results
        }


# Example usage
if __name__ == "__main__":
    
    # Example 1099-MISC document
    example_doc = """
    FORM 1099-MISC - MISCELLANEOUS INCOME
    
    Payer: ABC Corporation
    EIN: 12-3456789
    Recipient: John Smith
    TIN: 123-45-6789
    
    Box 1 - Rents: $5,500.00
    Box 2 - Royalties: $3,250.00
    Box 3 - Other Income: $2,100.00
    Box 5 - Fishing Boat Proceeds: $0.00
    Box 6 - Medical Payments: $1,200.00 (NOT TAXABLE)
    Box 8 - Substitute Payments: $5,800.00
    Box 9 - Crop Insurance Proceeds: $7,600.00
    Box 10 - Gross Proceeds Attorney: $3,500.00
    Box 14 - Excess Parachute Payments: $1,800.00
    Box 15 - Nonqualified Deferred Comp: $700.00
    
    Federal Income Tax Withheld: $2,000.00
    """
    
    # Run workflow
    workflow = CompleteWorkflow()
    results = workflow.run_complete_workflow([example_doc])
    
    # Print final JSON results
    print("\n\n")
    print("="*70)
    print("FINAL RESULTS (JSON)")
    print("="*70)
    print(json.dumps(results, indent=2, default=str))

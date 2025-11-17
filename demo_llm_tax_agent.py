#!/usr/bin/env python3
"""
Demo: Universal LLM Tax Agent

Shows how to use the LLM agent to extract taxes from ANY format.
"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'frontend', 'utils'))

from llm_tax_agent import UniversalLLMTaxAgent, LLMProvider, DocumentType, detect_document_type
import json


def demo_w2_extraction():
    """Demo: Extract W-2 from messy ADE markdown table"""
    
    print("\n" + "="*80)
    print("DEMO 1: W-2 Extraction from ADE Markdown Table")
    print("="*80)
    
    # Messy ADE output with table format
    w2_markdown = """
| **Box** | **Label** | **Value** |
| --- | --- | --- |
| 1 | Wages, tips, other compensation | $23500.00 |
| 2 | Federal income tax withheld | $1500.00 |
| 3 | Social Security wages | $23500.00 |
| 4 | Social Security tax withheld | $1457.00 |
| 5 | Medicare wages and tips | $23500.00 |
| 6 | Medicare tax withheld | $340.75 |
| 17 | State income tax | $800.00 |

Employee: John Smith
SSN: 123-45-6789
Employer: ACME Corporation
EIN: 12-3456789
"""
    
    print("[INFO] Processing W-2 document...")
    
    # Detect type
    doc_type = detect_document_type(w2_markdown)
    print(f"[INFO] Detected: {doc_type.value}")
    
    # Create agent
    agent = UniversalLLMTaxAgent(llm_provider=LLMProvider.GEMINI)
    
    # Process
    result = agent.process_document(w2_markdown)
    
    # Show results
    print(result["summary"])
    
    print("\n[DEBUG] Extracted fields (normalized):")
    for k, v in result["normalized_fields"].items():
        if v > 0:
            print(f"  {k:40s} = ${v:12,.2f}")
    
    return result


def demo_1099_nec_extraction():
    """Demo: Extract 1099-NEC from text format"""
    
    print("\n" + "="*80)
    print("DEMO 2: 1099-NEC Extraction from Text Format")
    print("="*80)
    
    # Simple text format (might come from OCR)
    nec_text = """
FORM 1099-NEC
Nonemployee Compensation

Box 1 - Nonemployee compensation: $12,000.00
Box 4 - Federal income tax withheld: $500.00

Payer: ABC Consulting LLC
Payer EIN: 98-7654321
Recipient: Jane Developer
Recipient TIN: 987-65-4321
"""
    
    print("[INFO] Processing 1099-NEC document...")
    
    # Detect type
    doc_type = detect_document_type(nec_text)
    print(f"[INFO] Detected: {doc_type.value}")
    
    # Create agent
    agent = UniversalLLMTaxAgent(llm_provider=LLMProvider.GEMINI)
    
    # Process
    result = agent.process_document(nec_text)
    
    # Show results
    print(result["summary"])
    
    print("\n[DEBUG] Extracted fields (normalized):")
    for k, v in result["normalized_fields"].items():
        if v > 0:
            print(f"  {k:40s} = ${v:12,.2f}")
    
    return result


def demo_messy_ocr():
    """Demo: Extract from messy OCR output"""
    
    print("\n" + "="*80)
    print("DEMO 3: Extract from Messy OCR Output (Real-world noise)")
    print("="*80)
    
    # Real-world messy OCR with artifacts
    messy_ocr = """
Form W-2 Wage and Tax Statement 2024

|ox 1 W4ges, tips, oth9r compensation..... $24,125.00
B0x 2 Federal income t4x withheld.... $2,150.00
Box 3 S0ci4l Security w4ges......... $24,125.00
B0X 4 S0ci4l S9curity t4x w/hield.... $1,495.50
B0X 5 Medicare w4ges and tips..... $24,125.00
BOX 6 M9dicare tax withh9ld........ $350.00

W0RK9R ID: 555-44-3332
9MP10Y9R: Gluebot M4nuf4cturing
9MP10Y9R 9IN: 34-5678901
"""
    
    print("[INFO] Processing OCR document with artifacts...")
    
    # Detect type
    doc_type = detect_document_type(messy_ocr)
    print(f"[INFO] Detected: {doc_type.value}")
    
    # Create agent
    agent = UniversalLLMTaxAgent(llm_provider=LLMProvider.GEMINI)
    
    # Process
    result = agent.process_document(messy_ocr)
    
    # Show results
    print(result["summary"])
    
    print("\n[DEBUG] Extracted fields (normalized):")
    for k, v in result["normalized_fields"].items():
        if v > 0:
            print(f"  {k:40s} = ${v:12,.2f}")
    
    return result


if __name__ == "__main__":
    print("\n" + "="*80)
    print("UNIVERSAL LLM TAX AGENT - DEMONSTRATION")
    print("="*80)
    print("\nThis demo shows how the LLM Tax Agent can extract taxes from:")
    print("  ✅ Structured markdown tables (ADE output)")
    print("  ✅ Plain text formats")
    print("  ✅ Messy OCR output with errors and noise")
    print("  ✅ ANY other format")
    print("\nNo schemas. No form-specific regex. Pure LLM reasoning.")
    
    try:
        # Run demos
        result1 = demo_w2_extraction()
        result2 = demo_1099_nec_extraction()
        result3 = demo_messy_ocr()
        
        print("\n" + "="*80)
        print("DEMO COMPLETE")
        print("="*80)
        print("\n✅ All demos completed successfully!")
        print("\nThe LLM Tax Agent successfully extracted taxes from:")
        print("  1. ADE markdown table format")
        print("  2. Plain text 1099-NEC")
        print("  3. Messy OCR output with artifacts")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()

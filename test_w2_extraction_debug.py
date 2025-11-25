"""
Debug script to test W-2 extraction from PDF
Shows what LandingAI actually returns and why extraction is failing
"""
import requests
import json
import os
import sys
from dotenv import load_dotenv

load_dotenv(override=True)

# PDF file path
pdf_path = r"C:\Users\riyam\Downloads\W2_Interactive.pdf"

if not os.path.exists(pdf_path):
    print(f"ERROR: PDF not found at {pdf_path}")
    exit(1)

print(f"[TEST] Extracting W-2 from: {pdf_path}")
print("=" * 80)

# Step 1: Call LandingAI API to extract
print("\n[STEP 1] Calling LandingAI extraction API...")
try:
    with open(pdf_path, 'rb') as f:
        response = requests.post(
            "http://localhost:8000/api/tax/extract-landingai",
            files={"file": (os.path.basename(pdf_path), f, "application/pdf")},
            timeout=300
        )
    
    if response.status_code == 200:
        landingai_output = response.json()
        print("[OK] LandingAI extraction successful")
        
        # Step 2: Show what we got
        print("\n[STEP 2] LandingAI Output Structure:")
        print(f"  Keys: {list(landingai_output.keys())}")
        
        # Show markdown preview
        if "markdown" in landingai_output:
            markdown = landingai_output["markdown"]
            print(f"\n[MARKDOWN] First 1000 characters:")
            print("-" * 80)
            print(markdown[:1000])
            print("-" * 80)
            
            # Look for wages pattern
            print("\n[PATTERN MATCHING] Looking for W-2 patterns...")
            import re
            
            # Current pattern from map_w2
            pattern1 = r"Wages[,\s]+tips[,\s]+other\s+compensation\s+([\d,\.]+)"
            match1 = re.search(pattern1, markdown, re.IGNORECASE)
            print(f"  Pattern 1 (current): {pattern1}")
            print(f"    Match: {match1.group(1) if match1 else 'NO MATCH'}")
            
            # Try alternative patterns
            pattern2 = r"Box 1[:\s]+([\d,\.]+)"
            match2 = re.search(pattern2, markdown, re.IGNORECASE)
            print(f"  Pattern 2 (Box 1): {pattern2}")
            print(f"    Match: {match2.group(1) if match2 else 'NO MATCH'}")
            
            pattern3 = r"(\d+)[,\.]?(\d+)\s*Wages"
            match3 = re.search(pattern3, markdown, re.IGNORECASE)
            print(f"  Pattern 3 (number before Wages): {pattern3}")
            print(f"    Match: {match3.group(0) if match3 else 'NO MATCH'}")
            
            pattern4 = r"wages.*?([\d,]+\.?\d*)"
            match4 = re.search(pattern4, markdown, re.IGNORECASE)
            print(f"  Pattern 4 (flexible): {pattern4}")
            print(f"    Match: {match4.group(1) if match4 else 'NO MATCH'}")
            
            # Show lines containing "wages"
            print("\n[WAGES LINES] Lines containing 'wages':")
            for i, line in enumerate(markdown.split('\n')):
                if 'wage' in line.lower():
                    print(f"  Line {i}: {line[:120]}")
        
        # Show key_value_pairs
        if "key_value_pairs" in landingai_output:
            kvp = landingai_output["key_value_pairs"]
            print(f"\n[KEY-VALUE PAIRS] ({len(kvp)} items):")
            for i, (k, v) in enumerate(list(kvp.items())[:10]):
                print(f"  {k}: {v}")
            if len(kvp) > 10:
                print(f"  ... and {len(kvp) - 10} more")
        
        # Show extracted_values
        if "extracted_values" in landingai_output:
            ev = landingai_output["extracted_values"]
            print(f"\n[EXTRACTED VALUES] ({len(ev)} items):")
            for i, item in enumerate(list(ev)[:10]):
                print(f"  {i}: {item}")
            if len(ev) > 10:
                print(f"  ... and {len(ev) - 10} more")
        
        # Step 3: Call the backend extractor
        print("\n[STEP 3] Testing backend extraction...")
        sys.path.insert(0, r"C:\Users\riyam\PDF_GREEN\LiteLLM_SummaryGenerator_with_Q-A\backend")
        from llm_tax_agent import map_w2, process_landingai_output
        
        result = map_w2(landingai_output)
        print(f"[MAP_W2 RESULT]:")
        for k, v in result.items():
            print(f"  {k}: {v}")
        
        # Show full process result
        print("\n[STEP 4] Full process_landingai_output result...")
        full_result = process_landingai_output(
            landingai_output,
            filing_status="single",
            num_dependents=0
        )
        print(f"[FULL RESULT]:")
        print(f"  Income Wages: {full_result.get('income_wages')}")
        print(f"  Taxable Income: {full_result.get('taxable_income')}")
        print(f"  Federal Tax: {full_result.get('taxes_federal_income_tax')}")
        print(f"  Refund: {full_result.get('refund_or_due')}")
        
        # Save full output for inspection
        with open("w2_landingai_output_debug.json", "w") as f:
            json.dump(landingai_output, f, indent=2)
        print("\n[SAVED] Full LandingAI output to: w2_landingai_output_debug.json")
        
    else:
        print(f"[ERROR] LandingAI API failed: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("[DONE]")

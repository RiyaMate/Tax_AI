"""
Debug W-2 extraction to diagnose why wages are showing as $0
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from llm_tax_agent import LLMTaxAgent

# Sample W-2 markdown output from LandingAI (typical format)
w2_markdown_examples = [
    # Format 1: Table format
    """
| Box | Label | Amount |
|-----|-------|--------|
| 1 | Wages, tips, other comp. | 23500.00 |
| 2 | Federal income tax withheld | 1500.00 |
| 3 | Social Security wages | 23500.00 |
| 4 | Social Security tax withheld | 1457.00 |
| 5 | Medicare wages and tips | 23500.00 |
| 6 | Medicare tax withheld | 340.75 |
""",
    
    # Format 2: Colon-separated
    """
W-2 Wage and Tax Statement

Box 1: Wages, tips, other compensation: $23,500.00
Box 2: Federal income tax withheld: $1,500.00
Box 3: Social Security wages: $23,500.00
Box 4: Social Security tax withheld: $1,457.00
Box 5: Medicare wages and tips: $23,500.00
Box 6: Medicare tax withheld: $340.75
""",
    
    # Format 3: HTML table (ADE output)
    """
<table>
<tr><td>1</td><td>Wages, tips, other comp.</td><td>23500.00</td></tr>
<tr><td>2</td><td>Federal income tax withheld</td><td>1500.00</td></tr>
<tr><td>3</td><td>Social Security wages</td><td>23500.00</td></tr>
<tr><td>4</td><td>Social Security tax withheld</td><td>1457.00</td></tr>
<tr><td>5</td><td>Medicare wages and tips</td><td>23500.00</td></tr>
<tr><td>6</td><td>Medicare tax withheld</td><td>340.75</td></tr>
</table>
""",
]

print("=" * 80)
print("DEBUG: W-2 EXTRACTION TEST")
print("=" * 80)

agent = LLMTaxAgent()

for idx, markdown in enumerate(w2_markdown_examples, 1):
    print(f"\n--- Test {idx} ---")
    print("Input markdown (first 200 chars):")
    print(markdown[:200])
    
    try:
        # Test document type detection
        from backend.llm_tax_agent import detect_document_type
        doc_type = detect_document_type(markdown)
        print(f"Detected type: {doc_type}")
        
        # Create LandingAI output format
        landingai_output = {
            "markdown": markdown,
            "extracted_values": [],
            "key_value_pairs": {}
        }
        
        # Process the document
        result = agent.process_landingai_output(landingai_output)
        
        print(f"Result Status: {result.get('status')}")
        print(f"Wages Extracted: ${result.get('income_wages', 0):,.2f}")
        print(f"Federal Withheld: ${result.get('withholding_federal_withheld', 0):,.2f}")
        print(f"Total Income: ${result.get('income_total_income', 0):,.2f}")
        
        if result.get('income_wages', 0) == 0:
            print("❌ WARNING: Wages not extracted!")
        else:
            print("✅ Wages extracted successfully")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("Now testing with actual W-2 markdown from LandingAI...")
print("=" * 80)

# Try to find actual LandingAI output
import json
from pathlib import Path

# Look for recent extraction results
for json_file in Path(".").glob("*.json"):
    if "landingai" in json_file.name.lower() or "w2" in json_file.name.lower():
        print(f"\nFound: {json_file.name}")
        try:
            with open(json_file) as f:
                data = json.load(f)
                if "markdown" in data:
                    markdown_content = data["markdown"]
                    print(f"Markdown content (first 300 chars):\n{markdown_content[:300]}")
                    
                    # Test extraction
                    result = agent.process_landingai_output(data)
                    print(f"\nExtraction Result:")
                    print(f"  Wages: ${result.get('income_wages', 0):,.2f}")
                    print(f"  Federal Withheld: ${result.get('withholding_federal_withheld', 0):,.2f}")
                    print(f"  Status: {result.get('status')}")
        except Exception as e:
            print(f"Error reading {json_file.name}: {e}")

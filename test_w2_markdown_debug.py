"""
Test to see what LandingAI actually returns from W2_Interactive.pdf
and why extraction is failing
"""

import json
from pathlib import Path

# Look for W2 test files or recent extraction outputs
print("Looking for test data files...")

test_files = [
    Path("test_w2_data.json"),
    Path("w2_extraction_sample.json"),
    Path("W2_Interactive_sample.json"),
]

# Also check downloads
downloads = Path("C:\\Users\\riyam\\Downloads").glob("*.json")

# Check recent JSON files in workspace
recent_json = Path(".").glob("test_*.json")

for json_file in list(test_files) + list(downloads) + list(recent_json):
    if json_file.exists():
        print(f"\nFound: {json_file}")
        try:
            with open(json_file) as f:
                data = json.load(f)
                
                # Show structure
                print(f"  Keys: {list(data.keys())}")
                
                if "markdown" in data:
                    md = data["markdown"]
                    print(f"  Markdown length: {len(md)}")
                    print(f"  Markdown preview (first 500 chars):")
                    print(f"  {md[:500]}")
                    print()
                    
                    # Test extraction with backend
                    import sys
                    sys.path.insert(0, str(Path(".") / "backend"))
                    
                    from llm_tax_agent import LLMTaxAgent
                    
                    agent = LLMTaxAgent()
                    result = agent.process_landingai_output(data)
                    
                    print(f"  Backend Extraction Result:")
                    print(f"    Wages: ${result.get('income_wages', 0):,.2f}")
                    print(f"    Fed Withheld: ${result.get('withholding_federal_withheld', 0):,.2f}")
                    print(f"    Status: {result.get('status')}")
                    print(f"    Document Type: {result.get('document_type')}")
                    
                    if result.get('income_wages', 0) == 0:
                        print(f"    >> ISSUE: Wages not extracted!")
                        print(f"    >> Full markdown:")
                        print(md)
                        
        except Exception as e:
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()

# Also test with a known W-2 markdown
print("\n" + "=" * 80)
print("Testing with known W-2 markdown formats...")
print("=" * 80)

import sys
sys.path.insert(0, str(Path(".") / "backend"))

from llm_tax_agent import LLMTaxAgent

test_w2_html = """
<table>
<tr><td>Box</td><td>Label</td><td>Value</td></tr>
<tr><td>1</td><td>Wages, tips, other comp.</td><td>23500.00</td></tr>
<tr><td>2</td><td>Federal income tax withheld</td><td>1500.00</td></tr>
<tr><td>3</td><td>Social Security wages</td><td>23500.00</td></tr>
<tr><td>4</td><td>Social Security tax withheld</td><td>1457.00</td></tr>
<tr><td>5</td><td>Medicare wages and tips</td><td>23500.00</td></tr>
<tr><td>6</td><td>Medicare tax withheld</td><td>340.75</td></tr>
</table>
"""

landingai_output = {
    "markdown": test_w2_html,
    "extracted_values": [],
    "key_value_pairs": {}
}

agent = LLMTaxAgent()
result = agent.process_landingai_output(landingai_output)

print(f"\nTest W-2 HTML Extraction:")
print(f"  Wages: ${result.get('income_wages', 0):,.2f}")
print(f"  Fed Withheld: ${result.get('withholding_federal_withheld', 0):,.2f}")

if result.get('income_wages', 0) > 0:
    print(f"  ✓ Backend extraction working for HTML format")
else:
    print(f"  ✗ Backend extraction NOT working - issue with regex patterns")

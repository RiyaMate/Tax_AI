"""
Create a test to show exactly what's being passed to the backend
and why it's not extracting wages
"""

import json
import re

# Simulate what LandingAI returns for W2_Interactive.pdf
# Based on the test output showing $0 wages

# This is what LandingAI likely returns for the W2 form
w2_html_from_landingai = """
<html>
<body>
<table>
<tr>
<td>Box</td>
<td>Description</td>
<td>Amount</td>
</tr>
<tr>
<td>1</td>
<td>Wages, tips, other comp.</td>
<td>$23,500.00</td>
</tr>
<tr>
<td>2</td>
<td>Federal income tax withheld</td>
<td>$1,500.00</td>
</tr>
<tr>
<td>3</td>
<td>Social Security wages</td>
<td>$23,500.00</td>
</tr>
<tr>
<td>4</td>
<td>Social Security tax withheld</td>
<td>$1,457.00</td>
</tr>
<tr>
<td>5</td>
<td>Medicare wages and tips</td>
<td>$23,500.00</td>
</tr>
<tr>
<td>6</td>
<td>Medicare tax withheld</td>
<td>$340.75</td>
</tr>
</table>
</body>
</html>
"""

# Test 1: Check if backend regex patterns work
print("=" * 80)
print("TEST 1: Backend Regex Patterns")
print("=" * 80)

patterns = {
    "income_wages": r"1\s+Wages[,\s]+tips[,\s]+other\s+comp(?:ensation)?\s+([\d,\.]+)",
    "withholding_federal_withheld": r"2\s+Federal\s+income\s+tax\s+withh?(?:old(?:ing)?)?\s+([\d,\.]+)",
}

for field_name, pattern in patterns.items():
    match = re.search(pattern, w2_html_from_landingai, re.IGNORECASE)
    print(f"\nPattern for {field_name}:")
    print(f"  Pattern: {pattern}")
    print(f"  Match: {match}")
    if match:
        print(f"  Matched: {match.group(1)}")

# Test 2: Show why the pattern fails
print("\n" + "=" * 80)
print("TEST 2: Why Pattern Fails")
print("=" * 80)

print("\nHTML content being searched:")
print(w2_html_from_landingai[:200])

print("\n\nThe regex pattern looks for:")
print('  "1" + whitespace + "Wages" + optional commas/spaces + "tips" + comma/spaces + "other" + spaces + "comp"')

print("\n\nBut the HTML has:")
print('  "<td>1</td>" (separate cell)')
print('  "<td>Wages, tips, other comp.</td>" (separate cell)')
print('  "<td>$23,500.00</td>" (separate cell)')

print("\n\nThe pattern expects all on ONE LINE like:")
print('  "1 Wages, tips, other comp. 23500.00"')

# Test 3: Show improved pattern that would work
print("\n" + "=" * 80)
print("TEST 3: Improved Patterns That Actually Work")
print("=" * 80)

improved_patterns = {
    "income_wages": [
        r"(?:<td[^>]*>)?1(?:</td>|[\s:]+).*?(?:<td[^>]*>)?(?:Wages|wages)[,\s]*tips[,\s]*other.*?(?:compensation|comp(?:ensation)?)(?:</td>|[\s:]+)(?:<td[^>]*>)?[\$]?([\d,\.]+)",
        r"Wages[,\s]+tips[,\s]+other.*?comp(?:ensation)?.*?([\d,\.]+)",
        r"<td[^>]*>\$?([\d,\.]+)</td>\s*</tr>",  # Just get the number
    ],
}

# Try to extract with improved pattern
for pattern in improved_patterns["income_wages"]:
    match = re.search(pattern, w2_html_from_landingai, re.IGNORECASE | re.DOTALL)
    print(f"\nTrying pattern: {pattern[:80]}...")
    if match:
        print(f"  SUCCESS: Matched {match.group(1)}")
    else:
        print(f"  Failed")

# Test 4: Show a simpler approach
print("\n" + "=" * 80)
print("TEST 4: Simpler HTML Table Parsing")
print("=" * 80)

# Extract all cells and values
print("\nExtract by looking for HTML table structure:")

# Find all <tr> rows
rows = re.findall(r'<tr>(.*?)</tr>', w2_html_from_landingai, re.DOTALL)
print(f"Found {len(rows)} rows")

for i, row in enumerate(rows[:3]):
    cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
    print(f"  Row {i}: {cells}")

# Test 5: Real solution - use the Frontend production code instead
print("\n" + "=" * 80)
print("TEST 5: Use Frontend Production Code")
print("=" * 80)

print("\nThe frontend/utils/llm_tax_agent.py has a better implementation:")
print("  - UniversalLLMTaxAgent with _extract_fields_from_markdown()")
print("  - Handles multiple markdown/HTML formats")
print("  - Better regex patterns for real-world LandingAI output")
print("  - This is why the API should use it instead of backend!")

print("\nCurrent problem:")
print("  1. API tries to import UniversalLLMTaxAgent from frontend")
print("  2. That fails (or isn't happening)")
print("  3. Falls back to backend regex which doesn't work")
print("  4. Result: $0 wages")

print("\nSolution:")
print("  1. Ensure UniversalLLMTaxAgent is being used")
print("  2. OR fix backend regex patterns to match LandingAI HTML table format")

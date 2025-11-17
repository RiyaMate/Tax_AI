import re

# Test the regex pattern with the table format
w2_markdown = """
Wages:</td><td>$68,500.00
"""

# Current pattern
pattern1 = r'(?:Box\s+1|Wages|wages)[:\s]*[\$]?([0-9,]+\.?\d*)'

# Test it
match = re.search(pattern1, w2_markdown, re.IGNORECASE | re.DOTALL)
if match:
    print(f"[OK] Match found: {match.group(1)}")
else:
    print(f"[NO] No match")

# Debug: what's actually in the text
print(f"\nText to search: {repr(w2_markdown)}")
print(f"\nPattern: {pattern1}")

# Try simpler pattern
pattern2 = r'Wages.*?[\$]?([0-9,]+\.?\d*)'
match2 = re.search(pattern2, w2_markdown, re.IGNORECASE | re.DOTALL)
if match2:
    print(f"\n[OK] Pattern 2 Match found: {match2.group(1)}")
else:
    print(f"\n[NO] Pattern 2 No match")

# The issue: we need to handle </td><td> between label and value
pattern3 = r'(?:Wages)[:\s]*(?:</td><td>)?[\$]?([0-9,]+\.?\d*)'
match3 = re.search(pattern3, w2_markdown, re.IGNORECASE | re.DOTALL)
if match3:
    print(f"\n[OK] Pattern 3 (with HTML) Match found: {match3.group(1)}")
else:
    print(f"\n[NO] Pattern 3 No match")

#!/usr/bin/env python
"""Test HTML preprocessing for LandingAI markdown output"""

import re

def preprocess_document(text: str) -> str:
    """Convert HTML tables and complex markup to plain text for LLM"""
    
    # Remove HTML tags but preserve content
    text = re.sub(r'<[^>]+>', '', text)
    
    # Convert HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&amp;', '&')
    
    # Remove extra whitespace
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)
    
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    return text


# Test with the actual W-2 HTML from the user
html_input = """<a id='8c20cfde-569e-40d8-b33e-e380ae812f1f'></a>

Form W-2 (2024) – Wage and Tax Statement

<a id='9adf233f-034e-44c7-b5d3-892da8a5e4a8'></a>

<table id="0-1">
<tr><td id="0-2">Employer:</td><td id="0-3">NOKIA</td></tr>
<tr><td id="0-4">Employer EIN:</td><td id="0-5">12-3456789</td></tr>
<tr><td id="0-6">Employer Address:</td><td id="0-7">600 Technology Drive, Espoo, Finland</td></tr>
<tr><td id="0-8">Employee:</td><td id="0-9">RSM</td></tr>
<tr><td id="0-a">Employee SSN:</td><td id="0-b">123-45-6789</td></tr>
<tr><td id="0-c">Employee Address:</td><td id="0-d">123 Elm Street, Boston, MA 02115</td></tr>
</table>

<a id='dbd3c885-3629-44c6-b851-597fdb51c207'></a>

<table id="0-e">
<tr><td id="0-f">Box 1 Wages</td><td id="0-g">$60,250.00</td></tr>
<tr><td id="0-h">Box 2 Federal Income Tax Withheld</td><td id="0-i">$7,200.00</td></tr>
<tr><td id="0-j">Box 3 Social Security Wages</td><td id="0-k">$60,250.00</td></tr>
<tr><td id="0-l">Box 4 Social Security Tax Withheld</td><td id="0-m">$3,735.50</td></tr>
<tr><td id="0-n">Box 5 Medicare Wages</td><td id="0-o">$60,250.00</td></tr>
<tr><td id="0-p">Box 6 Medicare Tax Withheld</td><td id="0-q">$873.63</td></tr>
<tr><td id="0-r">Box 16 State Wages</td><td id="0-s">$60,250.00</td></tr>
<tr><td id="0-t">Box 17 State Income Tax</td><td id="0-u">$2,100.00</td></tr>
</table>"""

print("=" * 80)
print("BEFORE PREPROCESSING (HTML)")
print("=" * 80)
print(html_input[:300])
print("... (truncated)")

print("\n" + "=" * 80)
print("AFTER PREPROCESSING (Plain Text)")
print("=" * 80)
clean_text = preprocess_document(html_input)
print(clean_text)

print("\n" + "=" * 80)
print("VERIFICATION")
print("=" * 80)
print(f"✅ Cleaned text length: {len(clean_text)} characters")
print(f"✅ Contains 'Box 1 Wages': {'Box 1 Wages' in clean_text}")
print(f"✅ Contains '$60,250.00': {'$60,250.00' in clean_text}")
print(f"✅ Contains 'NOKIA': {'NOKIA' in clean_text}")
print(f"✅ Contains 'RSM': {'RSM' in clean_text}")
print(f"✅ HTML tags removed: {'<' not in clean_text and '>' not in clean_text}")

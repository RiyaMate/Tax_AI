"""
Test script for Form 1040 PDF generation
"""

import sys
import os
from pathlib import Path

# Add frontend/utils to path
sys.path.insert(0, str(Path(__file__).parent / "frontend" / "utils"))

from form_1040_generator import generate_form_1040_from_tax_result


# Sample tax result from our test case
tax_result = {
    "status": "success",
    "tax_year": 2024,
    "filing_status": "single",
    "num_dependents": 0,
    "income": {
        "wages": 60250.0,
        "nonemployee_compensation": 0.0,
        "interest_income": 0.0,
        "dividend_income": 0.0,
        "total_income": 60250.0,
    },
    "deduction": {
        "type": "standard",
        "amount": 14600.0,
    },
    "taxable_income": 45650.0,
    "taxes": {
        "federal_income_tax": 5246.0,
        "self_employment_tax": 0.0,
        "total_tax_before_credits": 5246.0,
    },
    "credits": {
        "education_credits": 0.0,
        "child_tax_credit": 0.0,
        "earned_income_credit": 0.0,
        "other_credits": 0.0,
        "total_credits": 0.0,
    },
    "total_tax_liability": 5246.0,
    "withholding": {
        "federal_withheld": 7200.0,
        "ss_withheld": 0.0,
        "medicare_withheld": 0.0,
        "total_withheld": 7200.0,
    },
    "refund_or_due": 1954.0,
    "result_type": "Refund",
    "result_amount": 1954.0,
    "result_status": "Refund [OK]",
}

taxpayer_info = {
    "first_name": "John",
    "last_name": "Smith",
    "ssn": "123-45-6789",
    "address": "123 Main Street",
    "city": "Springfield",
    "state": "IL",
    "zip": "62701",
}

# Generate output path
output_dir = Path(__file__).parent.parent.parent / "output"
output_dir.mkdir(exist_ok=True)
output_path = output_dir / "Form_1040_Test.pdf"

print("="*80)
print("Form 1040 PDF Generation Test")
print("="*80)
print(f"\nInput Data:")
print(f"  Filing Status: {tax_result['filing_status']}")
print(f"  Total Income: ${tax_result['income']['total_income']:,.2f}")
print(f"  Taxable Income: ${tax_result['taxable_income']:,.2f}")
print(f"  Federal Tax: ${tax_result['taxes']['federal_income_tax']:,.2f}")
print(f"  Refund: ${tax_result['refund_or_due']:,.2f}")

print(f"\nTaxpayer Info:")
print(f"  Name: {taxpayer_info['first_name']} {taxpayer_info['last_name']}")
print(f"  SSN: {taxpayer_info['ssn']}")
print(f"  Address: {taxpayer_info['address']}, {taxpayer_info['city']}, {taxpayer_info['state']} {taxpayer_info['zip']}")

print(f"\nGenerating Form 1040...")
print(f"Output: {output_path}")

try:
    # Generate the PDF
    pdf_path = generate_form_1040_from_tax_result(
        tax_result=tax_result,
        taxpayer_info=taxpayer_info,
        output_path=str(output_path),
    )
    
    # Check if file was created
    if os.path.exists(pdf_path):
        file_size = os.path.getsize(pdf_path)
        print(f"\n✅ SUCCESS!")
        print(f"PDF generated: {pdf_path}")
        print(f"File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    else:
        print(f"\n❌ ERROR: PDF file not found at {pdf_path}")
        
except Exception as e:
    print(f"\n❌ ERROR during PDF generation:")
    print(f"  {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)

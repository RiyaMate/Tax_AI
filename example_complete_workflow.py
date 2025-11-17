"""
COMPLETE EXAMPLE: Tax Calculation + Form 1040 Generation
Demonstrates full workflow from input to PDF download
"""

import sys
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path(__file__).parent / "frontend" / "utils"))

from tax_engine import calculate_tax
from form_1040_generator import generate_form_1040_from_tax_result
from form_1040_ui import Form1040UI

# ============================================================================
# EXAMPLE 1: Simple W-2 Only (Single Filer)
# ============================================================================

def example_1_simple_w2():
    """Simple example: Single filer with W-2 wages"""
    
    print("\n" + "="*80)
    print("EXAMPLE 1: Simple W-2 (Single Filer)")
    print("="*80)
    
    # Step 1: Define income documents
    documents = [
        {
            "wages": 60250.00,
            "federal_income_tax_withheld": 7200.00,
            "social_security_wages": 60250.00,
            "social_security_tax_withheld": 0.0,
            "medicare_wages": 60250.00,
            "medicare_tax_withheld": 0.0,
            "nonemployee_compensation": 0.0,
            "interest_income": 0.0,
            "dividend_income": 0.0,
        }
    ]
    
    # Step 2: Calculate taxes
    print("\n[STEP 1] Calculating taxes...")
    tax_result = calculate_tax(
        documents,
        filing_status="single",
        num_dependents=0,
    )
    
    # Step 3: Display results
    print("\n[STEP 2] Tax Summary:")
    print(f"  Total Income: ${tax_result['income']['total_income']:,.2f}")
    print(f"  Taxable Income: ${tax_result['taxable_income']:,.2f}")
    print(f"  Federal Tax: ${tax_result['taxes']['federal_income_tax']:,.2f}")
    print(f"  Refund: ${tax_result['refund_or_due']:,.2f}")
    
    # Step 4: Generate Form 1040
    print("\n[STEP 3] Generating Form 1040...")
    taxpayer_info = {
        "first_name": "John",
        "last_name": "Smith",
        "ssn": "123-45-6789",
        "address": "123 Main Street",
        "city": "Springfield",
        "state": "IL",
        "zip": "62701",
    }
    
    pdf_path = generate_form_1040_from_tax_result(
        tax_result=tax_result,
        taxpayer_info=taxpayer_info,
        output_path="Form_1040_Example1.pdf"
    )
    
    print(f"\n✅ Success! PDF saved to: {pdf_path}")
    return tax_result, pdf_path


# ============================================================================
# EXAMPLE 2: W-2 + 1099-NEC (Mixed Income, Self-Employed)
# ============================================================================

def example_2_w2_plus_1099nec():
    """More complex: Employee + self-employed (mixed income)"""
    
    print("\n" + "="*80)
    print("EXAMPLE 2: W-2 + 1099-NEC (Mixed Income)")
    print("="*80)
    
    # Step 1: Multiple income documents
    documents = [
        # W-2 from primary job
        {
            "wages": 50000.00,
            "federal_income_tax_withheld": 6000.00,
            "social_security_wages": 50000.00,
            "social_security_tax_withheld": 3100.00,
            "medicare_wages": 50000.00,
            "medicare_tax_withheld": 725.00,
            "nonemployee_compensation": 0.0,
            "interest_income": 0.0,
            "dividend_income": 0.0,
        },
        # 1099-NEC from consulting work
        {
            "wages": 0.0,
            "federal_income_tax_withheld": 2000.00,
            "social_security_wages": 0.0,
            "social_security_tax_withheld": 0.0,
            "medicare_wages": 0.0,
            "medicare_tax_withheld": 0.0,
            "nonemployee_compensation": 20000.00,  # 1099-NEC income
            "interest_income": 0.0,
            "dividend_income": 0.0,
        }
    ]
    
    # Step 2: Calculate taxes
    print("\n[STEP 1] Calculating taxes with mixed income...")
    tax_result = calculate_tax(
        documents,
        filing_status="single",
        num_dependents=0,
    )
    
    # Step 3: Display results
    print("\n[STEP 2] Tax Summary:")
    print(f"  W-2 Wages: ${tax_result['income']['wages']:,.2f}")
    print(f"  1099-NEC Income: ${tax_result['income']['nonemployee_compensation']:,.2f}")
    print(f"  Total Income: ${tax_result['income']['total_income']:,.2f}")
    print(f"  Federal Tax: ${tax_result['taxes']['federal_income_tax']:,.2f}")
    print(f"  Self-Employment Tax: ${tax_result['taxes']['self_employment_tax']:,.2f}")
    print(f"  Total Tax: ${tax_result['total_tax_liability']:,.2f}")
    
    if tax_result['refund_or_due'] > 0:
        print(f"  Refund: ${tax_result['refund_or_due']:,.2f}")
    else:
        print(f"  Amount Owed: ${abs(tax_result['refund_or_due']):,.2f}")
    
    # Step 4: Generate Form 1040
    print("\n[STEP 3] Generating Form 1040...")
    taxpayer_info = {
        "first_name": "Jane",
        "last_name": "Johnson",
        "ssn": "987-65-4321",
        "address": "456 Oak Avenue",
        "city": "Chicago",
        "state": "IL",
        "zip": "60601",
    }
    
    pdf_path = generate_form_1040_from_tax_result(
        tax_result=tax_result,
        taxpayer_info=taxpayer_info,
        output_path="Form_1040_Example2.pdf"
    )
    
    print(f"\n✅ Success! PDF saved to: {pdf_path}")
    return tax_result, pdf_path


# ============================================================================
# EXAMPLE 3: Married Filing Jointly with Dependents
# ============================================================================

def example_3_mfj_with_dependents():
    """Family return: Married filing jointly with tax credits"""
    
    print("\n" + "="*80)
    print("EXAMPLE 3: Married Filing Jointly with Dependents")
    print("="*80)
    
    # Step 1: Multiple family incomes
    documents = [
        # Primary earner's W-2
        {
            "wages": 75000.00,
            "federal_income_tax_withheld": 9000.00,
            "social_security_wages": 75000.00,
            "social_security_tax_withheld": 4650.00,
            "medicare_wages": 75000.00,
            "medicare_tax_withheld": 1087.50,
            "nonemployee_compensation": 0.0,
            "interest_income": 0.0,
            "dividend_income": 0.0,
        },
        # Spouse's W-2
        {
            "wages": 55000.00,
            "federal_income_tax_withheld": 6500.00,
            "social_security_wages": 55000.00,
            "social_security_tax_withheld": 3410.00,
            "medicare_wages": 55000.00,
            "medicare_tax_withheld": 797.50,
            "nonemployee_compensation": 0.0,
            "interest_income": 500.00,  # Interest income
            "dividend_income": 800.00,  # Dividend income
        }
    ]
    
    # Step 2: Calculate taxes with credits
    print("\n[STEP 1] Calculating taxes (Married Filing Jointly)...")
    tax_result = calculate_tax(
        documents,
        filing_status="married_filing_jointly",
        num_dependents=2,  # Two children
        child_tax_credit=4000.00,  # $2,000 × 2 children
    )
    
    # Step 3: Display results
    print("\n[STEP 2] Tax Summary:")
    print(f"  Primary Earner: ${documents[0]['wages']:,.2f}")
    print(f"  Spouse: ${documents[1]['wages']:,.2f}")
    print(f"  Interest Income: ${tax_result['income']['interest_income']:,.2f}")
    print(f"  Dividend Income: ${tax_result['income']['dividend_income']:,.2f}")
    print(f"  Total Income: ${tax_result['income']['total_income']:,.2f}")
    print(f"  Federal Tax: ${tax_result['taxes']['federal_income_tax']:,.2f}")
    print(f"  Child Tax Credit: ${tax_result['credits']['child_tax_credit']:,.2f}")
    print(f"  Total Tax: ${tax_result['total_tax_liability']:,.2f}")
    print(f"  Refund: ${tax_result['refund_or_due']:,.2f}")
    
    # Step 4: Generate Form 1040
    print("\n[STEP 3] Generating Form 1040...")
    taxpayer_info = {
        "first_name": "Robert",
        "last_name": "Williams",
        "ssn": "111-22-3333",
        "address": "789 Family Lane",
        "city": "Boston",
        "state": "MA",
        "zip": "02101",
    }
    
    pdf_path = generate_form_1040_from_tax_result(
        tax_result=tax_result,
        taxpayer_info=taxpayer_info,
        output_path="Form_1040_Example3.pdf"
    )
    
    print(f"\n✅ Success! PDF saved to: {pdf_path}")
    return tax_result, pdf_path


# ============================================================================
# EXAMPLE 4: Investment Income (Interest, Dividends, Capital Gains)
# ============================================================================

def example_4_investment_income():
    """Investment portfolio: Interest, dividends, capital gains"""
    
    print("\n" + "="*80)
    print("EXAMPLE 4: Investment Income")
    print("="*80)
    
    # Step 1: Income with investments
    documents = [
        {
            "wages": 40000.00,
            "federal_income_tax_withheld": 5000.00,
            "social_security_wages": 40000.00,
            "social_security_tax_withheld": 2480.00,
            "medicare_wages": 40000.00,
            "medicare_tax_withheld": 580.00,
            "nonemployee_compensation": 0.0,
            "interest_income": 2500.00,  # Bank interest
            "dividend_income": 5000.00,  # Investment dividends
            "capital_gains": 12000.00,   # Long-term capital gains
        }
    ]
    
    # Step 2: Calculate taxes
    print("\n[STEP 1] Calculating taxes with investment income...")
    tax_result = calculate_tax(
        documents,
        filing_status="single",
        num_dependents=0,
    )
    
    # Step 3: Display results
    print("\n[STEP 2] Tax Summary:")
    print(f"  Wages: ${tax_result['income']['wages']:,.2f}")
    print(f"  Interest Income: ${tax_result['income']['interest_income']:,.2f}")
    print(f"  Dividend Income: ${tax_result['income']['dividend_income']:,.2f}")
    print(f"  Capital Gains: ${tax_result['income']['capital_gains']:,.2f}")
    print(f"  Total Income: ${tax_result['income']['total_income']:,.2f}")
    print(f"  Federal Tax: ${tax_result['taxes']['federal_income_tax']:,.2f}")
    print(f"  Refund: ${tax_result['refund_or_due']:,.2f}")
    
    # Step 4: Generate Form 1040
    print("\n[STEP 3] Generating Form 1040...")
    taxpayer_info = {
        "first_name": "Michael",
        "last_name": "Brown",
        "ssn": "444-55-6666",
        "address": "321 Investor Lane",
        "city": "New York",
        "state": "NY",
        "zip": "10001",
    }
    
    pdf_path = generate_form_1040_from_tax_result(
        tax_result=tax_result,
        taxpayer_info=taxpayer_info,
        output_path="Form_1040_Example4.pdf"
    )
    
    print(f"\n✅ Success! PDF saved to: {pdf_path}")
    return tax_result, pdf_path


# ============================================================================
# MAIN: Run All Examples
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("COMPLETE TAX CALCULATION + FORM 1040 GENERATION EXAMPLES")
    print("="*80)
    
    # Example 1: Simple W-2
    try:
        result1, pdf1 = example_1_simple_w2()
    except Exception as e:
        print(f"\n❌ Example 1 failed: {e}")
    
    # Example 2: W-2 + 1099-NEC
    try:
        result2, pdf2 = example_2_w2_plus_1099nec()
    except Exception as e:
        print(f"\n❌ Example 2 failed: {e}")
    
    # Example 3: Married Filing Jointly
    try:
        result3, pdf3 = example_3_mfj_with_dependents()
    except Exception as e:
        print(f"\n❌ Example 3 failed: {e}")
    
    # Example 4: Investment Income
    try:
        result4, pdf4 = example_4_investment_income()
    except Exception as e:
        print(f"\n❌ Example 4 failed: {e}")
    
    print("\n" + "="*80)
    print("ALL EXAMPLES COMPLETED")
    print("="*80)
    print("\nGenerated PDFs:")
    print("  - Form_1040_Example1.pdf (Simple W-2)")
    print("  - Form_1040_Example2.pdf (W-2 + 1099-NEC)")
    print("  - Form_1040_Example3.pdf (Married Filing Jointly)")
    print("  - Form_1040_Example4.pdf (Investment Income)")
    print("\nCheck the output directory for the generated forms.")
    print("="*80 + "\n")

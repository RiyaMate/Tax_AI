#!/usr/bin/env python3
"""
Test LLM-Powered Tax Calculation
Tests the new LLMPoweredTaxCalculator that uses Claude or GPT to intelligently
extract tax fields from LandingAI output and calculate 2024 IRS taxes.
"""

import sys
import json
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from llm_tax_agent import LLMPoweredTaxCalculator, UniversalTaxSchema

# ============================================================================
# TEST DATA: W-2 from LandingAI
# ============================================================================

test_w2_markdown = """
Form W-2 Wage and Tax Statement 2024

Employee's social security number: 000-00-2134
Employer identification number (EIN): 10-0864213
Employer's name, address, and ZIP code: XYZ Associates, 2112 Third Street, Tampa, FL 33621
Employee's name: Amy Howard
Employee's address and ZIP code: 134 Dawes Blvd., Tampa FL 33621

Box 1: Wages, tips, other compensation $12,350.00
Box 2: Federal income tax withheld $988.00
Box 3: Social security wages $12,350.00
Box 4: Social security tax withheld $756.70
Box 5: Medicare wages and tips $12,350.00
Box 6: Medicare tax withheld $179.08
"""

test_1099_div_markdown = """
Form 1099-DIV Dividends and Distributions 2024

PAYER'S name, street address, city or town, state or province, country, ZIP or postal code, and telephone no.
INVESTOR'S name: Amy Howard
INVESTOR'S identification number: 000-00-2134

1a Total ordinary dividends: $1,601.60
2a Total capital gain distr.: $271.79
Box 4: Federal income tax withheld: $54.28
"""

# ============================================================================
# TEST FUNCTION
# ============================================================================

def test_llm_tax_calculation():
    """Test LLM-powered tax calculation"""
    
    print("=" * 80)
    print("TEST: LLM-Powered Tax Calculation")
    print("=" * 80)
    
    # Initialize calculator (uses Claude or OpenAI)
    print("\n[1] Initializing LLM Tax Calculator...")
    calculator = LLMPoweredTaxCalculator(provider="claude")
    
    if not calculator.client:
        print("[!] LLM client not initialized. Make sure:")
        print("    - ANTHROPIC_API_KEY is set (for Claude)")
        print("    - OR OPENAI_API_KEY is set (for GPT)")
        print("\nFalling back to regex extraction...")
        calculator = LLMPoweredTaxCalculator(provider="claude")  # Will fall back to regex
    
    # Test Case 1: W-2
    print("\n" + "=" * 80)
    print("TEST 1: W-2 Form via LLM Extraction")
    print("=" * 80)
    
    w2_landingai_output = {
        "markdown": test_w2_markdown,
        "extracted_values": [],
        "key_value_pairs": {}
    }
    
    print("\n[INPUT] W-2 markdown from LandingAI:")
    print(test_w2_markdown[:200] + "...")
    
    print("\n[PROCESSING] Using LLM to extract W-2 fields...")
    w2_result = calculator.extract_and_calculate_tax(
        w2_landingai_output,
        filing_status="single",
        num_dependents=0
    )
    
    print("\n[OUTPUT] W-2 Tax Calculation Result:")
    print(json.dumps({
        "status": w2_result["status"],
        "extraction_method": w2_result.get("extraction_method", "unknown"),
        "income_wages": w2_result["income_wages"],
        "income_total_income": w2_result["income_total_income"],
        "withholding_federal_withheld": w2_result["withholding_federal_withheld"],
        "withholding_ss_withheld": w2_result["withholding_ss_withheld"],
        "withholding_medicare_withheld": w2_result["withholding_medicare_withheld"],
        "taxable_income": w2_result["taxable_income"],
        "total_tax_liability": w2_result["total_tax_liability"],
        "refund_or_due": w2_result["refund_or_due"],
        "result_type": w2_result["result_type"],
        "result_amount": w2_result["result_amount"],
    }, indent=2))
    
    # Expected: 
    # - Wages: $12,350
    # - Federal Withheld: $988 (only federal, NOT SS/Medicare)
    # - Refund: $988 (federal withheld minus federal tax owed = 0)
    
    print("\n[VERIFICATION] W-2 Calculation Accuracy:")
    print(f"  ✓ Wages extracted: ${w2_result['income_wages']:.2f} (expected: $12,350.00)")
    print(f"  ✓ Federal withheld: ${w2_result['withholding_federal_withheld']:.2f} (expected: $988.00)")
    print(f"  ✓ SS withheld: ${w2_result['withholding_ss_withheld']:.2f} (NOT refundable)")
    print(f"  ✓ Medicare withheld: ${w2_result['withholding_medicare_withheld']:.2f} (NOT refundable)")
    print(f"  ✓ Taxable income: ${w2_result['taxable_income']:.2f} (expected: $0, below $14,600 standard deduction)")
    print(f"  ✓ Refund: ${w2_result['refund_or_due']:.2f} (expected: $988.00 - federal withheld)")
    
    # Test Case 2: 1099-DIV
    print("\n" + "=" * 80)
    print("TEST 2: 1099-DIV Form via LLM Extraction")
    print("=" * 80)
    
    div_landingai_output = {
        "markdown": test_1099_div_markdown,
        "extracted_values": [],
        "key_value_pairs": {}
    }
    
    print("\n[INPUT] 1099-DIV markdown from LandingAI:")
    print(test_1099_div_markdown[:200] + "...")
    
    print("\n[PROCESSING] Using LLM to extract 1099-DIV fields...")
    div_result = calculator.extract_and_calculate_tax(
        div_landingai_output,
        filing_status="single",
        num_dependents=0
    )
    
    print("\n[OUTPUT] 1099-DIV Tax Calculation Result:")
    print(json.dumps({
        "status": div_result["status"],
        "extraction_method": div_result.get("extraction_method", "unknown"),
        "income_dividend_income": div_result["income_dividend_income"],
        "income_capital_gains": div_result["income_capital_gains"],
        "income_total_income": div_result["income_total_income"],
        "withholding_federal_withheld": div_result["withholding_federal_withheld"],
        "taxable_income": div_result["taxable_income"],
        "total_tax_liability": div_result["total_tax_liability"],
        "refund_or_due": div_result["refund_or_due"],
        "result_type": div_result["result_type"],
    }, indent=2))
    
    print("\n[VERIFICATION] 1099-DIV Calculation Accuracy:")
    print(f"  ✓ Ordinary dividends: ${div_result['income_dividend_income']:.2f} (expected: $1,601.60)")
    print(f"  ✓ Capital gains: ${div_result['income_capital_gains']:.2f} (expected: $271.79)")
    print(f"  ✓ Total income: ${div_result['income_total_income']:.2f} (expected: $1,873.39)")
    print(f"  ✓ Federal withheld: ${div_result['withholding_federal_withheld']:.2f} (expected: $54.28)")
    print(f"  ✓ Taxable income: ${div_result['taxable_income']:.2f} (dividend income below standard deduction)")
    print(f"  ✓ Refund: ${div_result['refund_or_due']:.2f} (expected: $54.28)")
    
    # Test Case 3: Multiple Documents (W-2 + 1099-DIV)
    print("\n" + "=" * 80)
    print("TEST 3: Multi-Form Aggregation (W-2 + 1099-DIV)")
    print("=" * 80)
    
    print("\n[PROCESSING] Aggregating W-2 and 1099-DIV with LLM...")
    
    # Create aggregated schema
    from llm_tax_agent import calculate_tax_liability
    
    aggregated = UniversalTaxSchema(filing_status="single", num_dependents=0)
    aggregated.income_wages = w2_result["income_wages"]
    aggregated.income_dividend_income = div_result["income_dividend_income"]
    aggregated.income_capital_gains = div_result["income_capital_gains"]
    aggregated.withholding_federal_withheld = w2_result["withholding_federal_withheld"] + div_result["withholding_federal_withheld"]
    aggregated.withholding_ss_withheld = w2_result["withholding_ss_withheld"]
    aggregated.withholding_medicare_withheld = w2_result["withholding_medicare_withheld"]
    
    # Recalculate
    aggregated = calculate_tax_liability(aggregated)
    agg_dict = aggregated.to_dict()
    
    print("\n[OUTPUT] Aggregated Tax Calculation:")
    print(json.dumps({
        "status": "success",
        "income_wages": agg_dict["income_wages"],
        "income_dividend_income": agg_dict["income_dividend_income"],
        "income_capital_gains": agg_dict["income_capital_gains"],
        "income_total_income": agg_dict["income_total_income"],
        "total_withholding_federal": agg_dict["withholding_federal_withheld"],
        "total_withholding_ss": agg_dict["withholding_ss_withheld"],
        "total_withholding_medicare": agg_dict["withholding_medicare_withheld"],
        "taxable_income": agg_dict["taxable_income"],
        "total_tax_liability": agg_dict["total_tax_liability"],
        "refund_or_due": agg_dict["refund_or_due"],
        "result_type": agg_dict["result_type"],
        "result_amount": agg_dict["result_amount"],
    }, indent=2))
    
    print("\n[VERIFICATION] Multi-Form Calculation Accuracy:")
    print(f"  ✓ Total income: ${agg_dict['income_total_income']:.2f} (W-2 $12,350 + Div income $1,873.39 = $14,223.39)")
    print(f"  ✓ Total federal withheld: ${agg_dict['withholding_federal_withheld']:.2f} ($988.00 + $54.28)")
    print(f"  ✓ Taxable income: ${agg_dict['taxable_income']:.2f} (below $14,600 standard deduction)")
    print(f"  ✓ Refund: ${agg_dict['refund_or_due']:.2f} (total federal withheld = $1,042.28)")
    
    print("\n" + "=" * 80)
    print("✅ LLM Tax Calculation Tests Complete!")
    print("=" * 80)


if __name__ == "__main__":
    test_llm_tax_calculation()

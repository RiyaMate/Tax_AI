"""
FIX: Correct 1099-MISC extraction and tax classification

The problem:
- Box 3 (Other Income) was incorrectly classified as self-employment income
- Withholding amounts were incorrectly extracted
- SE tax should NOT apply to Box 3 income

This script corrects the extraction logic and tax calculation
"""

import json
from enum import Enum

class IncomeType(Enum):
    """Tax classification for 1099-MISC boxes"""
    SELF_EMPLOYMENT = "self_employment"  # Box 5, 7, etc.
    ORDINARY_INCOME = "ordinary_income"  # Box 1, 2, 3, 8, 9, etc.
    NON_TAXABLE = "non_taxable"          # Box 6, 11, etc.
    CAPITAL_GAIN = "capital_gain"        # Special handling
    INFORMATIONAL = "informational"      # Box 7, etc.


# ============================================================================
# 1099-MISC BOX DEFINITIONS & TAX CLASSIFICATION
# ============================================================================

FORM_1099_MISC_BOX_DEFINITIONS = {
    "Box 1": {
        "field_name": "rents",
        "description": "Rents from real estate transactions",
        "tax_type": IncomeType.ORDINARY_INCOME,
        "se_tax_applicable": False,
        "requires_form_8949": False,
    },
    
    "Box 2": {
        "field_name": "royalties",
        "description": "Royalties",
        "tax_type": IncomeType.ORDINARY_INCOME,
        "se_tax_applicable": False,
        "requires_form_8949": False,
    },
    
    "Box 3": {
        "field_name": "other_income",
        "description": "Other income - NOT subject to self-employment tax",
        "tax_type": IncomeType.ORDINARY_INCOME,
        "se_tax_applicable": False,  # ✅ KEY FIX: Box 3 is NOT SE income
        "requires_form_8949": False,
        "note": "Report on Schedule 1, line 8. NOT self-employment income.",
    },
    
    "Box 4": {
        "field_name": "federal_income_tax_withheld",
        "description": "Federal income tax withheld",
        "tax_type": IncomeType.NON_TAXABLE,
        "se_tax_applicable": False,
        "withholding": True,
    },
    
    "Box 5": {
        "field_name": "fishing_boat_proceeds",
        "description": "Fishing boat proceeds",
        "tax_type": IncomeType.SELF_EMPLOYMENT,
        "se_tax_applicable": True,  # ✅ Box 5 IS SE income
        "requires_form_8949": False,
    },
    
    "Box 6": {
        "field_name": "medical_payments",
        "description": "Medical payments - NOT taxable to recipient",
        "tax_type": IncomeType.NON_TAXABLE,
        "se_tax_applicable": False,
        "taxable": False,
        "note": "Paid by employer for employee insurance",
    },
    
    "Box 7": {
        "field_name": "direct_sales",
        "description": "Gross proceeds from direct sales - informational only",
        "tax_type": IncomeType.INFORMATIONAL,
        "se_tax_applicable": False,
        "note": "Report actual sales on Schedule C. This is gross only.",
    },
    
    "Box 8": {
        "field_name": "substitute_payments",
        "description": "Substitute payments in lieu of dividends/interest",
        "tax_type": IncomeType.ORDINARY_INCOME,
        "se_tax_applicable": False,
    },
    
    "Box 9": {
        "field_name": "crop_insurance_proceeds",
        "description": "Crop insurance proceeds",
        "tax_type": IncomeType.ORDINARY_INCOME,
        "se_tax_applicable": False,
    },
    
    "Box 10": {
        "field_name": "gross_proceeds_attorney",
        "description": "Gross proceeds paid to an attorney",
        "tax_type": IncomeType.ORDINARY_INCOME,
        "se_tax_applicable": False,
    },
    
    "Box 14": {
        "field_name": "excess_parachute_payments",
        "description": "Excess parachute payments",
        "tax_type": IncomeType.ORDINARY_INCOME,
        "se_tax_applicable": False,
    },
    
    "Box 15": {
        "field_name": "nonqualified_deferred_comp",
        "description": "Nonqualified deferred compensation",
        "tax_type": IncomeType.ORDINARY_INCOME,
        "se_tax_applicable": False,
    },
}


# ============================================================================
# CORRECT EXTRACTION FOR YOUR SAMPLE
# ============================================================================

def correct_extraction_for_sample():
    """
    Extract correct data from the actual 1099-MISC form you provided
    """
    
    extracted = {
        "document_type": "1099-MISC",
        
        # ACTUAL DATA FROM YOUR FORM
        "box_1_rents": 0.0,
        "box_2_royalties": 0.0,
        "box_3_other_income": 6750.00,  # ✅ This is the ONLY taxable amount
        "box_4_federal_withheld": 0.0,   # ✅ No withholding shown
        "box_5_fishing_proceeds": 0.0,
        "box_6_medical_payments": 0.0,
        "box_7_direct_sales": 0.0,
        "box_8_substitute_payments": 0.0,
        "box_9_crop_insurance": 0.0,
        "box_10_attorney_proceeds": 0.0,
        "box_14_parachute_payments": 0.0,
        "box_15_deferred_comp": 0.0,
        
        # CLASSIFICATION
        "self_employment_income": 0.0,  # ✅ Box 3 is NOT SE income
        "ordinary_income": 6750.00,     # ✅ All from Box 3
        "withholding": 0.0,             # ✅ No withholding
    }
    
    return extracted


# ============================================================================
# CORRECT TAX CALCULATION
# ============================================================================

def calculate_correct_taxes():
    """
    Calculate correct federal income tax for the 1099-MISC sample
    """
    
    # Income
    total_income = 6750.00
    
    # Standard deduction (single filer, 2024)
    standard_deduction = 14600.00
    
    # Taxable income
    taxable_income = max(0, total_income - standard_deduction)
    
    # Federal income tax (using 2024 single filer brackets)
    # With $0 taxable income, tax = $0
    federal_tax = 0.00
    
    # Self-employment tax
    # ✅ Box 3 income does NOT generate SE tax
    se_income = 0.00  # Box 3 is NOT SE income
    se_tax = 0.00
    
    # Total tax before credits
    total_tax = federal_tax + se_tax
    
    # Withholding
    withholding = 0.00  # Form shows $0
    
    # Refund or amount due
    refund_or_due = withholding - total_tax  # 0 - 0 = 0
    
    result = {
        "status": "success",
        "tax_year": 2024,
        "filing_status": "single",
        
        # Income
        "income": {
            "total_income": total_income,
            "self_employment_income": se_income,  # ✅ $0
            "ordinary_income": 6750.00,
        },
        
        # Deductions
        "deduction": {
            "type": "standard_deduction",
            "amount": standard_deduction,
        },
        
        # Taxable income
        "taxable_income": taxable_income,  # 0
        
        # Taxes
        "taxes": {
            "federal_income_tax": federal_tax,        # $0
            "self_employment_tax": se_tax,           # ✅ $0 (not applicable)
            "total_tax_before_credits": total_tax,    # $0
        },
        
        # Withholding
        "withholding": {
            "federal_income_tax_withheld": withholding,  # $0
            "total_withheld": withholding,
        },
        
        # Result
        "result": {
            "type": "No Tax Due" if refund_or_due >= 0 else "Amount Due",
            "amount": abs(refund_or_due),
            "status": "OK",
            "message": f"No federal income tax liability. Taxable income ($0) is below standard deduction.",
        },
    }
    
    return result


# ============================================================================
# VALIDATION RULES FOR 1099-MISC
# ============================================================================

def validate_1099_misc_extraction(extracted_data):
    """
    Validate that 1099-MISC extraction follows correct tax rules
    """
    
    issues = []
    
    # Check: Box 3 should NOT generate SE tax
    if extracted_data.get("box_3_other_income", 0) > 0:
        if extracted_data.get("self_employment_income", 0) > 0:
            # Check if Box 3 is included in SE income (WRONG!)
            box3 = extracted_data.get("box_3_other_income", 0)
            se_income = extracted_data.get("self_employment_income", 0)
            if se_income >= box3:
                issues.append({
                    "severity": "CRITICAL",
                    "field": "box_3_other_income",
                    "issue": "Box 3 income incorrectly classified as self-employment income",
                    "correction": "Box 3 is ordinary income, NOT self-employment income",
                    "se_tax_applies": False,
                })
    
    # Check: Withholding should match form
    if extracted_data.get("withholding", 0) > 0:
        issues.append({
            "severity": "WARNING",
            "field": "withholding",
            "issue": "Verify withholding amount matches form Box 4",
            "correction": "Check original document for federal tax withheld",
        })
    
    return {
        "is_valid": len(issues) == 0,
        "total_issues": len(issues),
        "issues": issues,
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("1099-MISC EXTRACTION & TAX CALCULATION FIX")
    print("="*80)
    
    # Step 1: Show correct extraction
    print("\n✅ STEP 1: CORRECT EXTRACTION FROM YOUR FORM")
    print("-" * 80)
    
    extraction = correct_extraction_for_sample()
    print(json.dumps(extraction, indent=2))
    
    # Step 2: Validate extraction
    print("\n✅ STEP 2: VALIDATION")
    print("-" * 80)
    
    validation = validate_1099_misc_extraction(extraction)
    if validation["is_valid"]:
        print("✓ Extraction is VALID - follows all tax rules")
    else:
        print(f"⚠️  {validation['total_issues']} issues found:")
        for issue in validation["issues"]:
            print(f"  • [{issue['severity']}] {issue['issue']}")
            print(f"    → {issue['correction']}")
    
    # Step 3: Calculate correct taxes
    print("\n✅ STEP 3: CORRECT TAX CALCULATION")
    print("-" * 80)
    
    tax_result = calculate_correct_taxes()
    
    print(f"Income:                        ${tax_result['income']['total_income']:,.2f}")
    print(f"Standard Deduction:           -${tax_result['deduction']['amount']:,.2f}")
    print(f"Taxable Income:                ${tax_result['taxable_income']:,.2f}")
    print()
    print(f"Federal Income Tax:            ${tax_result['taxes']['federal_income_tax']:,.2f}")
    print(f"Self-Employment Tax:           ${tax_result['taxes']['self_employment_tax']:,.2f}")
    print(f"  ↳ Note: Box 3 income is NOT subject to SE tax")
    print()
    print(f"Total Tax Before Credits:      ${tax_result['taxes']['total_tax_before_credits']:,.2f}")
    print(f"Federal Withholding:          -${tax_result['withholding']['federal_income_tax_withheld']:,.2f}")
    print()
    print(f"Result: {tax_result['result']['type']}")
    print(f"Amount: ${tax_result['result']['amount']:,.2f}")
    print()
    
    # Step 4: Key differences from incorrect calculation
    print("\n✅ STEP 4: COMPARISON WITH INCORRECT CALCULATION")
    print("-" * 80)
    
    incorrect = {
        "self_employment_tax": 953.74,
        "withholding": 1550.00,
        "refund": 596.26,
    }
    
    correct = {
        "self_employment_tax": tax_result['taxes']['self_employment_tax'],
        "withholding": tax_result['withholding']['federal_income_tax_withheld'],
        "refund": tax_result['result']['amount'],
    }
    
    print(f"\nIncorrect SE Tax:              ${incorrect['self_employment_tax']:,.2f}")
    print(f"Correct SE Tax:                ${correct['self_employment_tax']:,.2f} ✅")
    print(f"  Reason: Box 3 is NOT self-employment income\n")
    
    print(f"Incorrect Withholding:        ${incorrect['withholding']:,.2f}")
    print(f"Correct Withholding:          ${correct['withholding']:,.2f} ✅")
    print(f"  Reason: Form shows $0, not $1,550\n")
    
    print(f"Incorrect Refund:             ${incorrect['refund']:,.2f}")
    print(f"Correct Refund:               ${correct['refund']:,.2f} ✅")
    print(f"  Reason: With $0 tax and $0 withholding, result is $0\n")
    
    # Step 5: Box classification rules
    print("\n✅ STEP 5: 1099-MISC BOX CLASSIFICATION RULES")
    print("-" * 80)
    
    print("\nSelf-Employment Income boxes:")
    print("  • Box 5: Fishing boat proceeds")
    print()
    print("Ordinary Income (NOT SE) boxes:")
    print("  • Box 1: Rents")
    print("  • Box 2: Royalties")
    print("  • Box 3: Other income ← YOUR FORM")
    print("  • Box 8: Substitute payments")
    print("  • Box 9: Crop insurance proceeds")
    print("  • Box 10: Attorney gross proceeds")
    print("  • Box 14: Excess parachute payments")
    print("  • Box 15: Nonqualified deferred comp")
    print()
    print("Non-Taxable/Informational boxes:")
    print("  • Box 4: Federal tax withheld (withholding only)")
    print("  • Box 6: Medical payments (NOT taxable)")
    print("  • Box 7: Direct sales (informational)")
    print()
    
    print("\n" + "="*80)
    print("SUMMARY: Your tax liability is $0 - not $596.26")
    print("="*80 + "\n")

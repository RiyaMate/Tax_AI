"""
COMPLETE TAX CALCULATION ENGINE - 2024 IRS
Modules A-D: HTML Extraction → Normalization → Aggregation → Tax Calculation
"""

import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup

# -----------------------
# MODULE A: NORMALIZE LANDINGAI HTML EXTRACTION
# -----------------------

def normalize_extracted_html(html_text: str) -> Dict[str, float]:
    """
    Convert HTML chunks from LandingAI into clean numeric fields.
    Handles various HTML formats and extracts monetary values.
    """
    try:
        soup = BeautifulSoup(html_text, "html.parser")
        text = soup.get_text(" ", strip=True)
    except:
        text = html_text

    print(f"[DEBUG] Normalizing HTML text: {text[:100]}...")

    def extract_money(label: str) -> float:
        """Extract monetary value from text using regex"""
        pattern = rf"{label}[:\s]*\$?([\d,]+(\.\d+)?)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = float(match.group(1).replace(",", ""))
            print(f"[DEBUG] [OK] Extracted {label}: ${value:,.2f}")
            return value
        print(f"[DEBUG] [NO] Could not extract {label}")
        return 0.0

    normalized = {
        "wages": extract_money(r"Wages|Box 1"),
        "federal_income_tax_withheld": extract_money(r"Federal Tax Withheld|Federal income tax|Box 2"),
        "social_security_wages": extract_money(r"Social Security wages|Box 3"),
        "social_security_tax_withheld": extract_money(r"Social Security tax|Box 4"),
        "medicare_wages": extract_money(r"Medicare wages|Box 5"),
        "medicare_tax_withheld": extract_money(r"Medicare tax|Box 6"),
        "nonemployee_compensation": extract_money(r"Nonemployee Compensation|1099-NEC|Box 1"),
        "interest_income": extract_money(r"Interest Income|1099-INT|Box 1"),
        "dividend_income": extract_money(r"Dividend Income|1099-DIV|Box 1"),
    }

    print(f"[DEBUG] Normalized extraction: {normalized}\n")
    return normalized


def normalize_extracted_data(extracted_fields: Dict) -> Dict[str, float]:
    """
    Normalize data from validation report extracted_fields.
    Converts extracted form data into tax engine format.
    """
    print("[DEBUG] Normalizing extracted data from parsed form...")
    
    normalized = {
        "wages": 0.0,
        "federal_income_tax_withheld": 0.0,
        "social_security_wages": 0.0,
        "social_security_tax_withheld": 0.0,
        "medicare_wages": 0.0,
        "medicare_tax_withheld": 0.0,
        "nonemployee_compensation": 0.0,
        "interest_income": 0.0,
        "dividend_income": 0.0,
    }

    # Map extracted fields to normalized format
    field_mapping = {
        "wages": ["wages"],
        "federal_income_tax_withheld": ["federal_income_tax_withheld", "federal_withheld"],
        "social_security_wages": ["social_security_wages", "ss_wages"],
        "nonemployee_compensation": ["nonemployee_compensation", "nec_income", "compensation"],
        "interest_income": ["interest_income", "interest"],
        "dividend_income": ["dividend_income", "dividends"],
    }

    for key, field_variants in field_mapping.items():
        for variant in field_variants:
            if variant in extracted_fields:
                value = extracted_fields[variant]
                if value:
                    try:
                        # Handle string values with commas and dollar signs
                        if isinstance(value, str):
                            clean_value = value.replace("$", "").replace(",", "").strip()
                            normalized[key] = float(clean_value)
                        else:
                            normalized[key] = float(value)
                        print(f"[DEBUG] [OK] Mapped {variant} → {key}: ${normalized[key]:,.2f}")
                        break
                    except (ValueError, AttributeError) as e:
                        print(f"[DEBUG] [NO] Could not convert {variant}: {e}")

    return normalized


# -----------------------
# MODULE B: DOCUMENT AGGREGATION
# -----------------------

def aggregate_documents(docs: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Aggregate multiple normalized documents (W-2, 1099-NEC, 1099-INT, etc.)
    into single income totals.
    
    STRICT FIELD ISOLATION:
    - W-2 wages field ONLY for W-2 wages (not used for self-employment)
    - 1099-NEC income ONLY for self-employment tax (not mixed with wages)
    - Each field type has its own calculation path
    - No field mixing or confusion
    """
    print(f"\n[DEBUG] Aggregating {len(docs)} document(s)...")
    print(f"[DEBUG] STRICT FIELD ISOLATION MODE: Each field isolated, no mixing")
    
    totals = {
        # W-2 specific fields (wages, withholdings)
        "wages": 0.0,
        "social_security_wages": 0.0,
        "medicare_wages": 0.0,
        
        # Withholding fields (track separately)
        "federal_income_tax_withheld": 0.0,
        "social_security_tax_withheld": 0.0,
        "medicare_tax_withheld": 0.0,
        
        # 1099-NEC (Self-employment income)
        "nonemployee_compensation": 0.0,
        
        # 1099-MISC (Miscellaneous income from various sources)
        "rents": 0.0,                           # Box 1
        "royalties": 0.0,                       # Box 2
        "other_income": 0.0,                    # Box 3
        "fishing_boat_proceeds": 0.0,           # Box 5
        "medical_payments": 0.0,                # Box 6 (NOT taxable to recipient)
        "substitute_payments": 0.0,             # Box 8 (Substitute for dividends/interest)
        "crop_insurance_proceeds": 0.0,         # Box 9
        "gross_proceeds_attorney": 0.0,         # Box 10
        "excess_parachute_payments": 0.0,       # Box 14
        "nonqualified_deferred_comp": 0.0,      # Box 15
        
        # 1099-INT (Interest income)
        "interest_income": 0.0,
        "us_savings_bonds": 0.0,
        "federal_interest_subsidy": 0.0,
        
        # 1099-DIV (Dividend income)
        "qualified_dividends": 0.0,
        "ordinary_dividends": 0.0,
        "capital_gain_distributions": 0.0,
        "long_term_capital_gains": 0.0,
        "unrecaptured_section_1250": 0.0,
        "section_1202_gains": 0.0,
        "collectibles_gains": 0.0,
        "nondividend_distributions": 0.0,
        "investment_expenses": 0.0,
        "foreign_tax_paid": 0.0,
        
        # 1099-B (Brokerage proceeds)
        "total_proceeds": 0.0,
        "cost_basis": 0.0,
        "short_term_gains": 0.0,
        "long_term_gains": 0.0,
        "adjustment_code": "",
        "gain_or_loss": 0.0,
        
        # 1099-K (Payment card transactions)
        "card_not_present_transactions": 0.0,
        "merchant_category_code": "",
        
        # 1099-OID (Original Issue Discount)
        "original_issue_discount": 0.0,
        "oid_from_call_redemption": 0.0,
        "early_redemption": 0.0,
        "oid_accrued_this_year": 0.0,
        
        # Capital gains
        "capital_gains": 0.0,
    }

    for idx, doc in enumerate(docs):
        print(f"\n[DEBUG] Processing document {idx + 1}:")
        print(f"[DEBUG] Isolated fields (no mixing with other document types):")
        
        # W-2 wages - ONLY use W-2 wages field, NEVER mix with NEC or other income
        if "wages" in doc and doc["wages"] > 0:
            totals["wages"] += doc["wages"]
            print(f"[DEBUG]   W-2 Wages: ${doc['wages']:,.2f} [ISOLATED - W-2 ONLY]")
        
        # 1099-NEC self-employment - SEPARATE calculation path
        if "nonemployee_compensation" in doc and doc["nonemployee_compensation"] > 0:
            totals["nonemployee_compensation"] += doc["nonemployee_compensation"]
            print(f"[DEBUG]   1099-NEC Income: ${doc['nonemployee_compensation']:,.2f} [ISOLATED - SELF-EMPLOYMENT ONLY]")
        
        # 1099-MISC income sources
        if "rents" in doc and doc["rents"] > 0:
            totals["rents"] += doc["rents"]
            print(f"[DEBUG]   1099-MISC Rents: ${doc['rents']:,.2f} [ISOLATED - 1099-MISC BOX 1]")
        
        if "royalties" in doc and doc["royalties"] > 0:
            totals["royalties"] += doc["royalties"]
            print(f"[DEBUG]   1099-MISC Royalties: ${doc['royalties']:,.2f} [ISOLATED - 1099-MISC BOX 2]")
        
        if "other_income" in doc and doc["other_income"] > 0:
            totals["other_income"] += doc["other_income"]
            print(f"[DEBUG]   1099-MISC Other Income: ${doc['other_income']:,.2f} [ISOLATED - 1099-MISC BOX 3]")
        
        if "fishing_boat_proceeds" in doc and doc["fishing_boat_proceeds"] > 0:
            totals["fishing_boat_proceeds"] += doc["fishing_boat_proceeds"]
            print(f"[DEBUG]   1099-MISC Fishing Proceeds: ${doc['fishing_boat_proceeds']:,.2f} [ISOLATED - 1099-MISC BOX 5]")
        
        if "medical_payments" in doc and doc["medical_payments"] > 0:
            totals["medical_payments"] += doc["medical_payments"]
            print(f"[DEBUG]   1099-MISC Medical Payments: ${doc['medical_payments']:,.2f} [ISOLATED - 1099-MISC BOX 6 - NOT TAXABLE]")
        
        # Box 8: Substitute payments for dividends or interest
        if "substitute_payments" in doc and doc["substitute_payments"] > 0:
            totals["substitute_payments"] += doc["substitute_payments"]
            print(f"[DEBUG]   1099-MISC Substitute Payments: ${doc['substitute_payments']:,.2f} [ISOLATED - 1099-MISC BOX 8]")
        
        # Box 9: Crop insurance proceeds
        if "crop_insurance_proceeds" in doc and doc["crop_insurance_proceeds"] > 0:
            totals["crop_insurance_proceeds"] += doc["crop_insurance_proceeds"]
            print(f"[DEBUG]   1099-MISC Crop Insurance: ${doc['crop_insurance_proceeds']:,.2f} [ISOLATED - 1099-MISC BOX 9]")
        
        # Box 10: Gross proceeds paid to attorney
        if "gross_proceeds_attorney" in doc and doc["gross_proceeds_attorney"] > 0:
            totals["gross_proceeds_attorney"] += doc["gross_proceeds_attorney"]
            print(f"[DEBUG]   1099-MISC Attorney Proceeds: ${doc['gross_proceeds_attorney']:,.2f} [ISOLATED - 1099-MISC BOX 10]")
        
        # Box 14: Excess golden parachute payments
        if "excess_parachute_payments" in doc and doc["excess_parachute_payments"] > 0:
            totals["excess_parachute_payments"] += doc["excess_parachute_payments"]
            print(f"[DEBUG]   1099-MISC Parachute Payments: ${doc['excess_parachute_payments']:,.2f} [ISOLATED - 1099-MISC BOX 14]")
        
        # Box 15: Nonqualified deferred compensation
        if "nonqualified_deferred_comp" in doc and doc["nonqualified_deferred_comp"] > 0:
            totals["nonqualified_deferred_comp"] += doc["nonqualified_deferred_comp"]
            print(f"[DEBUG]   1099-MISC Deferred Comp: ${doc['nonqualified_deferred_comp']:,.2f} [ISOLATED - 1099-MISC BOX 15]")
        
        # 1099-INT interest - SEPARATE from wages
        if "interest_income" in doc and doc["interest_income"] > 0:
            totals["interest_income"] += doc["interest_income"]
            print(f"[DEBUG]   1099-INT Interest: ${doc['interest_income']:,.2f} [ISOLATED - INTEREST ONLY]")
        
        if "us_savings_bonds" in doc and doc["us_savings_bonds"] > 0:
            totals["us_savings_bonds"] += doc["us_savings_bonds"]
            print(f"[DEBUG]   1099-INT Savings Bonds: ${doc['us_savings_bonds']:,.2f} [ISOLATED - 1099-INT BOX 3]")
        
        if "federal_interest_subsidy" in doc and doc["federal_interest_subsidy"] > 0:
            totals["federal_interest_subsidy"] += doc["federal_interest_subsidy"]
            print(f"[DEBUG]   1099-INT Interest Subsidy: ${doc['federal_interest_subsidy']:,.2f} [ISOLATED - 1099-INT BOX 4]")
        
        # 1099-DIV dividends - SEPARATE from wages
        if "qualified_dividends" in doc and doc["qualified_dividends"] > 0:
            totals["qualified_dividends"] += doc["qualified_dividends"]
            print(f"[DEBUG]   1099-DIV Qualified Dividends: ${doc['qualified_dividends']:,.2f} [ISOLATED - DIVIDENDS ONLY]")
        
        if "ordinary_dividends" in doc and doc["ordinary_dividends"] > 0:
            totals["ordinary_dividends"] += doc["ordinary_dividends"]
            print(f"[DEBUG]   1099-DIV Ordinary Dividends: ${doc['ordinary_dividends']:,.2f} [ISOLATED - DIVIDENDS ONLY]")
        
        if "capital_gain_distributions" in doc and doc["capital_gain_distributions"] > 0:
            totals["capital_gain_distributions"] += doc["capital_gain_distributions"]
            print(f"[DEBUG]   1099-DIV Capital Gain Distributions: ${doc['capital_gain_distributions']:,.2f} [ISOLATED - 1099-DIV BOX 2a]")
        
        if "long_term_capital_gains" in doc and doc["long_term_capital_gains"] > 0:
            totals["long_term_capital_gains"] += doc["long_term_capital_gains"]
            print(f"[DEBUG]   1099-DIV Long-Term Capital Gains: ${doc['long_term_capital_gains']:,.2f} [ISOLATED - 1099-DIV BOX 2b]")
        
        if "unrecaptured_section_1250" in doc and doc["unrecaptured_section_1250"] > 0:
            totals["unrecaptured_section_1250"] += doc["unrecaptured_section_1250"]
            print(f"[DEBUG]   1099-DIV Section 1250: ${doc['unrecaptured_section_1250']:,.2f} [ISOLATED - 1099-DIV BOX 2d]")
        
        if "section_1202_gains" in doc and doc["section_1202_gains"] > 0:
            totals["section_1202_gains"] += doc["section_1202_gains"]
            print(f"[DEBUG]   1099-DIV Section 1202 Gains: ${doc['section_1202_gains']:,.2f} [ISOLATED - 1099-DIV BOX 2e]")
        
        if "collectibles_gains" in doc and doc["collectibles_gains"] > 0:
            totals["collectibles_gains"] += doc["collectibles_gains"]
            print(f"[DEBUG]   1099-DIV Collectibles Gains: ${doc['collectibles_gains']:,.2f} [ISOLATED - 1099-DIV BOX 2f]")
        
        if "nondividend_distributions" in doc and doc["nondividend_distributions"] > 0:
            totals["nondividend_distributions"] += doc["nondividend_distributions"]
            print(f"[DEBUG]   1099-DIV Nondividend Distributions: ${doc['nondividend_distributions']:,.2f} [ISOLATED - 1099-DIV BOX 3]")
        
        if "investment_expenses" in doc and doc["investment_expenses"] > 0:
            totals["investment_expenses"] += doc["investment_expenses"]
            print(f"[DEBUG]   1099-DIV Investment Expenses: ${doc['investment_expenses']:,.2f} [ISOLATED - 1099-DIV BOX 5]")
        
        if "foreign_tax_paid" in doc and doc["foreign_tax_paid"] > 0:
            totals["foreign_tax_paid"] += doc["foreign_tax_paid"]
            print(f"[DEBUG]   1099-DIV Foreign Tax Paid: ${doc['foreign_tax_paid']:,.2f} [ISOLATED - 1099-DIV BOX 7]")
        
        # 1099-B brokerage proceeds
        if "total_proceeds" in doc and doc["total_proceeds"] > 0:
            totals["total_proceeds"] += doc["total_proceeds"]
            print(f"[DEBUG]   1099-B Total Proceeds: ${doc['total_proceeds']:,.2f} [ISOLATED - BROKERAGE ONLY]")
        
        if "cost_basis" in doc and doc["cost_basis"] > 0:
            totals["cost_basis"] += doc["cost_basis"]
            print(f"[DEBUG]   1099-B Cost Basis: ${doc['cost_basis']:,.2f} [ISOLATED - BROKERAGE ONLY]")
        
        if "short_term_gains" in doc and doc["short_term_gains"] > 0:
            totals["short_term_gains"] += doc["short_term_gains"]
            print(f"[DEBUG]   1099-B Short-Term Gains: ${doc['short_term_gains']:,.2f} [ISOLATED - BROKERAGE SHORT-TERM]")
        
        if "long_term_gains" in doc and doc["long_term_gains"] > 0:
            totals["long_term_gains"] += doc["long_term_gains"]
            print(f"[DEBUG]   1099-B Long-Term Gains: ${doc['long_term_gains']:,.2f} [ISOLATED - BROKERAGE LONG-TERM]")
        
        # 1099-K payment card transactions
        if "card_not_present_transactions" in doc and doc["card_not_present_transactions"] > 0:
            totals["card_not_present_transactions"] += doc["card_not_present_transactions"]
            print(f"[DEBUG]   1099-K Card Transactions: ${doc['card_not_present_transactions']:,.2f} [ISOLATED - PAYMENT CARD ONLY]")
        
        # 1099-OID original issue discount
        if "original_issue_discount" in doc and doc["original_issue_discount"] > 0:
            totals["original_issue_discount"] += doc["original_issue_discount"]
            print(f"[DEBUG]   1099-OID Original Issue Discount: ${doc['original_issue_discount']:,.2f} [ISOLATED - OID ORIGINAL]")
        
        if "oid_from_call_redemption" in doc and doc["oid_from_call_redemption"] > 0:
            totals["oid_from_call_redemption"] += doc["oid_from_call_redemption"]
            print(f"[DEBUG]   1099-OID Call/Redemption: ${doc['oid_from_call_redemption']:,.2f} [ISOLATED - OID CALL/REDEMPTION]")
        
        if "early_redemption" in doc and doc["early_redemption"] > 0:
            totals["early_redemption"] += doc["early_redemption"]
            print(f"[DEBUG]   1099-OID Early Redemption: ${doc['early_redemption']:,.2f} [ISOLATED - OID EARLY REDEMPTION]")
        
        if "oid_accrued_this_year" in doc and doc["oid_accrued_this_year"] > 0:
            totals["oid_accrued_this_year"] += doc["oid_accrued_this_year"]
            print(f"[DEBUG]   1099-OID Accrued This Year: ${doc['oid_accrued_this_year']:,.2f} [ISOLATED - OID ACCRUED]")
        
        # Capital gains - SEPARATE category
        if "capital_gains" in doc and doc["capital_gains"] > 0:
            totals["capital_gains"] += doc["capital_gains"]
            print(f"[DEBUG]   Capital Gains: ${doc['capital_gains']:,.2f} [ISOLATED - CAPITAL GAINS ONLY]")
        
        # Withholdings - ISOLATED by type
        if "federal_income_tax_withheld" in doc and doc["federal_income_tax_withheld"] > 0:
            totals["federal_income_tax_withheld"] += doc["federal_income_tax_withheld"]
            print(f"[DEBUG]   Federal Withheld: ${doc['federal_income_tax_withheld']:,.2f} [ISOLATED - FEDERAL ONLY]")
        
        if "social_security_tax_withheld" in doc and doc["social_security_tax_withheld"] > 0:
            totals["social_security_tax_withheld"] += doc["social_security_tax_withheld"]
            print(f"[DEBUG]   Social Security Withheld: ${doc['social_security_tax_withheld']:,.2f} [ISOLATED - SS ONLY]")
        
        if "medicare_tax_withheld" in doc and doc["medicare_tax_withheld"] > 0:
            totals["medicare_tax_withheld"] += doc["medicare_tax_withheld"]
            print(f"[DEBUG]   Medicare Withheld: ${doc['medicare_tax_withheld']:,.2f} [ISOLATED - MEDICARE ONLY]")

    # Calculate total income - CLEARLY SEPARATED by source
    print(f"\n[DEBUG] INCOME AGGREGATION (Strict Separation):")
    print(f"[DEBUG]   W-2 WAGES: ${totals['wages']:,.2f}")
    print(f"[DEBUG]   1099-NEC (Self-Employment): ${totals['nonemployee_compensation']:,.2f}")
    
    # 1099-MISC Box 5 (Fishing Boat Proceeds) is SELF-EMPLOYMENT INCOME
    # Must be separated from other 1099-MISC boxes
    fishing_se_income = totals['fishing_boat_proceeds']
    
    # 1099-MISC includes ORDINARY INCOME boxes (excludes Box 5 fishing, Box 6 medical, Box 7 direct sales)
    misc_total = (totals['rents'] + totals['royalties'] + totals['other_income'] + 
                  totals['substitute_payments'] + 
                  totals['crop_insurance_proceeds'] + totals['gross_proceeds_attorney'] + 
                  totals['excess_parachute_payments'] + totals['nonqualified_deferred_comp'])
    print(f"[DEBUG]   1099-MISC (8 ordinary income boxes): ${misc_total:,.2f}")
    print(f"[DEBUG]   1099-MISC Box 5 (Fishing - SE income): ${fishing_se_income:,.2f}")
    
    # 1099-INT includes all interest variations
    int_total = (totals['interest_income'] + totals['us_savings_bonds'] + totals['federal_interest_subsidy'])
    print(f"[DEBUG]   1099-INT (Interest + Bonds + Subsidy): ${int_total:,.2f}")
    
    # 1099-DIV includes all dividend types and capital gains
    div_total = (totals['ordinary_dividends'] + totals['qualified_dividends'] + 
                 totals['capital_gain_distributions'] + totals['long_term_capital_gains'] +
                 totals['unrecaptured_section_1250'] + totals['section_1202_gains'] + 
                 totals['collectibles_gains'] + totals['nondividend_distributions'] -
                 totals['investment_expenses'] + totals['foreign_tax_paid'])
    print(f"[DEBUG]   1099-DIV (Dividends + Capital Gains + Distributions): ${div_total:,.2f}")
    
    # 1099-B includes brokerage proceeds and gains
    b_total = (totals['total_proceeds'] - totals['cost_basis'] + 
               totals['short_term_gains'] + totals['long_term_gains'])
    print(f"[DEBUG]   1099-B (Brokerage Proceeds - Basis + Gains): ${b_total:,.2f}")
    
    # 1099-K payment card income
    k_total = totals['card_not_present_transactions']
    print(f"[DEBUG]   1099-K (Payment Card Transactions): ${k_total:,.2f}")
    
    # 1099-OID original issue discount income
    oid_total = (totals['original_issue_discount'] + totals['oid_from_call_redemption'] + 
                 totals['early_redemption'] + totals['oid_accrued_this_year'])
    print(f"[DEBUG]   1099-OID (Original + Call + Early + Accrued): ${oid_total:,.2f}")
    
    # Other capital gains (separate from 1099-B/DIV)
    print(f"[DEBUG]   Capital Gains (Other): ${totals['capital_gains']:,.2f}")
    
    # Aggregate all 1099-MISC items (IRS standard treatment - includes taxable boxes EXCEPT Box 5)
    # Box 5 (Fishing Boat Proceeds) is SELF-EMPLOYMENT INCOME, not ordinary income
    # EXCLUDES Box 5 (fishing_boat_proceeds) - SELF-EMPLOYMENT INCOME
    # EXCLUDES Box 6 (medical_payments) - NOT taxable to recipient
    # EXCLUDES Box 7 (direct_sales) - informational only
    # EXCLUDES Box 11 (fish purchased for resale) - reimbursement, not income
    misc_income = (totals["rents"] +                    # Box 1
                   totals["royalties"] +                # Box 2
                   totals["other_income"] +             # Box 3
                   totals["substitute_payments"] +      # Box 8
                   totals["crop_insurance_proceeds"] +  # Box 9
                   totals["gross_proceeds_attorney"] +  # Box 10
                   totals["excess_parachute_payments"] +# Box 14
                   totals["nonqualified_deferred_comp"]) # Box 15
    
    # Self-employment income includes:
    # - 1099-NEC nonemployee compensation
    # - 1099-MISC Box 5 (Fishing Boat Proceeds)
    se_income_total = totals["nonemployee_compensation"] + fishing_se_income
    
    # Aggregate 1099-INT interest income (all interest variations)
    interest_income = (totals["interest_income"] + 
                       totals["us_savings_bonds"] + 
                       totals["federal_interest_subsidy"])
    
    # Aggregate 1099-DIV dividend income (all dividend types and capital gains)
    dividend_income = (totals["ordinary_dividends"] + 
                       totals["qualified_dividends"] + 
                       totals["capital_gain_distributions"] + 
                       totals["long_term_capital_gains"] +
                       totals["unrecaptured_section_1250"] + 
                       totals["section_1202_gains"] + 
                       totals["collectibles_gains"] + 
                       totals["nondividend_distributions"] -
                       totals["investment_expenses"] + 
                       totals["foreign_tax_paid"])
    totals["dividend_income"] = dividend_income
    
    # Aggregate 1099-B brokerage income (proceeds - cost basis + gains)
    brokerage_income = (totals["total_proceeds"] - 
                        totals["cost_basis"] + 
                        totals["short_term_gains"] + 
                        totals["long_term_gains"])
    
    # Aggregate 1099-OID original issue discount income
    oid_income = (totals["original_issue_discount"] + 
                  totals["oid_from_call_redemption"] + 
                  totals["early_redemption"] + 
                  totals["oid_accrued_this_year"])
    
    # Calculate total income from all sources
    totals["total_income"] = (
        totals["wages"] +                              # W-2
        se_income_total +                             # 1099-NEC + 1099-MISC Box 5 (SE income)
        misc_income +                                  # 1099-MISC (8 ordinary boxes, NOT Box 5)
        interest_income +                              # 1099-INT (all variations)
        dividend_income +                              # 1099-DIV (all types)
        brokerage_income +                             # 1099-B (proceeds - basis + gains)
        totals["card_not_present_transactions"] +     # 1099-K
        oid_income +                                   # 1099-OID (all types)
        totals["capital_gains"]                        # Other capital gains
    )
    print(f"[DEBUG]   TOTAL INCOME (sum of above): ${totals['total_income']:,.2f}")

    # Calculate total withholdings - CLEARLY SEPARATED by type
    print(f"\n[DEBUG] WITHHOLDING AGGREGATION (Strict Separation):")
    print(f"[DEBUG]   Federal Income Tax: ${totals['federal_income_tax_withheld']:,.2f}")
    print(f"[DEBUG]   Social Security Tax: ${totals['social_security_tax_withheld']:,.2f}")
    print(f"[DEBUG]   Medicare Tax: ${totals['medicare_tax_withheld']:,.2f}")
    
    totals["total_withheld"] = (
        totals["federal_income_tax_withheld"]
        + totals["social_security_tax_withheld"]
        + totals["medicare_tax_withheld"]
    )
    print(f"[DEBUG]   TOTAL WITHHELD (sum of above): ${totals['total_withheld']:,.2f}\n")

    return totals


# -----------------------
# MODULE C: IRS 2024 TAX ENGINE
# -----------------------

# IRS STANDARD DEDUCTION (2024)
STANDARD_DEDUCTION_2024 = {
    "single": 14600,
    "married_filing_jointly": 29200,
    "married_filing_separately": 14600,
    "head_of_household": 21900,
    "qualifying_widow": 29200,
}

# IRS TAX BRACKETS (2024) - Single Filer
# Format: (upper_limit, rate, base_tax_at_floor)
# Base tax = accumulated tax from all lower brackets
IRS_BRACKETS_2024_SINGLE = [
    (11600, 0.10, 0),           # $0 to $11,600: 10% (base = $0)
    (47150, 0.12, 1160),        # $11,600 to $47,150: 12% (base = $1,160)
    (100525, 0.22, 5426),       # $47,150 to $100,525: 22% (base = $5,426)
    (191950, 0.24, 17168.50),   # $100,525 to $191,950: 24% (base = $17,168.50)
    (243725, 0.32, 39110.50),   # $191,950 to $243,725: 32% (base = $39,110.50)
    (609350, 0.35, 55678.50),   # $243,725 to $609,350: 35% (base = $55,678.50)
    (float("inf"), 0.37, 183647.25),  # $609,350+: 37% (base = $183,647.25)
]

# IRS TAX BRACKETS (2024) - Married Filing Jointly
# Format: (upper_limit, rate, base_tax_at_floor)
IRS_BRACKETS_2024_MFJ = [
    (23200, 0.10, 0),           # $0 to $23,200: 10% (base = $0)
    (94300, 0.12, 2320),        # $23,200 to $94,300: 12% (base = $2,320)
    (201050, 0.22, 10852),      # $94,300 to $201,050: 22% (base = $10,852)
    (383900, 0.24, 34337),      # $201,050 to $383,900: 24% (base = $34,337)
    (487450, 0.32, 78221),      # $383,900 to $487,450: 32% (base = $78,221)
    (731200, 0.35, 111357),     # $487,450 to $731,200: 35% (base = $111,357)
    (float("inf"), 0.37, 196669.50),  # $731,200+: 37% (base = $196,669.50)
]

# IRS TAX BRACKETS (2024) - Head of Household
# Format: (upper_limit, rate, base_tax_at_floor)
IRS_BRACKETS_2024_HOH = [
    (16550, 0.10, 0),           # $0 to $16,550: 10% (base = $0)
    (63100, 0.12, 1655),        # $16,550 to $63,100: 12% (base = $1,655)
    (100500, 0.22, 7231),       # $63,100 to $100,500: 22% (base = $7,231)
    (191950, 0.24, 17809),      # $100,500 to $191,950: 24% (base = $17,809)
    (243700, 0.32, 39689),      # $191,950 to $243,700: 32% (base = $39,689)
    (609350, 0.35, 57139),      # $243,700 to $609,350: 35% (base = $57,139)
    (float("inf"), 0.37, 183711.50),  # $609,350+: 37% (base = $183,711.50)
]

def get_tax_brackets(filing_status: str) -> List[tuple]:
    """Get appropriate tax brackets based on filing status"""
    if filing_status.lower() == "married_filing_jointly":
        return IRS_BRACKETS_2024_MFJ
    elif filing_status.lower() == "head_of_household":
        return IRS_BRACKETS_2024_HOH
    else:
        return IRS_BRACKETS_2024_SINGLE


def compute_federal_tax_2024(taxable_income: float, filing_status: str = "single", income_source: str = "W-2") -> float:
    """
    Compute federal income tax using 2024 IRS tax brackets.
    Uses CORRECT bracket algorithm: base_tax + (income - bracket_floor) * rate
    
    Args:
        taxable_income: Income after deductions (from ONE source - no mixing)
        filing_status: single, married_filing_jointly, head_of_household
        income_source: "W-2", "1099-NEC", "Mixed" - for audit trail
    
    STRICT: This function takes taxable income and applies ONLY federal tax calculation.
    No mixing with self-employment tax, interest calculations, or other sources.
    
    CORRECT ALGORITHM:
    For each bracket: tax = bracket_base + (income_in_bracket) * bracket_rate
    where bracket_base = accumulated tax from all lower brackets
    """
    if taxable_income <= 0:
        return 0.0

    brackets = get_tax_brackets(filing_status)
    tax = 0.0
    prev_limit = 0.0

    print(f"\n[DEBUG] Computing FEDERAL tax for ${taxable_income:,.2f} ({filing_status})")
    print(f"[DEBUG] Income Source: {income_source} (ISOLATED - no mixing)")

    for limit, rate, base_tax in brackets:
        if taxable_income > limit:
            # Full bracket is used
            tax_in_bracket = (limit - prev_limit) * rate
            tax += tax_in_bracket
            print(f"[DEBUG]   ${prev_limit:,.0f} - ${limit:,.0f} @ {rate*100}%: ${tax_in_bracket:,.2f}")
            prev_limit = limit
        else:
            # This is the final bracket
            tax_in_bracket = (taxable_income - prev_limit) * rate
            tax += tax_in_bracket
            print(f"[DEBUG]   ${prev_limit:,.0f} - ${taxable_income:,.0f} @ {rate*100}%: ${tax_in_bracket:,.2f}")
            break

    federal_tax = round(tax, 2)
    print(f"[DEBUG] FEDERAL INCOME TAX (from {income_source}): ${federal_tax:,.2f}\n")
    return federal_tax


def compute_self_employment_tax(se_income: float) -> float:
    """
    Compute self-employment tax on combined self-employment income.
    SE tax = 92.35% of SE income × 15.3% (Social Security 12.4% + Medicare 2.9%)
    
    SE Income includes:
    - 1099-NEC income (nonemployee compensation)
    - 1099-MISC Box 5 (fishing boat proceeds - treated as SE income per IRS)
    
    STRICT ISOLATION:
    - This ONLY applies to self-employment income (NEC + fishing)
    - NEVER applies to W-2 wages
    - NEVER mixes with federal income tax calculation
    - Separate calculation path from W-2 taxes
    """
    if se_income <= 0:
        return 0.0

    # 92.35% is the portion subject to SE tax (after deduction)
    se_tax_base = se_income * 0.9235
    se_tax = se_tax_base * 0.153

    se_tax = round(se_tax, 2)
    print(f"\n[DEBUG] SELF-EMPLOYMENT TAX Calculation (Combined SE Income):")
    print(f"[DEBUG]   SE Income (NEC + Fishing): ${se_income:,.2f} [SOURCE: 1099-NEC + 1099-MISC Box 5]")
    print(f"[DEBUG]   SE Tax Base (92.35%): ${se_tax_base:,.2f}")
    print(f"[DEBUG]   SE Tax (15.3%): ${se_tax:,.2f}")
    print(f"[DEBUG]   NOTE: Applied to 1099-NEC and 1099-MISC Box 5, NOT to W-2 wages\n")

    return se_tax


def compute_estimated_tax_credits(
    filing_status: str,
    num_dependents: int = 0,
    education_credits: float = 0.0,
    child_tax_credit: float = 0.0,
    earned_income_credit: float = 0.0,
    other_credits: float = 0.0,
) -> Dict[str, float]:
    """
    Calculate available tax credits.
    Returns breakdown of all applicable credits.
    """
    print(f"\n[DEBUG] Computing Tax Credits:")
    print(f"[DEBUG]   Filing Status: {filing_status}")
    print(f"[DEBUG]   Dependents: {num_dependents}")

    # Child Tax Credit: $2,000 per dependent
    calculated_ctc = num_dependents * 2000
    # But user might have entered custom amount
    ctc = max(child_tax_credit, calculated_ctc) if child_tax_credit > 0 else calculated_ctc

    credits = {
        "education_credits": round(education_credits, 2),
        "child_tax_credit": round(ctc, 2),
        "earned_income_credit": round(earned_income_credit, 2),
        "other_credits": round(other_credits, 2),
    }

    total_credits = sum(credits.values())

    for credit_type, amount in credits.items():
        if amount > 0:
            print(f"[DEBUG]   {credit_type}: ${amount:,.2f}")

    print(f"[DEBUG] Total Credits: ${total_credits:,.2f}\n")

    credits["total_credits"] = round(total_credits, 2)
    return credits


# -----------------------
# MODULE D: END-TO-END TAX CALCULATION
# -----------------------

def calculate_tax(
    docs: List[Dict[str, float]],
    filing_status: str = "single",
    num_dependents: int = 0,
    education_credits: float = 0.0,
    child_tax_credit: float = 0.0,
    earned_income_credit: float = 0.0,
    other_credits: float = 0.0,
    deduction_type: str = "standard",
    itemized_amount: float = 0.0,
) -> Dict[str, Any]:
    """
    MAIN TAX CALCULATION ENGINE
    
    Given multiple normalized documents and personal details,
    returns complete tax summary including refund or amount due.
    
    Args:
        docs: List of normalized income dictionaries
        filing_status: single, married_filing_jointly, head_of_household, etc.
        num_dependents: Number of dependents
        education_credits: Education-related credits
        child_tax_credit: Child tax credits
        earned_income_credit: EITC amount
        other_credits: Other miscellaneous credits
        deduction_type: "standard" or "itemized"
        itemized_amount: Amount if using itemized deductions
    
    Returns:
        Complete tax calculation dictionary
    """
    print("\n" + "="*80)
    print("TAX CALCULATION ENGINE - 2024 IRS")
    print("="*80)

    # Step 1: Aggregate income (with strict field isolation)
    print("\n[STEP 1] AGGREGATE DOCUMENTS - STRICT FIELD ISOLATION")
    totals = aggregate_documents(docs)

    # Extract each field type - KEEP SEPARATE, DON'T MIX
    wages = totals["wages"]  # From W-2, Box 1 ONLY
    nec_income = totals["nonemployee_compensation"]  # From 1099-NEC ONLY
    fishing_se_income = totals.get("fishing_boat_proceeds", 0.0)  # From 1099-MISC Box 5 - SE income
    se_income = nec_income + fishing_se_income  # Total self-employment income
    interest = totals["interest_income"]  # From 1099-INT ONLY
    dividends = totals["dividend_income"]  # From 1099-DIV ONLY
    capital_gains = totals.get("capital_gains", 0.0)  # From 1099-B ONLY
    
    # Withholdings - ISOLATED by type
    fed_withheld = totals["federal_income_tax_withheld"]  # Federal only
    ss_withheld = totals["social_security_tax_withheld"]  # Social Security only
    medicare_withheld = totals["medicare_tax_withheld"]  # Medicare only
    withheld = totals["total_withheld"]
    
    gross_income = totals["total_income"]  # Sum of all income sources

    print(f"\n[STEP 1] Field Isolation Verification:")
    print(f"[ISOLATION] W-2 Wages (Box 1): ${wages:,.2f} ← W-2 ONLY")
    print(f"[ISOLATION] 1099-NEC Income: ${nec_income:,.2f} ← NEC ONLY")
    print(f"[ISOLATION] 1099-MISC Box 5 (Fishing SE): ${fishing_se_income:,.2f} ← MISC BOX 5 (SE)")
    print(f"[ISOLATION] Total SE Income: ${se_income:,.2f} ← NEC + MISC Box 5")
    print(f"[ISOLATION] 1099-INT Interest: ${interest:,.2f} ← INTEREST ONLY")
    print(f"[ISOLATION] 1099-DIV Dividends: ${dividends:,.2f} ← DIVIDENDS ONLY")
    print(f"[ISOLATION] Fed Withheld: ${fed_withheld:,.2f} ← FEDERAL ONLY")
    print(f"[ISOLATION] SS Withheld: ${ss_withheld:,.2f} ← SOCIAL SECURITY ONLY")
    print(f"[ISOLATION] Medicare Withheld: ${medicare_withheld:,.2f} ← MEDICARE ONLY")

    # Step 2: Apply deduction
    print("\n[STEP 2] APPLY DEDUCTION")
    if deduction_type.lower() == "itemized" and itemized_amount > 0:
        deduction = round(itemized_amount, 2)
        print(f"[DEBUG] Itemized Deduction: ${deduction:,.2f}")
    else:
        deduction = STANDARD_DEDUCTION_2024.get(filing_status.lower(), STANDARD_DEDUCTION_2024["single"])
        print(f"[DEBUG] Standard Deduction ({filing_status}): ${deduction:,.2f}")

    taxable_income = max(0, gross_income - deduction)
    print(f"[DEBUG] Taxable Income: ${taxable_income:,.2f}\n")

    # Step 3: Compute taxes - STRICT FIELD ISOLATION
    print("[STEP 3] COMPUTE TAXES - STRICT FIELD ISOLATION")
    print("[STEP 3A] Federal Income Tax (from aggregate income)")
    federal_tax = compute_federal_tax_2024(taxable_income, filing_status, income_source="W-2 + 1099 Income")
    
    print("[STEP 3B] Self-Employment Tax (from 1099-NEC + 1099-MISC Box 5 Fishing)")
    se_tax = compute_self_employment_tax(se_income)
    
    total_tax_before_credits = federal_tax + se_tax
    print(f"\n[DEBUG] TOTAL TAX (Federal + SE): ${total_tax_before_credits:,.2f}")
    print(f"[DEBUG]   Federal: ${federal_tax:,.2f}")
    print(f"[DEBUG]   Self-Employment: ${se_tax:,.2f}\n")

    # Step 4: Apply credits
    print("[STEP 4] APPLY CREDITS")
    credits = compute_estimated_tax_credits(
        filing_status,
        num_dependents,
        education_credits,
        child_tax_credit,
        earned_income_credit,
        other_credits,
    )

    total_tax_liability = max(0, total_tax_before_credits - credits["total_credits"])
    print(f"[DEBUG] Total Tax Liability (after credits): ${total_tax_liability:,.2f}\n")

    # Step 5: Calculate refund or amount due
    print("[STEP 5] REFUND OR AMOUNT DUE")
    refund_or_due = round(fed_withheld - total_tax_liability, 2)
    result_status = "Refund [OK]" if refund_or_due > 0 else "Tax Due" if refund_or_due < 0 else "Zero"

    print(f"[DEBUG] Federal Tax Withheld: ${fed_withheld:,.2f}")
    print(f"[DEBUG] Total Tax Liability: ${total_tax_liability:,.2f}")
    print(f"[DEBUG] Result: {result_status} (${abs(refund_or_due):,.2f})\n")

    # Build final result
    final_result = {
        "status": "success",
        "tax_year": 2024,
        "filing_status": filing_status,
        "num_dependents": num_dependents,
        
        # Income Summary
        "income": {
            "wages": round(wages, 2),
            "nonemployee_compensation": round(nec_income, 2),
            "interest_income": round(interest, 2),
            "dividend_income": round(dividends, 2),
            "total_income": round(gross_income, 2),
        },
        
        # Deduction
        "deduction": {
            "type": deduction_type,
            "amount": round(deduction, 2),
        },
        
        # Taxable Income
        "taxable_income": round(taxable_income, 2),
        
        # Tax Calculation
        "taxes": {
            "federal_income_tax": round(federal_tax, 2),
            "self_employment_tax": round(se_tax, 2),
            "total_tax_before_credits": round(total_tax_before_credits, 2),
        },
        
        # Credits
        "credits": credits,
        
        # Tax Liability
        "total_tax_liability": round(total_tax_liability, 2),
        
        # Withholding & Result
        "withholding": {
            "federal_withheld": round(fed_withheld, 2),
            "ss_withheld": round(totals["social_security_tax_withheld"], 2),
            "medicare_withheld": round(totals["medicare_tax_withheld"], 2),
            "total_withheld": round(withheld, 2),
        },
        
        # Final Result
        "refund_or_due": refund_or_due,
        "result_type": "Refund" if refund_or_due > 0 else "Tax Due" if refund_or_due < 0 else "Zero",
        "result_amount": abs(refund_or_due),
        "result_status": result_status,
    }

    print("="*80)
    print("TAX CALCULATION COMPLETE")
    print("="*80 + "\n")

    return final_result


def calculate_tax_from_parsed_forms(
    parsed_forms: List[Dict],
    tax_details: Dict,
) -> Dict[str, Any]:
    """
    High-level function that takes parsed LandingAI forms + tax details
    and returns complete tax calculation.
    
    Args:
        parsed_forms: List of {"extracted_fields": {...}} from LandingAI parse
        tax_details: {"filing_status": ..., "num_dependents": ..., etc.}
    
    Returns:
        Complete tax calculation result
    """
    print("\n[DEBUG] Converting parsed forms to normalized data...\n")
    
    # Normalize each parsed form
    normalized_docs = []
    for form in parsed_forms:
        extracted_fields = form.get("extracted_fields", {})
        normalized = normalize_extracted_data(extracted_fields)
        normalized_docs.append(normalized)
    
    # Extract tax details
    filing_status = tax_details.get("filing_status", "single")
    num_dependents = tax_details.get("num_dependents", 0)
    education_credits = tax_details.get("education_credits", 0.0)
    child_tax_credit = tax_details.get("child_tax_credit", 0.0)
    earned_income_credit = tax_details.get("earned_income_credit", 0.0)
    other_credits = tax_details.get("other_credits", 0.0)
    deduction_type = tax_details.get("deduction_type", "standard")
    itemized_amount = tax_details.get("itemized_amount", 0.0)
    
    # Calculate tax
    result = calculate_tax(
        normalized_docs,
        filing_status=filing_status,
        num_dependents=num_dependents,
        education_credits=education_credits,
        child_tax_credit=child_tax_credit,
        earned_income_credit=earned_income_credit,
        other_credits=other_credits,
        deduction_type=deduction_type,
        itemized_amount=itemized_amount,
    )
    
    return result

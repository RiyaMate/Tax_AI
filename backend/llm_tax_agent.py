"""
TAX-GPT: LLM-based Tax Extraction + Calculation Agent
Processes LandingAI ADE structured output → Universal Schema → Tax Calculation

Uses: Google Gemini LLM (same as IRS Chatbot)
"""

import json
import re
import os
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# LLM imports - Gemini REQUIRED
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# Optional: Claude and OpenAI (deprecated - Gemini is primary)
try:
    from anthropic import Anthropic
    HAS_CLAUDE = True
except ImportError:
    HAS_CLAUDE = False

try:
    from openai import OpenAI as OpenAIClient
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

logger = logging.getLogger(__name__)

# ============================================================================
# UNIVERSAL TAX SCHEMA
# ============================================================================

@dataclass
class UniversalTaxSchema:
    """Universal tax schema compatible with all 1099 forms + W-2"""
    
    # Tax metadata
    tax_year: int = 2024
    filing_status: str = "single"
    num_dependents: int = 0
    
    # Income fields (isolated by type)
    income_wages: float = 0.0
    income_nonemployee_compensation: float = 0.0
    income_other_income: float = 0.0
    income_rents: float = 0.0
    income_royalties: float = 0.0
    income_fishing_boat_proceeds: float = 0.0  # 1099-MISC Box 5
    income_interest_income: float = 0.0
    income_dividend_income: float = 0.0
    income_capital_gains: float = 0.0
    income_misc: float = 0.0
    income_total_income: float = 0.0
    
    # Withholding fields (isolated by type)
    withholding_federal_withheld: float = 0.0
    withholding_ss_withheld: float = 0.0
    withholding_medicare_withheld: float = 0.0
    withholding_total_withheld: float = 0.0
    
    # Deductions
    deduction_type: str = "standard deduction"
    deduction_amount: float = 14600
    
    # Calculated tax fields
    taxable_income: float = 0.0
    taxes_federal_income_tax: float = 0.0
    taxes_self_employment_tax: float = 0.0
    taxes_total_tax_before_credits: float = 0.0
    
    # Credits
    credits_total_credits: float = 0.0
    
    # Final results
    total_tax_liability: float = 0.0
    refund_or_due: float = 0.0
    result_type: str = ""
    result_amount: float = 0.0
    result_status: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# DOCUMENT TYPE DETECTION
# ============================================================================

class DocumentType(Enum):
    """Supported tax document types"""
    W2 = "W-2"
    FORM_1099_NEC = "1099-NEC"
    FORM_1099_MISC = "1099-MISC"
    FORM_1099_INT = "1099-INT"
    FORM_1099_DIV = "1099-DIV"
    FORM_1099_K = "1099-K"
    FORM_1099_B = "1099-B"
    FORM_1099_OID = "1099-OID"
    UNKNOWN = "UNKNOWN"


def detect_document_type(landingai_output: Dict[str, Any]) -> DocumentType:
    """
    Detect document type from LandingAI ADE output.
    
    Checks: text content, extracted fields, document title/headers
    """
    
    # Extract all text from LandingAI output
    all_text = ""
    
    if isinstance(landingai_output.get("markdown"), str):
        all_text += landingai_output["markdown"].upper()
    
    if isinstance(landingai_output.get("extracted_values"), list):
        for item in landingai_output["extracted_values"]:
            if isinstance(item.get("text"), str):
                all_text += " " + item["text"].upper()
    
    if isinstance(landingai_output.get("key_value_pairs"), dict):
        all_text += " " + " ".join(landingai_output["key_value_pairs"].keys()).upper()
    
    print(f"[DEBUG] Document detection text length: {len(all_text)}")
    print(f"[DEBUG] First 500 chars: {all_text[:500]}")
    
    # Pattern matching - improved with more flexible patterns
    patterns = {
        DocumentType.W2: [
            r"FORM\s*W-?2\b",
            r"WAGES.*TIPS.*WITHHOLD",
            r"BOX\s*1.*WAGES",
            r"W\s*2\s*FORM",
            r"FEDERAL.*WITHHOLDING",
        ],
        DocumentType.FORM_1099_NEC: [
            r"FORM\s*1099-NEC",
            r"1099\s*NEC",
            r"NONEMPLOYEE\s*COMPENSATION",
            r"1099.*NEC",
        ],
        DocumentType.FORM_1099_MISC: [
            r"FORM\s*1099-MISC",
            r"1099\s*MISC",
            r"RENTS.*ROYALTIES",
            r"MISCELLANEOUS\s*INCOME",
            r"1099.*MISC",
        ],
        DocumentType.FORM_1099_INT: [
            r"FORM\s*1099-INT",
            r"1099\s*INT",
            r"INTEREST\s*INCOME",
            r"1099.*INT",
        ],
        DocumentType.FORM_1099_DIV: [
            r"FORM\s*1099-DIV",
            r"1099\s*DIV",
            r"DIVIDENDS.*CAPITAL\s*GAIN",
            r"DIVIDEND\s*INCOME",
            r"1099.*DIV",
        ],
        DocumentType.FORM_1099_K: [
            r"FORM\s*1099-K",
            r"1099\s*K",
            r"PAYMENT\s*CARD",
            r"1099.*K",
        ],
    }
    
    for doc_type, patterns_list in patterns.items():
        for pattern in patterns_list:
            if re.search(pattern, all_text):
                logger.info(f"Detected document type: {doc_type.value}")
                print(f"[INFO] Detected document type: {doc_type.value} (pattern: {pattern})")
                return doc_type
    
    # If no patterns match but we have income data, infer from context
    # Check if markdown contains typical tax form structures
    if "box" in all_text.lower() or "amount" in all_text.lower():
        # Has box structure - likely a tax form
        if "federal" in all_text.lower() or "wages" in all_text.lower():
            logger.info("Inferring W-2 from text structure")
            print("[INFO] Inferring W-2 from text structure")
            return DocumentType.W2
        elif "nonemployee" in all_text.lower() or "nec" in all_text.lower():
            logger.info("Inferring 1099-NEC from text structure")
            print("[INFO] Inferring 1099-NEC from text structure")
            return DocumentType.FORM_1099_NEC
    
    logger.warning("Could not detect document type, returning UNKNOWN")
    print(f"[WARNING] Could not detect document type, returning UNKNOWN")
    return DocumentType.UNKNOWN


# ============================================================================
# W-2 MAPPING
# ============================================================================

def map_w2(landingai_output: Dict[str, Any]) -> Dict[str, float]:
    """Map W-2 form boxes to universal schema"""
    
    mapping = {
        "income_wages": None,  # Box 1
        "withholding_federal_withheld": None,  # Box 2
        "withholding_ss_withheld": None,  # Box 4
        "withholding_medicare_withheld": None,  # Box 6
    }
    
    box_mapping = {
        "Box 1": "income_wages",
        "Box 2": "withholding_federal_withheld",
        "Box 4": "withholding_ss_withheld",
        "Box 6": "withholding_medicare_withheld",
    }
    
    # Try key_value_pairs first
    if isinstance(landingai_output.get("key_value_pairs"), dict):
        for box_label, field_name in box_mapping.items():
            for key in landingai_output["key_value_pairs"].keys():
                if box_label in key:
                    value = extract_numeric_value(
                        landingai_output["key_value_pairs"][key]
                    )
                    if value is not None:
                        mapping[field_name] = value
    
    # Try extracted_values
    if isinstance(landingai_output.get("extracted_values"), list):
        for item in landingai_output["extracted_values"]:
            if isinstance(item.get("text"), str):
                text = item["text"]
                for box_label, field_name in box_mapping.items():
                    if box_label in text:
                        value = extract_numeric_value(text)
                        if value is not None:
                            mapping[field_name] = value
    
    # If still empty, try to parse from markdown (LandingAI puts data there)
    if all(v is None for v in mapping.values()) and landingai_output.get("markdown"):
        markdown = landingai_output["markdown"]
        
        # Look for W-2 Box patterns in markdown (handles HTML table format from LandingAI)
        # Patterns for HTML table: <td>1</td><td>Wages, tips...</td><td>$23,500.00</td>
        # OR single cell: <td>1 Wages, tips... 23500.00</td>
        patterns = {
            # Primary: Look for amount in cells after box number and label
            "income_wages": [
                r"(?:<td[^>]*>)?1(?:</td>\s*<td[^>]*>)?\s*Wages[,\s]+tips[,\s]+other[^<]*?comp(?:ensation)?(?:</td>\s*<td[^>]*>)?\s*[\$]?([\d,\.]+)",
                r"(?:<td[^>]*>)?1(?:</td>)?[^<]*?Wages[,\s]+tips[,\s]+other[^<]*?comp(?:ensation)?[^<]*?([\d,\.]+)",
                r"Wages[,\s]+tips[,\s]+other\s+comp(?:ensation)?[^\d]*([\d,\.]+)",  # Flexible match
                r"<tr[^>]*>.*?<td[^>]*>1</td>.*?<td[^>]*>[\$]?([\d,\.]+)</td>.*?</tr>",  # First amount in row
            ],
            "withholding_federal_withheld": [
                r"(?:<td[^>]*>)?2(?:</td>\s*<td[^>]*>)?\s*Federal\s+income\s+tax[^\d]*([\d,\.]+)",
                r"Federal\s+income\s+tax\s+withh?(?:old(?:ing)?)?[^\d]*([\d,\.]+)",
                r"<tr[^>]*>.*?<td[^>]*>2</td>.*?<td[^>]*>[\$]?([\d,\.]+)</td>.*?</tr>",
            ],
            "withholding_ss_withheld": [
                r"(?:<td[^>]*>)?4(?:</td>\s*<td[^>]*>)?\s*Social\s+security\s+tax[^\d]*([\d,\.]+)",
                r"Social\s+security\s+tax\s+withh?(?:old(?:ing)?)?[^\d]*([\d,\.]+)",
                r"<tr[^>]*>.*?<td[^>]*>4</td>.*?<td[^>]*>[\$]?([\d,\.]+)</td>.*?</tr>",
            ],
            "withholding_medicare_withheld": [
                r"(?:<td[^>]*>)?6(?:</td>\s*<td[^>]*>)?\s*Medicare\s+tax[^\d]*([\d,\.]+)",
                r"Medicare\s+tax\s+withh?(?:old(?:ing)?)?[^\d]*([\d,\.]+)",
                r"<tr[^>]*>.*?<td[^>]*>6</td>.*?<td[^>]*>[\$]?([\d,\.]+)</td>.*?</tr>",
            ],
        }
        
        for field_name, pattern_list in patterns.items():
            if isinstance(pattern_list, list):
                for pattern in pattern_list:
                    match = re.search(pattern, markdown, re.IGNORECASE | re.DOTALL)
                    if match:
                        value = extract_numeric_value(match.group(1))
                        if value is not None:
                            mapping[field_name] = value
                            break  # Use first successful match
    
    # Clean up None values
    return {k: (v or 0.0) for k, v in mapping.items()}


# ============================================================================
# 1099-NEC MAPPING
# ============================================================================

def map_1099_nec(landingai_output: Dict[str, Any]) -> Dict[str, float]:
    """Map 1099-NEC form to universal schema"""
    
    mapping = {
        "income_nonemployee_compensation": None,  # Box 1
        "withholding_federal_withheld": None,  # Box 4
    }
    
    box_mapping = {
        "Box 1": "income_nonemployee_compensation",
        "Box 4": "withholding_federal_withheld",
    }
    
    # Key-value pairs
    if isinstance(landingai_output.get("key_value_pairs"), dict):
        for box_label, field_name in box_mapping.items():
            for key in landingai_output["key_value_pairs"].keys():
                if box_label in key:
                    value = extract_numeric_value(
                        landingai_output["key_value_pairs"][key]
                    )
                    if value is not None:
                        mapping[field_name] = value
    
    # Extracted values
    if isinstance(landingai_output.get("extracted_values"), list):
        for item in landingai_output["extracted_values"]:
            if isinstance(item.get("text"), str):
                text = item["text"]
                for box_label, field_name in box_mapping.items():
                    if box_label in text:
                        value = extract_numeric_value(text)
                        if value is not None:
                            mapping[field_name] = value
    
    # If still empty, try to parse from markdown
    if all(v is None for v in mapping.values()) and landingai_output.get("markdown"):
        markdown = landingai_output["markdown"]
        
        # Look for 1099-NEC Box patterns (HTML table format)
        # Format: "1 Nonemployee compensation $ 5000" or "Nonemployee compensation $5000.00"
        patterns = {
            "income_nonemployee_compensation": r"1\s+Nonemployee\s+compensation\s*\$?\s*([\d,\.]+)",
            "withholding_federal_withheld": r"4\s+Federal\s+income\s+tax\s+withheld\s*\$?\s*([\d,\.]*)",
        }
        
        for field_name, pattern in patterns.items():
            match = re.search(pattern, markdown, re.IGNORECASE)
            if match:
                value_str = match.group(1).strip()
                if value_str:  # Only extract if there's a non-empty match
                    value = extract_numeric_value(value_str)
                    if value is not None:
                        mapping[field_name] = value
    
    return {k: (v or 0.0) for k, v in mapping.items()}


# ============================================================================
# 1099-MISC MAPPING
# ============================================================================

def map_1099_misc(landingai_output: Dict[str, Any]) -> Dict[str, float]:
    """Map 1099-MISC form to universal schema"""
    
    mapping = {
        "income_rents": None,  # Box 1
        "income_royalties": None,  # Box 2
        "income_other_income": None,  # Box 3
        "withholding_federal_withheld": None,  # Box 4
        "income_fishing_boat_proceeds": None,  # Box 5
    }
    
    box_mapping = {
        "Box 1": "income_rents",
        "Box 2": "income_royalties",
        "Box 3": "income_other_income",
        "Box 4": "withholding_federal_withheld",
        "Box 5": "income_fishing_boat_proceeds",
    }
    
    # Key-value pairs
    if isinstance(landingai_output.get("key_value_pairs"), dict):
        for box_label, field_name in box_mapping.items():
            for key in landingai_output["key_value_pairs"].keys():
                if box_label in key:
                    value = extract_numeric_value(
                        landingai_output["key_value_pairs"][key]
                    )
                    if value is not None:
                        mapping[field_name] = value
    
    # Extracted values
    if isinstance(landingai_output.get("extracted_values"), list):
        for item in landingai_output["extracted_values"]:
            if isinstance(item.get("text"), str):
                text = item["text"]
                for box_label, field_name in box_mapping.items():
                    if box_label in text:
                        value = extract_numeric_value(text)
                        if value is not None:
                            mapping[field_name] = value
    
    return {k: (v or 0.0) for k, v in mapping.items()}


# ============================================================================
# 1099-INT MAPPING
# ============================================================================

def map_1099_int(landingai_output: Dict[str, Any]) -> Dict[str, float]:
    """Map 1099-INT form to universal schema"""
    
    mapping = {
        "income_interest_income": None,  # Box 1
        "withholding_federal_withheld": None,  # Box 4
    }
    
    box_mapping = {
        "Box 1": "income_interest_income",
        "Box 4": "withholding_federal_withheld",
    }
    
    if isinstance(landingai_output.get("key_value_pairs"), dict):
        for box_label, field_name in box_mapping.items():
            for key in landingai_output["key_value_pairs"].keys():
                if box_label in key:
                    value = extract_numeric_value(
                        landingai_output["key_value_pairs"][key]
                    )
                    if value is not None:
                        mapping[field_name] = value
    
    if isinstance(landingai_output.get("extracted_values"), list):
        for item in landingai_output["extracted_values"]:
            if isinstance(item.get("text"), str):
                text = item["text"]
                for box_label, field_name in box_mapping.items():
                    if box_label in text:
                        value = extract_numeric_value(text)
                        if value is not None:
                            mapping[field_name] = value
    
    return {k: (v or 0.0) for k, v in mapping.items()}


# ============================================================================
# 1099-DIV MAPPING
# ============================================================================

def map_1099_div(landingai_output: Dict[str, Any]) -> Dict[str, float]:
    """Map 1099-DIV form to universal schema"""
    
    mapping = {
        "income_dividend_income": None,  # Box 1a
        "income_capital_gains": None,  # Box 2a
        "withholding_federal_withheld": None,  # Box 4
    }
    
    box_mapping = {
        "Box 1a": "income_dividend_income",
        "Box 2a": "income_capital_gains",
        "Box 4": "withholding_federal_withheld",
    }
    
    if isinstance(landingai_output.get("key_value_pairs"), dict):
        for box_label, field_name in box_mapping.items():
            for key in landingai_output["key_value_pairs"].keys():
                if box_label in key:
                    value = extract_numeric_value(
                        landingai_output["key_value_pairs"][key]
                    )
                    if value is not None:
                        mapping[field_name] = value
    
    if isinstance(landingai_output.get("extracted_values"), list):
        for item in landingai_output["extracted_values"]:
            if isinstance(item.get("text"), str):
                text = item["text"]
                for box_label, field_name in box_mapping.items():
                    if box_label in text:
                        value = extract_numeric_value(text)
                        if value is not None:
                            mapping[field_name] = value
    
    # If still empty, try to parse from markdown (LandingAI puts data there in HTML table)
    if all(v is None for v in mapping.values()) and landingai_output.get("markdown"):
        markdown = landingai_output["markdown"]
        
        # Look for 1099-DIV Box patterns in HTML table format
        # Pattern: "1a Total ordinary dividends $ 1601.60"
        # Pattern: "2a Total capital gain distr.$ 271.79"
        # Pattern: "4 Federal income tax withheld $ 54.28"
        patterns = {
            "income_dividend_income": r"1a\s+Total\s+ordinary\s+dividends\s+\$?\s*([\d,\.]+)",
            "income_capital_gains": r"2a\s+Total\s+capital\s+gain\s+distr\.\s*\$?\s*([\d,\.]+)",
            "withholding_federal_withheld": r"4\s+Federal\s+income\s+tax\s+withheld\s+\$?\s*([\d,\.]+)",
        }
        
        for field_name, pattern in patterns.items():
            match = re.search(pattern, markdown, re.IGNORECASE)
            if match:
                value = extract_numeric_value(match.group(1))
                if value is not None:
                    mapping[field_name] = value
    
    return {k: (v or 0.0) for k, v in mapping.items()}


# ============================================================================
# NUMERIC VALUE EXTRACTION
# ============================================================================

def extract_numeric_value(text: Union[str, Any]) -> Optional[float]:
    """
    Extract numeric value from text.
    Handles:
    - Currency: $1,234.56
    - Parentheses for negatives: (123)
    - Spaces: 1 234 567
    - Multiple numbers: returns last (most relevant)
    """
    
    if not isinstance(text, str):
        text = str(text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Handle parentheses for negatives
    is_negative = "(" in text and ")" in text
    
    # Extract all numeric patterns
    pattern = r'-?\d+(?:[,\s]\d{3})*(?:\.\d{2})?|\(\d+(?:[,\s]\d{3})*(?:\.\d{2})?\)'
    matches = re.findall(pattern, text)
    
    if not matches:
        return None
    
    # Use last match (most likely to be the value)
    last_match = matches[-1]
    
    # Clean up
    last_match = last_match.replace("(", "").replace(")", "").replace(",", "").replace(" ", "")
    
    try:
        value = float(last_match)
        # Apply negative if found in parentheses
        if is_negative and value > 0:
            value = -value
        return value
    except ValueError:
        return None


# ============================================================================
# TAX CALCULATION ENGINE
# ============================================================================

def calculate_standard_deduction(filing_status: str) -> float:
    """2024 standard deduction by filing status"""
    deductions = {
        "single": 14600,
        "married_filing_jointly": 29200,
        "married_filing_separately": 14600,
        "head_of_household": 21900,
        "qualifying_widow": 29200,
    }
    return deductions.get(filing_status.lower(), 14600)


def calculate_federal_income_tax(taxable_income: float, filing_status: str) -> float:
    """Calculate federal income tax using 2024 brackets"""
    
    if taxable_income <= 0:
        return 0.0
    
    # 2024 tax brackets (single filer)
    brackets = [
        (11600, 0.10),
        (47150, 0.12),
        (100525, 0.22),
        (191950, 0.24),
        (243725, 0.32),
        (609350, 0.35),
        (float('inf'), 0.37),
    ]
    
    # Adjust brackets for filing status
    if filing_status.lower() in ["married_filing_jointly", "qualifying_widow"]:
        brackets = [
            (23200, 0.10),
            (94300, 0.12),
            (201050, 0.22),
            (383900, 0.24),
            (487450, 0.32),
            (731200, 0.35),
            (float('inf'), 0.37),
        ]
    elif filing_status.lower() == "head_of_household":
        brackets = [
            (16550, 0.10),
            (63100, 0.12),
            (100500, 0.22),
            (191950, 0.24),
            (243700, 0.32),
            (609350, 0.35),
            (float('inf'), 0.37),
        ]
    
    tax = 0.0
    previous_bracket = 0.0
    
    for bracket_limit, rate in brackets:
        if taxable_income > bracket_limit:
            tax += (bracket_limit - previous_bracket) * rate
            previous_bracket = bracket_limit
        else:
            tax += (taxable_income - previous_bracket) * rate
            break
    
    return round(tax, 2)


def calculate_self_employment_tax(
    nec_income: float,
    fishing_income: float = 0.0
) -> float:
    """
    Calculate self-employment tax on combined SE income.
    
    SE Income = NEC + Fishing boat proceeds (1099-MISC Box 5)
    SE Tax = (SE Income × 0.9235) × 0.153
    """
    
    se_income = nec_income + fishing_income
    
    if se_income <= 0:
        return 0.0
    
    se_tax_base = se_income * 0.9235
    se_tax = se_tax_base * 0.153
    
    return round(se_tax, 2)


def calculate_tax_liability(schema: UniversalTaxSchema) -> UniversalTaxSchema:
    """Calculate complete tax liability"""
    
    # 1. Calculate total income
    schema.income_total_income = (
        schema.income_wages +
        schema.income_nonemployee_compensation +
        schema.income_other_income +
        schema.income_rents +
        schema.income_royalties +
        schema.income_fishing_boat_proceeds +
        schema.income_interest_income +
        schema.income_dividend_income +
        schema.income_capital_gains +
        schema.income_misc
    )
    
    # 2. Calculate taxable income
    schema.deduction_amount = calculate_standard_deduction(schema.filing_status)
    schema.taxable_income = max(0, schema.income_total_income - schema.deduction_amount)
    
    # 3. Calculate federal income tax
    schema.taxes_federal_income_tax = calculate_federal_income_tax(
        schema.taxable_income,
        schema.filing_status
    )
    
    # 4. Calculate self-employment tax
    schema.taxes_self_employment_tax = calculate_self_employment_tax(
        schema.income_nonemployee_compensation,
        schema.income_fishing_boat_proceeds
    )
    
    # 5. Calculate total tax before credits
    schema.taxes_total_tax_before_credits = (
        schema.taxes_federal_income_tax +
        schema.taxes_self_employment_tax
    )
    
    # 6. Apply credits (simplified - add more as needed)
    schema.credits_total_credits = 0.0
    
    # 7. Calculate total tax liability
    schema.total_tax_liability = (
        schema.taxes_total_tax_before_credits -
        schema.credits_total_credits
    )
    
    # 8. Calculate refund or due
    # NOTE: Only federal withholding is refundable. Social Security and Medicare 
    # taxes are self-employment taxes and are NOT refundable for income tax purposes.
    schema.withholding_total_withheld = (
        schema.withholding_federal_withheld +
        schema.withholding_ss_withheld +
        schema.withholding_medicare_withheld
    )
    
    # Refund calculation uses only FEDERAL income tax withheld
    schema.refund_or_due = (
        schema.withholding_federal_withheld -
        schema.total_tax_liability
    )
    
    # 9. Determine result type and status
    if schema.refund_or_due > 0:
        schema.result_type = "Refund"
        schema.result_amount = round(schema.refund_or_due, 2)
        schema.result_status = f"Refund [OK]"
    elif schema.refund_or_due < 0:
        schema.result_type = "Amount Due"
        schema.result_amount = round(abs(schema.refund_or_due), 2)
        schema.result_status = f"Amount Due [OK]"
    else:
        schema.result_type = "Break Even"
        schema.result_amount = 0.0
        schema.result_status = "No refund or amount due"
    
    return schema


# ============================================================================
# MAIN LLM TAX AGENT
# ============================================================================

class LLMTaxAgent:
    """Main tax extraction and calculation agent"""
    
    def __init__(self):
        self.logger = logger
    
    def process_landingai_output(
        self,
        landingai_output: Dict[str, Any],
        filing_status: str = "single",
        num_dependents: int = 0,
    ) -> Dict[str, Any]:
        """
        Process LandingAI ADE output and return complete tax calculation.
        
        Args:
            landingai_output: Raw JSON from LandingAI
            filing_status: Filing status (single, married_filing_jointly, etc.)
            num_dependents: Number of dependents
        
        Returns:
            Complete tax calculation in UniversalTaxSchema format
        """
        
        try:
            # Step 1: Detect document type
            doc_type = detect_document_type(landingai_output)
            self.logger.info(f"Processing document type: {doc_type.value}")
            
            # Step 2: Initialize schema
            schema = UniversalTaxSchema(
                filing_status=filing_status,
                num_dependents=num_dependents,
            )
            
            # Step 3: Map document to schema
            mapping_functions = {
                DocumentType.W2: map_w2,
                DocumentType.FORM_1099_NEC: map_1099_nec,
                DocumentType.FORM_1099_MISC: map_1099_misc,
                DocumentType.FORM_1099_INT: map_1099_int,
                DocumentType.FORM_1099_DIV: map_1099_div,
            }
            
            if doc_type in mapping_functions:
                mapped_values = mapping_functions[doc_type](landingai_output)
                for key, value in mapped_values.items():
                    if hasattr(schema, key) and value is not None:
                        setattr(schema, key, value)
            elif doc_type == DocumentType.UNKNOWN:
                # Fallback: try to extract any numeric values as income
                print("[DEBUG] Using fallback extraction for UNKNOWN document type")
                all_text = ""
                if isinstance(landingai_output.get("markdown"), str):
                    all_text = landingai_output["markdown"]
                
                # Try to find any dollar amounts
                dollar_amounts = re.findall(r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', all_text)
                if dollar_amounts:
                    # Use largest amount as primary income
                    amounts = [float(x.replace(',', '')) for x in dollar_amounts]
                    amounts.sort(reverse=True)
                    if amounts:
                        # Assume it's some form of income
                        schema.income_nonemployee_compensation = amounts[0]
                        print(f"[DEBUG] Extracted fallback income: {amounts[0]}")
            
            # Step 4: Calculate tax liability
            schema = calculate_tax_liability(schema)
            
            # Step 5: Return as dictionary with status
            result = schema.to_dict()
            result["status"] = "success"
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error processing LandingAI output: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e),
            }
    
    def process_multiple_documents(
        self,
        documents: list,
        filing_status: str = "single",
        num_dependents: int = 0,
    ) -> Dict[str, Any]:
        """
        Process multiple documents and aggregate results.
        
        Args:
            documents: List of LandingAI outputs
            filing_status: Filing status
            num_dependents: Number of dependents
        
        Returns:
            Aggregated tax calculation
        """
        
        # Initialize aggregated schema
        aggregated = UniversalTaxSchema(
            filing_status=filing_status,
            num_dependents=num_dependents,
        )
        
        try:
            # Process each document
            for doc in documents:
                result = self.process_landingai_output(doc, filing_status, num_dependents)
                
                if result.get("status") == "success":
                    # Aggregate income
                    aggregated.income_wages += result.get("income_wages", 0)
                    aggregated.income_nonemployee_compensation += result.get("income_nonemployee_compensation", 0)
                    aggregated.income_other_income += result.get("income_other_income", 0)
                    aggregated.income_rents += result.get("income_rents", 0)
                    aggregated.income_royalties += result.get("income_royalties", 0)
                    aggregated.income_fishing_boat_proceeds += result.get("income_fishing_boat_proceeds", 0)
                    aggregated.income_interest_income += result.get("income_interest_income", 0)
                    aggregated.income_dividend_income += result.get("income_dividend_income", 0)
                    aggregated.income_capital_gains += result.get("income_capital_gains", 0)
                    aggregated.income_misc += result.get("income_misc", 0)
                    
                    # Aggregate withholding
                    aggregated.withholding_federal_withheld += result.get("withholding_federal_withheld", 0)
                    aggregated.withholding_ss_withheld += result.get("withholding_ss_withheld", 0)
                    aggregated.withholding_medicare_withheld += result.get("withholding_medicare_withheld", 0)
            
            # Recalculate final tax liability
            aggregated = calculate_tax_liability(aggregated)
            
            result = aggregated.to_dict()
            result["status"] = "success"
            result["documents_processed"] = len(documents)
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error aggregating documents: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e),
            }


# ============================================================================
# LLM-POWERED TAX CALCULATOR (Uses Google Gemini for intelligent extraction)
# ============================================================================

class LLMPoweredTaxCalculator:
    """
    Uses Google Gemini to intelligently parse LandingAI output and calculate taxes.
    Gemini is the primary LLM for all tax extraction and calculation.
    Same API key as IRS Chatbot.
    """
    
    def __init__(self, provider: str = "gemini"):
        """
        Initialize LLM-powered tax calculator.
        
        Args:
            provider: "gemini" (only Gemini supported - required)
        """
        self.logger = logger
        self.provider = "gemini"  # Force Gemini
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Gemini client"""
        if not HAS_GEMINI:
            self.logger.error("Google Generative AI library not installed!")
            self.logger.error("Install with: pip install google-generativeai")
            return
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.logger.error("GEMINI_API_KEY environment variable not set!")
            return
        
        try:
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel("gemini-1.5-flash")
            self.logger.info("✅ Google Gemini LLM initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini: {e}")
            self.client = None
    
    def extract_and_calculate_tax(
        self,
        landingai_output: Dict[str, Any],
        filing_status: str = "single",
        num_dependents: int = 0,
    ) -> Dict[str, Any]:
        """
        Use Google Gemini LLM to extract fields from LandingAI output and calculate 2024 IRS taxes.
        
        ⚠️ REQUIRES: GEMINI_API_KEY environment variable
        This method does NOT fall back to regex - it requires Gemini LLM.
        
        Args:
            landingai_output: Raw LandingAI JSON output
            filing_status: Filing status
            num_dependents: Number of dependents
        
        Returns:
            Complete tax calculation with Gemini-extracted fields
            
        Raises:
            Exception if Gemini is not initialized or extraction fails
        """
        
        if not self.client:
            error_msg = (
                "Gemini LLM client not initialized.\n"
                "Set GEMINI_API_KEY environment variable.\n"
                "This system REQUIRES Gemini LLM for tax extraction."
            )
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Step 1: Use Gemini to extract tax fields from markdown
        extracted_fields = self._gemini_extract_fields(landingai_output)
        
        # Step 2: Initialize schema with extracted fields
        schema = UniversalTaxSchema(
            filing_status=filing_status,
            num_dependents=num_dependents,
        )
        
        # Apply extracted fields to schema
        for key, value in extracted_fields.items():
            if hasattr(schema, key) and value is not None:
                setattr(schema, key, value)
        
        # Step 3: Calculate tax liability using IRS 2024 rules
        schema = calculate_tax_liability(schema)
        
        # Step 4: Return result
        result = schema.to_dict()
        result["status"] = "success"
        result["extraction_method"] = "gemini_llm"
        result["document_type"] = extracted_fields.get("document_type", "UNKNOWN")
        
        return result
    
    def _gemini_extract_fields(self, landingai_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use Google Gemini LLM to extract tax fields from LandingAI markdown output.
        Returns dictionary of extracted fields mapped to UniversalTaxSchema.
        """
        
        markdown = landingai_output.get("markdown", "")
        if not markdown:
            return {}
        
        # Create Gemini prompt for tax field extraction
        extraction_prompt = f"""You are a tax extraction expert specializing in IRS 2024 tax forms. 
Parse the following tax document and extract ALL tax fields with high accuracy.

DOCUMENT CONTENT:
{markdown}

EXTRACTION TASK:
1. Identify the document type (W-2, 1099-NEC, 1099-DIV, 1099-INT, 1099-MISC, etc.)
2. Extract these fields EXACTLY as they appear on the form:
   - For W-2: Box 1 (wages), Box 2 (federal withheld), Box 4 (SS tax withheld), Box 6 (Medicare withheld)
   - For 1099-NEC: Box 1 (nonemployee compensation), Box 4 (federal withheld)
   - For 1099-DIV: Box 1a (ordinary dividends), Box 2a (capital gains), Box 4 (federal withheld)
   - For 1099-INT: Box 1 (interest), Box 4 (federal withheld)
   - For 1099-MISC: Box 1 (rents), Box 5 (royalties), Box 7 (nonemployee compensation)

IMPORTANT RULES:
- Extract ONLY numeric values (no $ signs or formatting)
- If a field is blank/zero, report it as 0
- Be precise with decimal values (e.g., 12350.00, not 12350)
- Return ONLY valid JSON, no extra text

RESPONSE FORMAT (MUST be valid JSON):
{{
  "document_type": "W-2" or "1099-NEC" or "1099-DIV" or "1099-INT" or "1099-MISC",
  "income_wages": numeric,
  "income_nonemployee_compensation": numeric,
  "income_dividend_income": numeric,
  "income_interest_income": numeric,
  "income_capital_gains": numeric,
  "income_rents": numeric,
  "income_royalties": numeric,
  "withholding_federal_withheld": numeric,
  "withholding_ss_withheld": numeric,
  "withholding_medicare_withheld": numeric
}}

Extract now. Return ONLY the JSON object:"""
        
        try:
            response = self.client.generate_content(extraction_prompt)
            response_text = response.text
            
            # Parse JSON response
            # Try to extract JSON from the response (may contain extra text)
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                extracted = json.loads(json_match.group())
                # Convert all numeric values
                for key in extracted:
                    if isinstance(extracted[key], str):
                        try:
                            extracted[key] = float(extracted[key].replace(',', ''))
                        except:
                            extracted[key] = 0.0
                    elif extracted[key] is None:
                        extracted[key] = 0.0
                return extracted
            
        except Exception as e:
            self.logger.error(f"Gemini extraction error: {str(e)}")
        
        return {}
    
    def _fallback_extraction(
        self,
        landingai_output: Dict[str, Any],
        filing_status: str = "single",
        num_dependents: int = 0,
    ) -> Dict[str, Any]:
        """
        ❌ DISABLED - Fallback extraction is no longer available.
        
        This system REQUIRES Gemini LLM.
        Regex-based extraction and other LLM providers have been removed.
        
        To use this system:
        1. Set GEMINI_API_KEY environment variable (same as IRS Chatbot)
        2. Restart the API server
        """
        raise RuntimeError(
            "Regex fallback extraction is DISABLED.\n"
            "This system requires Google Gemini LLM.\n"
            "Set GEMINI_API_KEY and restart the server."
        )


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example LandingAI output
    example_1099_nec = {
        "markdown": "Form 1099-NEC Nonemployee Compensation Box 1: $6,750.00",
        "extracted_values": [
            {"text": "Box 1", "confidence": 0.95},
            {"text": "$6,750.00", "confidence": 0.98},
        ],
        "key_value_pairs": {
            "Box 1 (Nonemployee Compensation)": "$6,750.00",
        },
    }
    
    # Create agent and process
    agent = LLMTaxAgent()
    result = agent.process_landingai_output(
        example_1099_nec,
        filing_status="single",
        num_dependents=0,
    )
    
    print(json.dumps(result, indent=2))

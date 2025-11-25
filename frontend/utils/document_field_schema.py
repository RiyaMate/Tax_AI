"""
Document Field Schema Generator
Defines all available fields for each tax document type and generates LLM prompts.
This allows the LLM to know EXACTLY what fields exist before extraction.
"""

from enum import Enum
from typing import Dict, List, Tuple
from llm_tax_agent import DocumentType


class DocumentFieldSchema:
    """
    Comprehensive field definitions for all supported tax documents.
    Maps document types to their available fields with descriptions and IRS box numbers.
    """
    
    # W-2 FIELDS
    W2_FIELDS = {
        "wages": ("Box 1", "Wages, tips, other compensation"),
        "federal_income_tax_withheld": ("Box 2", "Federal income tax withheld"),
        "social_security_wages": ("Box 3", "Social Security wages"),
        "social_security_tax_withheld": ("Box 4", "Social Security tax withheld"),
        "medicare_wages": ("Box 5", "Medicare wages and tips"),
        "medicare_tax_withheld": ("Box 6", "Medicare tax withheld"),
        "social_security_tips": ("Box 7", "Social Security tips"),
        "allocated_tips": ("Box 8", "Allocated tips"),
        "dependent_care_benefits": ("Box 10", "Dependent care benefits"),
        "nonqualified_deferred_comp": ("Box 11", "Nonqualified deferred compensation"),
        "statutory_employee": ("Box 13a", "Statutory employee"),
        "retired_public_safety_officer": ("Box 13b", "Retired public safety officer"),
        "third_party_sick_pay": ("Box 13c", "Third party sick pay"),
        "employee_name": ("Header", "Employee name"),
        "employee_ssn": ("Header", "Employee SSN/TIN"),
        "employer_name": ("Header", "Employer name"),
        "employer_ein": ("Header", "Employer EIN"),
        "employer_address": ("Header", "Employer address"),
    }
    
    # 1099-NEC FIELDS
    FORM_1099_NEC_FIELDS = {
        "nonemployee_compensation": ("Box 1", "Nonemployee compensation"),
        "payment_method": ("Box 1a", "Payment method indicator"),
        "merchant_category_code": ("Box 1b", "Merchant category code"),
        "federal_income_tax_withheld": ("Box 2", "Federal income tax withheld"),
        "recipient_name": ("Header", "Recipient name"),
        "recipient_tin": ("Header", "Recipient TIN"),
        "payer_name": ("Header", "Payer name"),
        "payer_ein": ("Header", "Payer EIN"),
        "payer_address": ("Header", "Payer address"),
        "account_number": ("Header", "Account number"),
        "secondary_tin": ("Header", "Secondary TIN"),
        "fatca_filing_requirement": ("Header", "FATCA filing requirement"),
    }
    
    # 1099-MISC FIELDS (10 boxes)
    FORM_1099_MISC_FIELDS = {
        "rents": ("Box 1", "Rents"),
        "royalties": ("Box 2", "Royalties"),
        "other_income": ("Box 3", "Other income"),
        "federal_income_tax_withheld": ("Box 4", "Federal income tax withheld"),
        "fishing_boat_proceeds": ("Box 5", "Fishing boat proceeds"),
        "medical_payments": ("Box 6", "Medical payments - NOT taxable to recipient"),
        "direct_sales": ("Box 7", "Direct sales - informational only"),
        "substitute_payments": ("Box 8", "Substitute payments"),
        "crop_insurance_proceeds": ("Box 9", "Crop insurance proceeds"),
        "gross_proceeds_attorney": ("Box 10", "Gross proceeds attorney"),
        "fish_purchased_for_resale": ("Box 11", "Fish purchased for resale - NOT income"),
        "section_409a_deferrals": ("Box 12", "Section 409a deferrals"),
        "excess_parachute_payments": ("Box 14", "Excess parachute payments"),
        "nonqualified_deferred_comp": ("Box 15", "Nonqualified deferred comp"),
        "recipient_name": ("Header", "Recipient name"),
        "recipient_tin": ("Header", "Recipient TIN"),
        "payer_name": ("Header", "Payer name"),
        "payer_ein": ("Header", "Payer EIN"),
        "payer_address": ("Header", "Payer address"),
    }
    
    # 1099-INT FIELDS
    FORM_1099_INT_FIELDS = {
        "interest_income": ("Box 1", "Interest income"),
        "us_savings_bonds": ("Box 3", "US savings bonds"),
        "federal_income_tax_withheld": ("Box 4", "Federal income tax withheld"),
        "federal_interest_subsidy": ("Box 8", "Federal interest subsidy"),
        "recipient_name": ("Header", "Recipient name"),
        "recipient_tin": ("Header", "Recipient TIN"),
        "payer_name": ("Header", "Payer name"),
        "payer_ein": ("Header", "Payer EIN"),
        "payer_address": ("Header", "Payer address"),
        "account_number": ("Header", "Account number"),
    }
    
    # 1099-DIV FIELDS
    FORM_1099_DIV_FIELDS = {
        "ordinary_dividends": ("Box 1a", "Ordinary dividends"),
        "qualified_dividends": ("Box 1b", "Qualified dividends"),
        "capital_gain_distributions": ("Box 2a", "Capital gain distributions"),
        "long_term_capital_gains": ("Box 2b", "Long-term capital gains"),
        "unrecaptured_section_1250": ("Box 2d", "Unrecaptured Section 1250 gain"),
        "section_1202_gains": ("Box 2e", "Section 1202 gain"),
        "collectibles_gains": ("Box 2f", "Collectibles (28%) gain"),
        "nondividend_distributions": ("Box 3", "Nondividend distributions"),
        "federal_income_tax_withheld": ("Box 4", "Federal income tax withheld"),
        "investment_expenses": ("Box 5", "Investment expenses"),
        "foreign_tax_paid": ("Box 7", "Foreign tax paid"),
        "foreign_country": ("Box 8a", "Foreign country"),
        "recipient_name": ("Header", "Recipient name"),
        "recipient_tin": ("Header", "Recipient TIN"),
        "payer_name": ("Header", "Payer name"),
        "payer_ein": ("Header", "Payer EIN"),
        "payer_address": ("Header", "Payer address"),
    }
    
    # 1099-B FIELDS
    FORM_1099_B_FIELDS = {
        "total_proceeds": ("Box 1d", "Total proceeds from sales"),
        "cost_basis": ("Box 1e", "Cost basis"),
        "adjustment_code": ("Box 1f", "Adjustment code"),
        "short_term_gains": ("Box 1g", "Short-term gains/losses"),
        "long_term_gains": ("Box 1h", "Long-term gains/losses"),
        "gain_or_loss": ("Box 1i", "Gain or loss"),
        "wash_sale_loss_disallowed": ("Box 1j", "Wash sale loss disallowed"),
        "federal_income_tax_withheld": ("Box 1k", "Federal income tax withheld"),
        "recipient_name": ("Header", "Recipient name"),
        "recipient_tin": ("Header", "Recipient TIN"),
        "payer_name": ("Header", "Payer name"),
        "payer_ein": ("Header", "Payer EIN"),
        "payer_address": ("Header", "Payer address"),
    }
    
    # 1099-K FIELDS
    FORM_1099_K_FIELDS = {
        "monthly_gross_amounts": ("Box 1a-l", "Monthly gross transaction amounts (12 months)"),
        "card_not_present_transactions": ("Box 1a", "Card not present transactions"),
        "merchant_category_code": ("Box 2", "Merchant category code"),
        "state_income_tax_withheld": ("Box 3", "State income tax withheld"),
        "state": ("Box 3a", "State code"),
        "state_identification_number": ("Box 3b", "State identification number"),
        "federal_income_tax_withheld": ("Box 1f", "Federal income tax withheld"),
        "recipient_name": ("Header", "Recipient name"),
        "recipient_tin": ("Header", "Recipient TIN"),
        "recipient_address": ("Header", "Recipient address"),
        "payer_name": ("Header", "Payer name"),
        "payer_ein": ("Header", "Payer EIN"),
        "payer_address": ("Header", "Payer address"),
    }
    
    # 1099-OID FIELDS
    FORM_1099_OID_FIELDS = {
        "original_issue_discount": ("Box 1", "Original issue discount"),
        "oid_from_call_redemption": ("Box 2", "OID from call or redemption"),
        "early_redemption": ("Box 3", "Early redemption"),
        "oid_accrued_this_year": ("Box 5", "OID accrued this year"),
        "federal_income_tax_withheld": ("Box 4", "Federal income tax withheld"),
        "us_savings_bonds": ("Box 8", "US savings bonds"),
        "recipient_name": ("Header", "Recipient name"),
        "recipient_tin": ("Header", "Recipient TIN"),
        "issuer_name": ("Header", "Issuer name"),
        "issuer_ein": ("Header", "Issuer EIN"),
        "issuer_address": ("Header", "Issuer address"),
    }
    
    # PAYSTUB FIELDS
    PAYSTUB_FIELDS = {
        "gross_pay": ("Header", "Gross pay"),
        "federal_income_tax": ("Deduction", "Federal income tax withheld"),
        "social_security_tax": ("Deduction", "Social Security tax withheld"),
        "medicare_tax": ("Deduction", "Medicare tax withheld"),
        "state_income_tax": ("Deduction", "State income tax withheld"),
        "local_income_tax": ("Deduction", "Local income tax withheld"),
        "net_pay": ("Footer", "Net pay"),
        "employee_name": ("Header", "Employee name"),
        "employee_ssn": ("Header", "Employee SSN"),
        "employer_name": ("Header", "Employer name"),
        "employer_ein": ("Header", "Employer EIN"),
        "pay_period": ("Header", "Pay period"),
        "pay_date": ("Header", "Pay date"),
    }
    
    # BANK STATEMENT FIELDS
    BANK_STATEMENT_FIELDS = {
        "account_number": ("Header", "Account number"),
        "account_type": ("Header", "Account type"),
        "statement_period": ("Header", "Statement period"),
        "opening_balance": ("Header", "Opening balance"),
        "closing_balance": ("Header", "Closing balance"),
        "total_deposits": ("Summary", "Total deposits"),
        "total_withdrawals": ("Summary", "Total withdrawals"),
        "interest_earned": ("Summary", "Interest earned"),
        "bank_name": ("Header", "Bank name"),
        "bank_address": ("Header", "Bank address"),
    }
    
    # Mapping of DocumentType to field dictionary
    SCHEMA_MAP = {
        DocumentType.W2: W2_FIELDS,
        DocumentType.FORM_1099_NEC: FORM_1099_NEC_FIELDS,
        DocumentType.FORM_1099_MISC: FORM_1099_MISC_FIELDS,
        DocumentType.FORM_1099_INT: FORM_1099_INT_FIELDS,
        DocumentType.FORM_1099_DIV: FORM_1099_DIV_FIELDS,
        DocumentType.FORM_1099_B: FORM_1099_B_FIELDS,
        DocumentType.FORM_1099_K: FORM_1099_K_FIELDS,
        DocumentType.FORM_1099_OID: FORM_1099_OID_FIELDS,
        DocumentType.PAYSTUB: PAYSTUB_FIELDS,
        DocumentType.BANK_STATEMENT: BANK_STATEMENT_FIELDS,
    }
    
    @staticmethod
    def get_schema_for_document(doc_type: DocumentType) -> Dict[str, Tuple[str, str]]:
        """
        Get all available fields for a document type.
        
        Args:
            doc_type: The document type
            
        Returns:
            Dictionary mapping field_name -> (box_number, description)
        """
        return DocumentFieldSchema.SCHEMA_MAP.get(doc_type, {})
    
    @staticmethod
    def get_field_names_for_document(doc_type: DocumentType) -> List[str]:
        """Get just the field names for a document type"""
        schema = DocumentFieldSchema.get_schema_for_document(doc_type)
        return list(schema.keys())
    
    @staticmethod
    def get_field_descriptions_for_document(doc_type: DocumentType) -> Dict[str, str]:
        """Get field descriptions only (without box numbers)"""
        schema = DocumentFieldSchema.get_schema_for_document(doc_type)
        return {name: desc for name, (box, desc) in schema.items()}
    
    @staticmethod
    def generate_field_list_prompt(doc_type: DocumentType) -> str:
        """
        Generate a prompt segment showing all available fields.
        Used by LLM to know what to extract.
        
        Args:
            doc_type: The document type
            
        Returns:
            Formatted prompt with all field definitions
        """
        schema = DocumentFieldSchema.get_schema_for_document(doc_type)
        
        if not schema:
            return f"No schema defined for {doc_type.value}"
        
        prompt = f"\nAVAILABLE FIELDS FOR {doc_type.value}:\n"
        prompt += "=" * 70 + "\n"
        
        # Group by box type
        by_type = {}
        for field_name, (box_number, description) in schema.items():
            box_type = box_number.split()[0]  # "Box", "Header", "Deduction", "Summary", etc.
            if box_type not in by_type:
                by_type[box_type] = []
            by_type[box_type].append((field_name, box_number, description))
        
        # Print organized
        for box_type in ["Box", "Header", "Deduction", "Summary", "Footer"]:
            if box_type in by_type:
                prompt += f"\n{box_type}:\n"
                for field_name, box_number, description in by_type[box_type]:
                    prompt += f"  • {field_name:40s} ({box_number:15s}): {description}\n"
        
        prompt += "\n" + "=" * 70 + "\n"
        return prompt


def get_available_fields_for_document(doc_type: DocumentType) -> str:
    """
    Helper function: Get formatted list of available fields for a document.
    This is what gets sent to the LLM to tell it what to extract.
    
    Args:
        doc_type: The document type
        
    Returns:
        Human-readable string listing all available fields with descriptions
    """
    return DocumentFieldSchema.generate_field_list_prompt(doc_type)


if __name__ == "__main__":
    # Demo
    for doc_type in [DocumentType.W2, DocumentType.FORM_1099_MISC, DocumentType.FORM_1099_DIV]:
        print(get_available_fields_for_document(doc_type))
        print("\n" + "="*80 + "\n")

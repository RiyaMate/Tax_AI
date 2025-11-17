"""
Tax Calculation Engine for Form 1040 Preparation
Implements 2024 IRS tax brackets, standard deductions, and tax liability calculations
"""

import logging
from typing import Dict, Any, List
from enum import Enum
from dataclasses import dataclass
from decimal import Decimal

logger = logging.getLogger(__name__)

class FilingStatus(Enum):
    SINGLE = "Single"
    MARRIED_FILING_JOINTLY = "Married Filing Jointly"
    MARRIED_FILING_SEPARATELY = "Married Filing Separately"
    HEAD_OF_HOUSEHOLD = "Head of Household"
    QUALIFYING_WIDOW = "Qualifying Widow(er)"

@dataclass
class TaxBracket:
    """Represents a single tax bracket"""
    min_income: float
    max_income: float
    rate: float

class TaxCalculationEngine:
    """
    Calculates federal income tax liability based on 2024 IRS standards
    """
    
    # 2024 Tax Brackets
    TAX_BRACKETS = {
        FilingStatus.SINGLE: [
            TaxBracket(0, 11600, 0.10),
            TaxBracket(11600, 47150, 0.12),
            TaxBracket(47150, 100525, 0.22),
            TaxBracket(100525, 191950, 0.24),
            TaxBracket(191950, 243725, 0.32),
            TaxBracket(243725, 609350, 0.35),
            TaxBracket(609350, float('inf'), 0.37),
        ],
        FilingStatus.MARRIED_FILING_JOINTLY: [
            TaxBracket(0, 23200, 0.10),
            TaxBracket(23200, 94300, 0.12),
            TaxBracket(94300, 201050, 0.22),
            TaxBracket(201050, 383900, 0.24),
            TaxBracket(383900, 487450, 0.32),
            TaxBracket(487450, 731200, 0.35),
            TaxBracket(731200, float('inf'), 0.37),
        ],
        FilingStatus.MARRIED_FILING_SEPARATELY: [
            TaxBracket(0, 11600, 0.10),
            TaxBracket(11600, 47150, 0.12),
            TaxBracket(47150, 100525, 0.22),
            TaxBracket(100525, 191950, 0.24),
            TaxBracket(191950, 243725, 0.32),
            TaxBracket(243725, 365600, 0.35),
            TaxBracket(365600, float('inf'), 0.37),
        ],
        FilingStatus.HEAD_OF_HOUSEHOLD: [
            TaxBracket(0, 17450, 0.10),
            TaxBracket(17450, 66550, 0.12),
            TaxBracket(66550, 151900, 0.22),
            TaxBracket(151900, 261500, 0.24),
            TaxBracket(261500, 398350, 0.32),
            TaxBracket(398350, 731200, 0.35),
            TaxBracket(731200, float('inf'), 0.37),
        ],
        FilingStatus.QUALIFYING_WIDOW: [
            TaxBracket(0, 23200, 0.10),
            TaxBracket(23200, 94300, 0.12),
            TaxBracket(94300, 201050, 0.22),
            TaxBracket(201050, 383900, 0.24),
            TaxBracket(383900, 487450, 0.32),
            TaxBracket(487450, 731200, 0.35),
            TaxBracket(731200, float('inf'), 0.37),
        ],
    }
    
    # 2024 Standard Deductions
    STANDARD_DEDUCTIONS = {
        FilingStatus.SINGLE: 14600,
        FilingStatus.MARRIED_FILING_JOINTLY: 29200,
        FilingStatus.MARRIED_FILING_SEPARATELY: 14600,
        FilingStatus.HEAD_OF_HOUSEHOLD: 21900,
        FilingStatus.QUALIFYING_WIDOW: 29200,
    }
    
    # Dependent exemption (2024)
    DEPENDENT_EXEMPTION = 4700
    
    # Child Tax Credit
    CHILD_TAX_CREDIT = 2000
    
    # EARNED INCOME TAX CREDIT (EITC) 2024 - Simplified
    EITC_RATES = {
        FilingStatus.SINGLE: {
            0: {"phase_in_rate": 0.0765, "max_credit": 3995, "phase_out_start": 17810, "phase_out_rate": 0.0765},
            1: {"phase_in_rate": 0.34, "max_credit": 3995, "phase_out_start": 17810, "phase_out_rate": 0.21},
            2: {"phase_in_rate": 0.40, "max_credit": 4964, "phase_out_start": 18123, "phase_out_rate": 0.21},
        },
        FilingStatus.MARRIED_FILING_JOINTLY: {
            0: {"phase_in_rate": 0.0765, "max_credit": 3995, "phase_out_start": 23370, "phase_out_rate": 0.0765},
            1: {"phase_in_rate": 0.34, "max_credit": 3995, "phase_out_start": 23370, "phase_out_rate": 0.21},
            2: {"phase_in_rate": 0.40, "max_credit": 4964, "phase_out_start": 23693, "phase_out_rate": 0.21},
        },
    }
    
    def __init__(self):
        self.logger = logger
    
    def get_filing_status_enum(self, filing_status_str: str) -> FilingStatus:
        """Convert string to FilingStatus enum"""
        for status in FilingStatus:
            if status.value == filing_status_str:
                return status
        raise ValueError(f"Invalid filing status: {filing_status_str}")
    
    def calculate_tax(self, taxable_income: float, filing_status: FilingStatus) -> float:
        """
        Calculate federal income tax using 2024 tax brackets
        """
        if taxable_income <= 0:
            return 0.0
        
        tax = 0.0
        brackets = self.TAX_BRACKETS[filing_status]
        
        for bracket in brackets:
            if taxable_income > bracket.min_income:
                taxable_in_bracket = min(taxable_income, bracket.max_income) - bracket.min_income
                tax += taxable_in_bracket * bracket.rate
            else:
                break
        
        return round(tax, 2)
    
    def calculate_eitc(self, earned_income: float, filing_status: FilingStatus, dependents: int) -> float:
        """
        Calculate Earned Income Tax Credit (simplified)
        """
        if earned_income <= 0 or dependents > 2:
            return 0.0
        
        filing_status_map = {
            FilingStatus.MARRIED_FILING_JOINTLY: FilingStatus.MARRIED_FILING_JOINTLY,
            FilingStatus.MARRIED_FILING_SEPARATELY: FilingStatus.SINGLE,
            FilingStatus.SINGLE: FilingStatus.SINGLE,
            FilingStatus.HEAD_OF_HOUSEHOLD: FilingStatus.SINGLE,
            FilingStatus.QUALIFYING_WIDOW: FilingStatus.MARRIED_FILING_JOINTLY,
        }
        
        mapped_status = filing_status_map.get(filing_status, FilingStatus.SINGLE)
        
        try:
            eitc_config = self.EITC_RATES[mapped_status][dependents]
        except KeyError:
            return 0.0
        
        # Phase in
        credit = earned_income * eitc_config["phase_in_rate"]
        credit = min(credit, eitc_config["max_credit"])
        
        # Phase out
        if earned_income > eitc_config["phase_out_start"]:
            phase_out_amount = (earned_income - eitc_config["phase_out_start"]) * eitc_config["phase_out_rate"]
            credit = max(0, credit - phase_out_amount)
        
        return round(credit, 2)
    
    def calculate_child_tax_credit(self, dependent_count: int) -> float:
        """
        Calculate Child Tax Credit
        """
        return min(dependent_count, 10) * self.CHILD_TAX_CREDIT
    
    def process_tax_return(self, tax_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main function to process a complete tax return
        """
        try:
            # Extract filing information
            filing_status = self.get_filing_status_enum(tax_data.get("filing_status", "Single"))
            dependent_count = tax_data.get("dependent_count", 0)
            
            # Extract income items
            w2_wages = tax_data.get("w2_wages", 0.0)
            nec_income = tax_data.get("nec_income", 0.0)
            int_income = tax_data.get("interest_income", 0.0)
            other_income = tax_data.get("other_income", 0.0)
            
            # Extract withholdings
            federal_withheld_w2 = tax_data.get("federal_withheld_w2", 0.0)
            federal_withheld_1099 = tax_data.get("federal_withheld_1099", 0.0)
            total_federal_withheld = federal_withheld_w2 + federal_withheld_1099
            
            # Calculate total income
            total_income = w2_wages + nec_income + int_income + other_income
            
            # Apply standard deduction
            standard_deduction = self.STANDARD_DEDUCTIONS[filing_status]
            taxable_income = max(0, total_income - standard_deduction)
            
            # Calculate base tax
            base_tax = self.calculate_tax(taxable_income, filing_status)
            
            # Calculate credits
            eitc = self.calculate_eitc(w2_wages, filing_status, dependent_count)
            child_tax_credit = self.calculate_child_tax_credit(dependent_count)
            
            # Total credits
            total_credits = eitc + child_tax_credit
            
            # Calculate tax liability
            total_tax_liability = max(0, base_tax - total_credits)
            
            # Calculate refund or amount owed
            refund_or_owed = total_federal_withheld - total_tax_liability
            
            result = {
                "filing_status": filing_status.value,
                "dependent_count": dependent_count,
                "income": {
                    "w2_wages": round(w2_wages, 2),
                    "nec_income": round(nec_income, 2),
                    "interest_income": round(int_income, 2),
                    "other_income": round(other_income, 2),
                    "total_income": round(total_income, 2),
                },
                "deductions": {
                    "standard_deduction": standard_deduction,
                    "taxable_income": round(taxable_income, 2),
                },
                "tax_calculation": {
                    "base_tax": round(base_tax, 2),
                    "earned_income_tax_credit": round(eitc, 2),
                    "child_tax_credit": round(child_tax_credit, 2),
                    "total_credits": round(total_credits, 2),
                    "total_tax_liability": round(total_tax_liability, 2),
                },
                "withholding": {
                    "w2_federal_withheld": round(federal_withheld_w2, 2),
                    "1099_federal_withheld": round(federal_withheld_1099, 2),
                    "total_federal_withheld": round(total_federal_withheld, 2),
                },
                "final_result": {
                    "total_tax_liability": round(total_tax_liability, 2),
                    "total_payments_and_credits": round(total_federal_withheld + total_credits, 2),
                    "refund_amount" if refund_or_owed >= 0 else "amount_owed": round(abs(refund_or_owed), 2),
                    "refund": round(refund_or_owed, 2) if refund_or_owed >= 0 else 0.0,
                    "amount_owed": round(abs(refund_or_owed), 2) if refund_or_owed < 0 else 0.0,
                },
                "status": "calculated"
            }
            
            self.logger.info(f"Tax return processed successfully. Refund/Owed: ${refund_or_owed:.2f}")
            return result
        
        except Exception as e:
            self.logger.error(f"Error processing tax return: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

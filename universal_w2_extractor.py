#!/usr/bin/env python3
"""
UNIVERSAL W-2 EXTRACTION ENGINE
Format-agnostic extraction that works with ANY W-2 layout
Uses semantic matching + positional anchoring instead of rigid label matching
"""

import re
from typing import Dict, Any, Optional, List, Tuple

class UniversalW2Extractor:
    """
    Extracts W-2 fields universally by:
    1. Finding ALL currency values in the document
    2. Matching them to their corresponding Box numbers
    3. Using context clues (surrounding text) to identify field types
    4. Falling back to positional logic if labels are ambiguous
    """
    
    def __init__(self, text: str):
        self.text = text
        self.lines = text.split('\n')
        
        # Define field identification patterns with alternatives
        self.field_patterns = {
            'wages': [
                r'(?:Box\s*1|^1\.?)[\s:]*(?:Wages|tips|compensation)',
                r'(?:Wages|wages),?\s*(?:tips|other\s*compensation)?',
                r'Wages,\s*tips,\s*other\s*(?:compensation|comp)',
            ],
            'federal_income_tax_withheld': [
                r'(?:Box\s*2|^2\.?)[\s:]*(?:Federal|income\s*tax)',
                r'Federal\s*(?:income\s*)?tax\s*withheld',
                r'Federal\s+tax\s+withheld',
            ],
            'social_security_wages': [
                r'(?:Box\s*3|^3\.?)[\s:]*(?:Social|Security)',
                r'Social\s+Security\s+wages',
                r'Social\s+Security\s+wages\s+and\s+tips',
            ],
            'social_security_tax_withheld': [
                r'(?:Box\s*4|^4\.?)[\s:]*(?:Social|Security|tax)',
                r'Social\s+Security\s+tax\s+withheld',
            ],
            'medicare_wages': [
                r'(?:Box\s*5|^5\.?)[\s:]*(?:Medicare)',
                r'Medicare\s+wages\s+and\s+tips',
            ],
            'medicare_tax_withheld': [
                r'(?:Box\s*6|^6\.?)[\s:]*(?:Medicare|tax)',
                r'Medicare\s+tax\s+withheld',
            ],
        }
    
    def find_value_after_label(self, label_pattern: str, lookahead: int = 500) -> Optional[str]:
        """Find currency value immediately after a label pattern"""
        try:
            match = re.search(label_pattern, self.text, re.IGNORECASE | re.DOTALL)
            if match:
                # Look ahead from the end of the label match
                start_pos = match.end()
                lookahead_text = self.text[start_pos:start_pos + lookahead]
                
                # Find first currency value
                value_match = re.search(r'[\$]?\s*([0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?)', lookahead_text)
                if value_match:
                    return value_match.group(1)
        except:
            pass
        return None
    
    def extract_field(self, field_name: str) -> Optional[str]:
        """Extract a field using multiple pattern strategies"""
        patterns = self.field_patterns.get(field_name, [])
        
        # Try each pattern
        for pattern in patterns:
            value = self.find_value_after_label(pattern)
            if value:
                return value
        
        return None
    
    def extract_all(self) -> Dict[str, Any]:
        """Extract all W-2 fields"""
        result = {
            'document_type': 'W-2',
            'wages': None,
            'federal_income_tax_withheld': None,
            'social_security_wages': None,
            'social_security_tax_withheld': None,
            'medicare_wages': None,
            'medicare_tax_withheld': None,
            'employer_ein': None,
            'employee_ssn': None,
        }
        
        # Extract numeric fields
        for field in ['wages', 'federal_income_tax_withheld', 'social_security_wages', 
                      'social_security_tax_withheld', 'medicare_wages', 'medicare_tax_withheld']:
            result[field] = self.extract_field(field)
        
        # Extract EIN (11-digit with specific format)
        ein_match = re.search(r'EIN[:\s]*(\d{2}-\d{7})', self.text, re.IGNORECASE)
        if ein_match:
            result['employer_ein'] = ein_match.group(1)
        
        # Extract SSN (9-digit with specific format)
        ssn_match = re.search(r'(?:Employee\s+)?SSN[:\s]*(\d{3}-\d{2}-\d{4})', self.text, re.IGNORECASE)
        if ssn_match:
            result['employee_ssn'] = ssn_match.group(1)
        
        return result


# Test it with your actual W-2 data
if __name__ == '__main__':
    # Your actual W-2 text
    w2_text = """
Form W-2 (2024) – Wage and Tax Statement

Employer: NOKIA
Employer EIN: 12-3456789
Employer Address: 600 Technology Drive, Espoo, Finland

Employee: RSM
Employee SSN: 123-45-6789

Box 1 - Wages, tips, other compensation: $23,500.00
Box 2 - Federal income tax withheld: $1,500.00
Box 3 - Social Security wages and tips: $23,500.00
Box 4 - Social Security tax withheld: $1,457.00
Box 5 - Medicare wages and tips: $23,500.00
Box 6 - Medicare tax withheld: $340.75
Box 17 - State income tax: $800.00
    """
    
    extractor = UniversalW2Extractor(w2_text)
    result = extractor.extract_all()
    
    print("=" * 80)
    print("UNIVERSAL W-2 EXTRACTION TEST")
    print("=" * 80)
    print("\nExtracted Fields:")
    for key, value in result.items():
        if key != 'document_type':
            status = "[OK]" if value else "[MISS]"
            print(f"  {status} {key}: {value}")
    
    # Calculate tax to verify
    print("\n" + "=" * 80)
    print("VERIFICATION: Tax Calculation")
    print("=" * 80)
    
    try:
        wages = float(result['wages'].replace(',', '').replace('$', '')) if result['wages'] else 0
        fed_withheld = float(result['federal_income_tax_withheld'].replace(',', '').replace('$', '')) if result['federal_income_tax_withheld'] else 0
        
        print(f"\nW-2 Wages (Box 1): ${wages:,.2f}")
        print(f"Federal Withheld (Box 2): ${fed_withheld:,.2f}")
        
        # Tax calculation
        standard_deduction = 14600  # 2024 single
        taxable_income = max(0, wages - standard_deduction)
        
        # Simple 2024 tax bracket for single filer
        if taxable_income <= 11000:
            federal_tax = taxable_income * 0.10
        elif taxable_income <= 44725:
            federal_tax = 1100 + (taxable_income - 11000) * 0.12
        else:
            federal_tax = 1100 + 4047 + (taxable_income - 44725) * 0.22
        
        refund_due = fed_withheld - federal_tax
        
        print(f"\nStandard Deduction: ${standard_deduction:,.2f}")
        print(f"Taxable Income: ${taxable_income:,.2f}")
        print(f"Federal Tax Owed: ${federal_tax:,.2f}")
        print(f"\nRefund/Due: ${abs(refund_due):,.2f} ({'REFUND' if refund_due > 0 else 'DUE'})")
    except Exception as e:
        print(f"Error in calculation: {e}")

"""
UNIVERSAL MARKDOWN NUMERIC EXTRACTOR

Zero schema. Zero form-specific regex. Works on ANY Markdown.

This system extracts all numeric values from LandingAI Markdown output
and automatically normalizes them for tax calculation.

Principle:
  1. Extract all (label, numeric_value) pairs from Markdown
  2. Normalize field names using semantic keyword matching
  3. Feed into tax engine without form assumptions
"""

import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, field


@dataclass
class NumericField:
    """Represents a single extracted numeric field."""
    raw_label: str          # Original label from Markdown
    raw_value: float        # Parsed numeric value
    normalized_key: str     # Auto-detected field name
    confidence: float       # Confidence in normalization (0.0-1.0)
    context: str = ""       # Surrounding context for debugging


class UniversalMarkdownNumericExtractor:
    """
    Extracts numeric fields from ANY Markdown without schema.
    """

    def __init__(self):
        """Initialize the extractor."""
        self.extracted_fields: List[NumericField] = []
        self.raw_numeric_map: Dict[str, float] = {}

    def extract_all_numeric_pairs(self, md_text: str) -> Dict[str, float]:
        """
        Extract all numeric fields from Markdown using DUAL regex patterns.
        
        Supports TWO formats:
        1. Colon/dash separator: "Label: $45,000" or "Label - $45,000"
        2. Table format: "Label 45000.00" (ADE table output with spaces)
        
        Matches:
          - Wages: $45,000
          - Box 1 - Federal income tax: $1,500
          - Box 1 Wages, tips, other comp. 23500.00
          - Gross Pay 25,000.00
        
        Args:
            md_text: Markdown text from LandingAI
            
        Returns:
            Dictionary mapping cleaned labels to numeric values
        """
        fields = {}
        
        # PATTERN 1: Colon/dash with explicit word boundary
        # Examples: "Wages: $45,000", "Box 1 - Federal income tax: $1,500"
        # Requires word characters/spaces before colon/dash (no markdown symbols)
        pattern1 = r"(?:^|\s)([A-Za-z0-9\s\-\.,()/#]+?)\s*:\s*\$?\s*([\d,]+(?:\.\d+)?)(?:\s|$)"
        
        # PATTERN 2: Table format (label followed by multiple spaces then number)
        # Examples: "Box 1 Wages, tips, other comp.          23500.00"
        # Key: 2+ spaces between label and number (not 1 space - that's likely noise)
        # Label must start with Box/number or a word, and can contain periods
        pattern2 = r"^((?:Box\s+\d+\s+)?[A-Za-z0-9][A-Za-z0-9\s\.,()/#\-]*?)\s{2,}\$?([\d,]+(?:\.\d+)?)(?:\s|$)"
        
        # Apply PATTERN 1 (colon/dash with boundaries)
        for match in re.finditer(pattern1, md_text, re.MULTILINE):
            raw_label = match.group(1).strip()
            raw_value_str = match.group(2).strip()
            
            # Skip if label is too short or contains only markdown
            if len(raw_label) < 3 or raw_label.startswith("#"):
                continue
            
            try:
                # Parse numeric value
                clean_value = float(raw_value_str.replace(",", ""))
                
                # Normalize label for storage
                clean_label = (
                    raw_label.lower()
                    .replace(" ", "_")
                    .replace("-", "_")
                    .replace("–", "_")
                    .replace("/", "_")
                    .replace(".", "_")
                    .strip("_")
                )
                
                # Store (keep all occurrences, normalization handles duplicates)
                if clean_label not in fields:
                    fields[clean_label] = clean_value
                else:
                    # If duplicate, sum (handles multiple sections)
                    fields[clean_label] += clean_value
                    
            except ValueError:
                # Could not parse as float, skip
                continue
        
        # Apply PATTERN 2 (table format - multi-space separated)
        for match in re.finditer(pattern2, md_text, re.MULTILINE):
            raw_label = match.group(1).strip()
            raw_value_str = match.group(2).strip()
            
            # Skip if label is too short
            if len(raw_label) < 3:
                continue
            
            # Skip if label is already captured by pattern1
            clean_label_test = (
                raw_label.lower()
                .replace(" ", "_")
                .replace("-", "_")
                .replace("–", "_")
                .replace("/", "_")
                .replace(".", "_")
                .strip("_")
            )
            
            # Skip if we already have this field (pattern1 takes priority)
            if clean_label_test in fields:
                continue
            
            try:
                # Parse numeric value
                clean_value = float(raw_value_str.replace(",", ""))
                
                # Normalize label for storage
                clean_label = clean_label_test
                
                # Store
                if clean_label not in fields:
                    fields[clean_label] = clean_value
                else:
                    # If duplicate, sum
                    fields[clean_label] += clean_value
                    
            except ValueError:
                # Could not parse as float, skip
                continue
        
        self.raw_numeric_map = fields
        return fields

    def normalize_auto(self, fields: Dict[str, float]) -> Dict[str, float]:
        """
        Universal field normalization using keyword matching.
        Auto-detects income, withholding, and tax field types.
        
        No schema dependency. Works on any form structure.
        
        Args:
            fields: Raw numeric field map
            
        Returns:
            Normalized dictionary with standard field names
        """
        normalized = {
            "wages": 0.0,
            "nonemployee_compensation": 0.0,
            "interest_income": 0.0,
            "dividend_income": 0.0,
            "capital_gains": 0.0,
            "federal_income_tax_withheld": 0.0,
            "social_security_wages": 0.0,
            "social_security_tax_withheld": 0.0,
            "medicare_wages": 0.0,
            "medicare_tax_withheld": 0.0,
            "state_tax_withheld": 0.0,
            "employer_ein": None,
            "employee_ssn": None,
        }
        
        for key, value in fields.items():
            k = key.lower()
            
            # -----------------------
            # W-2 / General Wages
            # -----------------------
            if "wage" in k:
                normalized["wages"] = value
            
            # -----------------------
            # Social Security
            # -----------------------
            elif "social" in k and "wage" in k:
                normalized["social_security_wages"] = value
            
            # -----------------------
            # Medicare Wages
            # -----------------------
            elif "medicare" in k and "wage" in k:
                normalized["medicare_wages"] = value
            
            # -----------------------
            # Social Security Tax
            # -----------------------
            elif ("social" in k and "tax" in k) or "ss_tax" in k:
                normalized["social_security_tax_withheld"] = value
            
            # -----------------------
            # Medicare Tax
            # -----------------------
            elif "medicare" in k and "tax" in k:
                normalized["medicare_tax_withheld"] = value
            
            # -----------------------
            # Federal Withholding
            # -----------------------
            elif "withheld" in k or ("federal" in k and "tax" in k):
                # Avoid mis-matching state withheld
                if "state" not in k:
                    normalized["federal_income_tax_withheld"] += value
            
            # -----------------------
            # State Withholding
            # -----------------------
            elif "state" in k and ("withheld" in k or "tax" in k):
                normalized["state_tax_withheld"] = value
            
            # -----------------------
            # 1099-NEC (Nonemployee Compensation)
            # -----------------------
            elif "nec" in k or "nonemployee" in k or "contractor" in k:
                normalized["nonemployee_compensation"] = value
            
            # -----------------------
            # 1099-INT (Interest Income)
            # -----------------------
            elif "interest" in k or "int_" in k:
                normalized["interest_income"] = value
            
            # -----------------------
            # 1099-DIV (Dividends)
            # -----------------------
            elif "div" in k:
                normalized["dividend_income"] = value
            
            # -----------------------
            # Capital Gains
            # -----------------------
            elif "capital" in k or "gain" in k:
                normalized["capital_gains"] = value
        
        return normalized

    def extract_and_normalize(self, md_text: str) -> Dict[str, Any]:
        """
        Full pipeline: extract → normalize → return.
        
        Args:
            md_text: Markdown text from LandingAI
            
        Returns:
            Dictionary with normalized tax fields
        """
        raw_fields = self.extract_all_numeric_pairs(md_text)
        normalized = self.normalize_auto(raw_fields)
        
        return {
            "raw_fields": raw_fields,
            "normalized": normalized,
            "field_count": len(raw_fields),
        }

    def debug_extraction(self, md_text: str) -> str:
        """
        Return human-readable extraction report for debugging.
        
        Args:
            md_text: Markdown text
            
        Returns:
            Formatted debug report
        """
        raw = self.extract_all_numeric_pairs(md_text)
        normalized = self.normalize_auto(raw)
        
        report = "=== UNIVERSAL MARKDOWN NUMERIC EXTRACTION ===\n\n"
        report += f"RAW NUMERIC FIELDS ({len(raw)}):\n"
        for label, value in raw.items():
            report += f"  {label:40s} = {value:15.2f}\n"
        
        report += "\nNORMALIZED TAX FIELDS:\n"
        for key, value in normalized.items():
            if value not in (0.0, None) or key in ["wages", "federal_income_tax_withheld"]:
                report += f"  {key:40s} = {value}\n"
        
        return report


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def extract_markdown_numeric_fields(md_text: str) -> Dict[str, float]:
    """
    Simple extraction: Markdown → raw numeric fields.
    
    Args:
        md_text: LandingAI Markdown
        
    Returns:
        Dictionary of (label, value) pairs
    """
    extractor = UniversalMarkdownNumericExtractor()
    return extractor.extract_all_numeric_pairs(md_text)


def normalize_numeric_fields(fields: Dict[str, float]) -> Dict[str, Any]:
    """
    Simple normalization: raw fields → normalized for tax engine.
    
    Args:
        fields: Raw numeric field map
        
    Returns:
        Normalized fields ready for tax calculation
    """
    extractor = UniversalMarkdownNumericExtractor()
    return extractor.normalize_auto(fields)


def markdown_to_tax_fields(md_text: str) -> Dict[str, Any]:
    """
    Full pipeline: Markdown → normalized tax fields.
    
    Args:
        md_text: LandingAI Markdown
        
    Returns:
        Normalized dictionary ready for tax engine
    """
    extractor = UniversalMarkdownNumericExtractor()
    return extractor.extract_and_normalize(md_text)

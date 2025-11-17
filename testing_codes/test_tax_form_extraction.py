#!/usr/bin/env python3
"""
Test suite for Tax Form Extraction
Tests W-2, 1099-NEC, and 1099-INT form extraction accuracy
"""

import sys
import os
from pathlib import Path

# Add api directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from tax_document_parser import TaxDocumentParser, DocumentType

# Test data based on user-provided samples
SAMPLE_W2 = {
    "document_type": "W-2",
    "expected_fields": {
        "wages": 23500.00,
        "federal_income_tax_withheld": 1500.00,
        "social_security_wages": 23500.00,
        "social_security_tax_withheld": 1457.00,
        "medicare_wages": 23500.00,
        "medicare_tax_withheld": 340.75,
    },
    "validation_rules": {
        "wages": {"min": 0.01, "max": 999999.99},
        "federal_income_tax_withheld": {"min": 0, "max": "<=wages"},
        "social_security_tax_withheld": {"expected_calc": "wages * 0.062", "tolerance": 50},
        "medicare_tax_withheld": {"expected_calc": "wages * 0.0145", "tolerance": 10},
    }
}

SAMPLE_1099NEC = {
    "document_type": "1099-NEC",
    "expected_fields": {
        "nonemployee_compensation": 15000.00,  # Placeholder - adjust to actual value
        "federal_income_tax_withheld": 450.00,  # Placeholder
    },
    "validation_rules": {
        "nonemployee_compensation": {"min": 0.01, "max": 999999.99},
        "federal_income_tax_withheld": {"min": 0, "max": "<=compensation"},
    }
}

SAMPLE_1099INT = {
    "document_type": "1099-INT",
    "expected_fields": {
        "interest_income": 500.00,  # Placeholder
        "federal_income_tax_withheld": 0.00,
    },
    "validation_rules": {
        "interest_income": {"min": 0.01, "max": 999999.99},
        "federal_income_tax_withheld": {"min": 0, "max": "<=interest"},
    }
}

class TaxFormExtractionTest:
    def __init__(self):
        self.parser = TaxDocumentParser()
        self.passed = 0
        self.failed = 0
        self.warnings = []
    
    def log_pass(self, test_name, details=""):
        self.passed += 1
        symbol = "✓"
        print(f"{symbol} PASS: {test_name}")
        if details:
            print(f"  └─ {details}")
    
    def log_fail(self, test_name, expected, actual):
        self.failed += 1
        symbol = "✗"
        print(f"{symbol} FAIL: {test_name}")
        print(f"  Expected: {expected}")
        print(f"  Actual:   {actual}")
    
    def log_warning(self, test_name, message):
        self.warnings.append(f"{test_name}: {message}")
        symbol = "⚠"
        print(f"{symbol} WARN: {test_name}")
        print(f"  └─ {message}")
    
    def test_w2_extraction(self, pdf_path: str):
        """Test W-2 form extraction"""
        print("\n" + "="*60)
        print("TEST: W-2 Form Extraction")
        print("="*60)
        
        if not os.path.exists(pdf_path):
            self.log_fail("File exists", "yes", "File not found")
            return
        
        result = self.parser.parse(pdf_path)
        
        if result.get("status") != "success":
            self.log_fail("Parse success", "success", result.get("status"))
            return
        
        self.log_pass("Parse success", f"Method: {result.get('extraction_method')}")
        
        doc_type = result.get("document_type")
        if doc_type != "W-2":
            self.log_fail("Document type detection", "W-2", doc_type)
            return
        
        self.log_pass("Document type detection", f"Detected: {doc_type}")
        
        data = result.get("extracted_data", {})
        
        # Test critical fields
        print("\nCritical Fields:")
        self._test_field(data, "wages", SAMPLE_W2["expected_fields"]["wages"])
        self._test_field(data, "federal_income_tax_withheld", SAMPLE_W2["expected_fields"]["federal_income_tax_withheld"])
        
        print("\nSecondary Fields:")
        self._test_field(data, "social_security_wages", SAMPLE_W2["expected_fields"]["social_security_wages"])
        self._test_field(data, "social_security_tax_withheld", SAMPLE_W2["expected_fields"]["social_security_tax_withheld"])
        self._test_field(data, "medicare_wages", SAMPLE_W2["expected_fields"]["medicare_wages"])
        self._test_field(data, "medicare_tax_withheld", SAMPLE_W2["expected_fields"]["medicare_tax_withheld"])
        
        # Validation
        print("\nValidation:")
        validation = self.parser.validate_w2_fields(data)
        print(f"Confidence: {validation['confidence']}%")
        
        if validation["valid"]:
            self.log_pass("W-2 Validation", f"All checks passed (Confidence: {validation['confidence']}%)")
        else:
            for error in validation["errors"]:
                self.log_fail("W-2 Validation", "Valid", error)
        
        for warning in validation["warnings"]:
            self.log_warning("W-2 Validation", warning)
        
        # Test validation issues from parser
        issues = result.get("validation_issues", [])
        if issues:
            print(f"\nExtraction Issues ({len(issues)}):")
            for issue in issues:
                self.log_warning("Extraction issue", issue)
        else:
            self.log_pass("No extraction issues")
    
    def test_1099nec_extraction(self, pdf_path: str):
        """Test 1099-NEC form extraction"""
        print("\n" + "="*60)
        print("TEST: 1099-NEC Form Extraction")
        print("="*60)
        
        if not os.path.exists(pdf_path):
            self.log_fail("File exists", "yes", "File not found")
            return
        
        result = self.parser.parse(pdf_path)
        
        if result.get("status") != "success":
            self.log_fail("Parse success", "success", result.get("status"))
            return
        
        self.log_pass("Parse success", f"Method: {result.get('extraction_method')}")
        
        doc_type = result.get("document_type")
        if doc_type != "1099-NEC":
            self.log_fail("Document type detection", "1099-NEC", doc_type)
            return
        
        self.log_pass("Document type detection", f"Detected: {doc_type}")
        
        data = result.get("extracted_data", {})
        
        print("\nCritical Fields:")
        self._test_field(data, "nonemployee_compensation", SAMPLE_1099NEC["expected_fields"].get("nonemployee_compensation"))
        self._test_field(data, "federal_income_tax_withheld", SAMPLE_1099NEC["expected_fields"].get("federal_income_tax_withheld"))
        
        # Validation
        print("\nValidation:")
        validation = self.parser.validate_1099nec_fields(data)
        print(f"Confidence: {validation['confidence']}%")
        
        if validation["valid"]:
            self.log_pass("1099-NEC Validation", f"All checks passed (Confidence: {validation['confidence']}%)")
        else:
            for error in validation["errors"]:
                self.log_fail("1099-NEC Validation", "Valid", error)
    
    def test_1099int_extraction(self, pdf_path: str):
        """Test 1099-INT form extraction"""
        print("\n" + "="*60)
        print("TEST: 1099-INT Form Extraction")
        print("="*60)
        
        if not os.path.exists(pdf_path):
            self.log_fail("File exists", "yes", "File not found")
            return
        
        result = self.parser.parse(pdf_path)
        
        if result.get("status") != "success":
            self.log_fail("Parse success", "success", result.get("status"))
            return
        
        self.log_pass("Parse success", f"Method: {result.get('extraction_method')}")
        
        doc_type = result.get("document_type")
        if doc_type != "1099-INT":
            self.log_fail("Document type detection", "1099-INT", doc_type)
            return
        
        self.log_pass("Document type detection", f"Detected: {doc_type}")
        
        data = result.get("extracted_data", {})
        
        print("\nCritical Fields:")
        self._test_field(data, "interest_income", SAMPLE_1099INT["expected_fields"].get("interest_income"))
        self._test_field(data, "federal_income_tax_withheld", SAMPLE_1099INT["expected_fields"].get("federal_income_tax_withheld"))
        
        # Validation
        print("\nValidation:")
        validation = self.parser.validate_1099int_fields(data)
        print(f"Confidence: {validation['confidence']}%")
        
        if validation["valid"]:
            self.log_pass("1099-INT Validation", f"All checks passed (Confidence: {validation['confidence']}%)")
        else:
            for error in validation["errors"]:
                self.log_fail("1099-INT Validation", "Valid", error)
    
    def _test_field(self, data, field_name, expected_value):
        """Test a single field extraction"""
        actual_value = data.get(field_name)
        
        if actual_value is None:
            self.log_fail(f"{field_name}", f"${expected_value:,.2f}", "NOT EXTRACTED")
            return
        
        if isinstance(actual_value, float) and isinstance(expected_value, float):
            # For numeric fields, allow small tolerance
            tolerance = 0.01
            if abs(actual_value - expected_value) <= tolerance:
                self.log_pass(f"{field_name}", f"${actual_value:,.2f}")
            else:
                self.log_fail(f"{field_name}", f"${expected_value:,.2f}", f"${actual_value:,.2f}")
        else:
            if actual_value == expected_value:
                self.log_pass(f"{field_name}", f"{actual_value}")
            else:
                self.log_fail(f"{field_name}", f"{expected_value}", f"{actual_value}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        total = self.passed + self.failed
        print(f"Passed: {self.passed}/{total}")
        print(f"Failed: {self.failed}/{total}")
        
        if self.warnings:
            print(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")
        
        if self.failed == 0:
            print("\n✓ ALL TESTS PASSED!")
        else:
            print(f"\n✗ {self.failed} TEST(S) FAILED")
        
        return self.failed == 0

if __name__ == "__main__":
    print("="*60)
    print("TAX FORM EXTRACTION TEST SUITE")
    print("="*60)
    print("\nTesting W-2, 1099-NEC, and 1099-INT extraction")
    print("Please provide PDF file paths as arguments")
    print("\nUsage:")
    print("  python test_tax_form_extraction.py <w2.pdf> <1099nec.pdf> <1099int.pdf>")
    print("\n" + "="*60)
    
    tester = TaxFormExtractionTest()
    
    if len(sys.argv) > 1:
        # Test W-2
        if os.path.exists(sys.argv[1]):
            tester.test_w2_extraction(sys.argv[1])
        
        # Test 1099-NEC
        if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):
            tester.test_1099nec_extraction(sys.argv[2])
        
        # Test 1099-INT
        if len(sys.argv) > 3 and os.path.exists(sys.argv[3]):
            tester.test_1099int_extraction(sys.argv[3])
    else:
        print("\nNo PDF files provided. Create test files and run:")
        print("  python test_tax_form_extraction.py w2.pdf 1099nec.pdf 1099int.pdf")
    
    tester.print_summary()

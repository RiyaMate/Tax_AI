"""
Test suite for multi-form extraction functionality

Tests the new parse_multi() method that extracts all forms from a PDF
"""

import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.tax_document_parser import TaxDocumentParser, DocumentType


def test_multi_form_extraction():
    """Test extracting multiple forms from a single PDF"""
    logger.info("=" * 60)
    logger.info("TEST: Multi-Form Extraction")
    logger.info("=" * 60)
    
    parser = TaxDocumentParser()
    
    # Note: This assumes you have a multi-form PDF available
    pdf_path = "test_multi_form.pdf"
    
    try:
        result = parser.parse_multi(pdf_path)
        
        logger.info(f"\n[CHART] Extraction Results:")
        logger.info(f"Status: {result['status']}")
        logger.info(f"Total pages: {result['total_pages']}")
        logger.info(f"Forms extracted: {result['forms_extracted']}")
        
        if result['status'] == 'success':
            logger.info(f"\n📋 Forms Found:")
            
            for i, form in enumerate(result['forms'], 1):
                logger.info(f"\n  Form {i}:")
                logger.info(f"    Page: {form['page_number']}")
                logger.info(f"    Type: {form['document_type']}")
                logger.info(f"    Method: {form['extraction_method']}")
                logger.info(f"    Quality: {form['data_quality_score']}%")
                
                if form['validation_issues']:
                    logger.warning(f"    Issues: {form['validation_issues']}")
                else:
                    logger.info(f"    [YES] No validation issues")
                
                logger.info(f"    Data: {form['extracted_data']}")
            
            if result['extraction_errors']:
                logger.warning(f"\n[WARN] Errors during extraction:")
                for error in result['extraction_errors']:
                    logger.warning(f"  - {error}")
        
        return result
    
    except FileNotFoundError:
        logger.error(f"Test file not found: {pdf_path}")
        logger.info("To test, provide a multi-form PDF file")
        return None


def test_form_merging():
    """Test merging multi-page forms"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Multi-Page Form Merging")
    logger.info("=" * 60)
    
    parser = TaxDocumentParser()
    
    # Example: Simulate extracted forms from pages 1-2 (same W-2)
    simulated_forms = [
        {
            "page_number": 1,
            "document_type": "W-2",
            "extraction_method": "Donut",
            "extracted_data": {
                "wages": 50000.0,
                "federal_income_tax_withheld": 5000.0,
                "social_security_wages": None,
                "medicare_wages": None,
                "employer_ein": "12-3456789",
                "employer_name": "ACME Corp",
                "employee_ssn": "123-45-6789"
            },
            "validation_issues": ["Social security wages not found"],
            "data_quality_score": 71.4
        },
        {
            "page_number": 2,
            "document_type": "W-2",
            "extraction_method": "Donut",
            "extracted_data": {
                "wages": None,
                "federal_income_tax_withheld": None,
                "social_security_wages": 50000.0,
                "medicare_wages": 50000.0,
                "employer_ein": "12-3456789",
                "employer_name": "ACME Corp",
                "employee_ssn": "123-45-6789"
            },
            "validation_issues": [],
            "data_quality_score": 57.1
        },
        {
            "page_number": 3,
            "document_type": "1099-NEC",
            "extraction_method": "Donut",
            "extracted_data": {
                "nonemployee_compensation": 25000.0,
                "federal_income_tax_withheld": 2500.0,
                "payer_name": "XYZ Consulting",
                "payer_ein": "98-7654321",
                "recipient_tin": "123-45-6789"
            },
            "validation_issues": [],
            "data_quality_score": 100.0
        }
    ]
    
    logger.info(f"\nBefore merge: {len(simulated_forms)} forms")
    for form in simulated_forms:
        logger.info(f"  Page {form['page_number']}: {form['document_type']}")
    
    merged_forms = parser.merge_multipage_forms(simulated_forms)
    
    logger.info(f"\nAfter merge: {len(merged_forms)} forms")
    for form in merged_forms:
        page_info = form.get('page_number', 'merged')
        logger.info(f"  Page {page_info}: {form['document_type']}")
        logger.info(f"    Data: {form['extracted_data']}")
    
    return merged_forms


def test_data_quality_scoring():
    """Test data quality score calculation"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Data Quality Scoring")
    logger.info("=" * 60)
    
    parser = TaxDocumentParser()
    
    # Test 1: Complete W-2 data
    w2_complete = {
        "wages": 50000.0,
        "federal_income_tax_withheld": 5000.0,
        "social_security_wages": 50000.0,
        "medicare_wages": 50000.0,
        "employer_ein": "12-3456789",
        "employer_name": "ACME Corp",
        "employee_ssn": "123-45-6789"
    }
    score1 = parser._calculate_data_quality(w2_complete, DocumentType.W2)
    logger.info(f"Complete W-2: {score1}% (expected 100%)")
    
    # Test 2: Partial W-2 data
    w2_partial = {
        "wages": 50000.0,
        "federal_income_tax_withheld": None,
        "social_security_wages": None,
        "medicare_wages": None,
        "employer_ein": None,
        "employer_name": None,
        "employee_ssn": "123-45-6789"
    }
    score2 = parser._calculate_data_quality(w2_partial, DocumentType.W2)
    logger.info(f"Partial W-2: {score2}% (expected ~28%)")
    
    # Test 3: Complete 1099-NEC data
    nec_complete = {
        "nonemployee_compensation": 25000.0,
        "federal_income_tax_withheld": 2500.0,
        "payer_name": "XYZ Consulting",
        "payer_ein": "98-7654321",
        "recipient_tin": "123-45-6789"
    }
    score3 = parser._calculate_data_quality(nec_complete, DocumentType.FORM_1099_NEC)
    logger.info(f"Complete 1099-NEC: {score3}% (expected 100%)")
    
    # Test 4: Empty data
    score4 = parser._calculate_data_quality({}, DocumentType.W2)
    logger.info(f"Empty data: {score4}% (expected 0%)")


def test_form_type_detection():
    """Test document type detection"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Document Type Detection")
    logger.info("=" * 60)
    
    parser = TaxDocumentParser()
    
    # Test cases
    test_cases = [
        ("Form W-2 Wage and Tax Statement Box 1 Wages: $50,000", DocumentType.W2),
        ("1099-NEC Nonemployee Compensation Box 1: $25,000", DocumentType.FORM_1099_NEC),
        ("Form 1099-INT Interest Income Box 1: $500", DocumentType.FORM_1099_INT),
        ("Some random text with no form", DocumentType.UNKNOWN),
    ]
    
    for text, expected_type in test_cases:
        detected_type = parser.detect_document_type(text)
        status = "[YES]" if detected_type == expected_type else "[FAIL]"
        logger.info(f"{status} Text: '{text[:40]}...'")
        logger.info(f"   Expected: {expected_type.value}, Got: {detected_type.value}")


def main():
    """Run all tests"""
    logger.info("\n🧪 MULTI-FORM EXTRACTION TEST SUITE\n")
    
    # Test 1: Form type detection
    test_form_type_detection()
    
    # Test 2: Data quality scoring
    test_data_quality_scoring()
    
    # Test 3: Multi-page form merging
    test_form_merging()
    
    # Test 4: Multi-form extraction (requires actual PDF)
    result = test_multi_form_extraction()
    
    logger.info("\n" + "=" * 60)
    logger.info("[YES] Test suite completed")
    logger.info("=" * 60 + "\n")


if __name__ == "__main__":
    main()

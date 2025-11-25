import logging
import re
from typing import Dict, Any, List, Optional
from enum import Enum
from decimal import Decimal
import pdfplumber
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os
from pathlib import Path
import json

# LandingAI imports
try:
    from llm_extractor.landingai_processor import LandingAIDocumentProcessor
    LANDINGAI_AVAILABLE = True
except ImportError:
    LANDINGAI_AVAILABLE = False
    logging.warning("LandingAI not available. Will use fallback extraction methods.")

# Donut imports
try:
    from transformers import DonutProcessor, VisionEncoderDecoderModel
    DONUT_AVAILABLE = True
except ImportError:
    DONUT_AVAILABLE = False
    logging.warning("Donut model not available. Install: pip install transformers")

# Configure logging
logger = logging.getLogger(__name__)

class DocumentType(Enum):
    W2 = "W-2"
    FORM_1099_MISC = "1099-MISC"
    FORM_1099_NEC = "1099-NEC"
    FORM_1099_INT = "1099-INT"
    UNKNOWN = "UNKNOWN"

class TaxDocumentParser:
    """Parse tax documents and extract relevant fields using Donut + fallback OCR"""
    
    def __init__(self):
        self.doc_type_patterns = {
            DocumentType.FORM_1099_MISC: [r"1099[\s-]?misc", r"miscellaneous\s+income", r"form\s+1099[\s-]?misc", r"royalties", r"nonemployee compensation.*box 7"],
            DocumentType.W2: [r"w[\s-]?2", r"form\s+w[\s-]?2", r"wage\s+and\s+tax", r"box\s+1[\s]*wages"],
            DocumentType.FORM_1099_NEC: [r"1099[\s-]?nec", r"nonemployee\s+compensation", r"form\s+1099[\s-]?nec"],
            DocumentType.FORM_1099_INT: [r"1099[\s-]?int", r"interest\s+income", r"form\s+1099[\s-]?int"],
        }
        
        # Initialize Donut model for document understanding
        self.donut_processor = None
        self.donut_model = None
        self.use_donut = DONUT_AVAILABLE
        
        if DONUT_AVAILABLE:
            try:
                logger.info("Initializing Donut model for document understanding...")
                self.donut_processor = DonutProcessor.from_pretrained("naver-clova-ix/donut-base-finetuned-rvlcdip")
                self.donut_model = VisionEncoderDecoderModel.from_pretrained("naver-clova-ix/donut-base-finetuned-rvlcdip")
                logger.info("[YES] Donut model loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load Donut model: {e}. Will use fallback OCR.")
                self.use_donut = False
        
        # Field patterns for extraction (fallback for when Donut unavailable)
        # Improved patterns to match exact box numbers and amounts more reliably
        self.w2_fields = {
            "wages": r"(?:Box\s*1|1\s+Wages)[\s\$]*([0-9,]+(?:\.\d{2})?)",
            "federal_income_tax_withheld": r"(?:Box\s*2|2\s+Federal)[\s\$]*([0-9,]+(?:\.\d{2})?)",
            "social_security_wages": r"(?:Box\s*3|3\s+Social)[\s\$]*([0-9,]+(?:\.\d{2})?)",
            "medicare_wages": r"(?:Box\s*5|5\s+Medicare)[\s\$]*([0-9,]+(?:\.\d{2})?)",
            "employer_ein": r"EIN.*?(\d{2}-\d{7})",
            "employer_name": r"employer.*?:\s*([^\n]+)",
            "employee_ssn": r"SSN.*?(\d{3}-\d{2}-\d{4})",
        }
        
        self.form_1099_misc_fields = {
            "nonemployee_compensation": r"(?:Box\s*7|7\s+Nonemployee)[\s\$]*([0-9,]+(?:\.\d{2})?)",
            "federal_income_tax_withheld": r"(?:Box\s*4|4\s+Federal)[\s\$]*([0-9,]+(?:\.\d{2})?)",
            "rents": r"(?:Box\s*1|1\s+Rents)[\s\$]*([0-9,]+(?:\.\d{2})?)",
            "royalties": r"(?:Box\s*2|2\s+Royalties)[\s\$]*([0-9,]+(?:\.\d{2})?)",
            "payer_name": r"payer.*?:\s*([^\n]+)",
            "payer_ein": r"payer\s+(?:federal\s+)?identification\s+number.*?(\d{2}-\d{7})",
            "recipient_tin": r"recipient.*?identification\s+number.*?(\d{3}-\d{2}-\d{4})",
        }
        
        self.form_1099_nec_fields = {
            "nonemployee_compensation": r"(?:Box\s*1|1\s+Nonemployee)[\s\$]*([0-9,]+(?:\.\d{2})?)",
            "federal_income_tax_withheld": r"(?:Box\s*4|4\s+Federal)[\s\$]*([0-9,]+(?:\.\d{2})?)",
            "payer_name": r"payer.*?:\s*([^\n]+)",
            "payer_ein": r"payer\s+ein.*?(\d{2}-\d{7})",
            "recipient_tin": r"recipient\s+tin.*?(\d{3}-\d{2}-\d{4})",
        }
        
        self.form_1099_int_fields = {
            "interest_income": r"(?:Box\s*1|1\s+Interest)[\s\$]*([0-9,]+(?:\.\d{2})?)",
            "federal_income_tax_withheld": r"(?:Box\s*4|4\s+Federal)[\s\$]*([0-9,]+(?:\.\d{2})?)",
            "payer_name": r"payer.*?:\s*([^\n]+)",
            "payer_tin": r"payer\s+tin.*?(\d{2}-\d{7})",
            "recipient_tin": r"recipient\s+tin.*?(\d{3}-\d{2}-\d{4})",
        }
    
    def detect_document_type(self, text: str) -> DocumentType:
        """Detect document type from text content"""
        text_lower = text.lower()
        
        for doc_type, patterns in self.doc_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    logger.info(f"Detected document type: {doc_type.value}")
                    return doc_type
        
        logger.warning("Could not determine document type, marking as UNKNOWN")
        return DocumentType.UNKNOWN
    
    def extract_currency(self, text: str) -> float:
        """Extract currency value from text"""
        if not text:
            return 0.0
        
        # Remove common currency symbols and commas
        text = re.sub(r'[$,\s]', '', text)
        
        try:
            return float(text)
        except ValueError:
            logger.warning(f"Could not convert '{text}' to float")
            return 0.0
    
    def extract_with_donut(self, image_path: str, doc_type: DocumentType) -> Optional[Dict[str, Any]]:
        """Extract structured data from tax form image using Donut model
        
        Donut is a DOcument Understanding TRansformer that directly reads documents
        without needing OCR. It understands layout, boxes, and context.
        
        Returns structured output like:
        {
            "wages": "56000.00",
            "tax_withheld": "6500.00",
            "ein": "12-3456789",
            ...
        }
        """
        if not self.use_donut or not self.donut_model or not self.donut_processor:
            return None
        
        try:
            logger.info(f"Extracting from {doc_type.value} using Donut vision model...")
            
            # Open image
            image = Image.open(image_path).convert("RGB")
            
            # Prepare task prompt based on document type
            task_prompts = {
                DocumentType.W2: "<s_rvlcdip>W-2 Form</s_rvlcdip>",
                DocumentType.FORM_1099_NEC: "<s_rvlcdip>1099-NEC Form</s_rvlcdip>",
                DocumentType.FORM_1099_INT: "<s_rvlcdip>1099-INT Form</s_rvlcdip>",
            }
            
            task_prompt = task_prompts.get(doc_type, "<s_rvlcdip>Tax Form</s_rvlcdip>")
            
            # Process image with Donut
            pixel_values = self.donut_processor(image, return_tensors="pt").pixel_values
            
            # Generate structured output
            decoder_input_ids = self.donut_processor.tokenizer(
                task_prompt, 
                add_special_tokens=False, 
                return_tensors="pt"
            ).input_ids
            
            # Get model predictions
            outputs = self.donut_model.generate(
                pixel_values,
                decoder_input_ids=decoder_input_ids,
                max_length=1024,
                early_stopping=True,
                pad_token_id=self.donut_processor.tokenizer.pad_token_id,
                eos_token_id=self.donut_processor.tokenizer.eos_token_id,
                use_cache=True,
                num_beams=1,
                bad_words_ids=[[self.donut_processor.tokenizer.unk_token_id]],
            )
            
            # Decode output
            sequence = self.donut_processor.batch_decode(outputs.sequences)[0]
            sequence = sequence.replace(self.donut_processor.tokenizer.eos_token, "").replace(task_prompt, "").strip()
            
            logger.info(f"Donut extracted: {sequence[:200]}...")
            
            # Parse JSON output if available
            try:
                extracted_data = json.loads(sequence)
                logger.info("[YES] Donut successfully extracted structured data")
                return extracted_data
            except json.JSONDecodeError:
                logger.warning(f"Donut output not valid JSON: {sequence[:100]}")
                return None
        
        except Exception as e:
            logger.warning(f"Donut extraction failed: {e}. Will fall back to OCR.")
            return None
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using LandingAI (primary), then pdfplumber, then OCR as fallback
        
        Strategy:
        1. Try LandingAI (best for scanned forms)
        2. Try pdfplumber (good for digital PDFs)
        3. Fall back to OCR (when others fail)
        """
        text = ""
        extraction_method = "None"
        
        # Try LandingAI first for best accuracy on tax forms
        if LANDINGAI_AVAILABLE:
            try:
                logger.info(f"Attempting LandingAI extraction for {pdf_path}")
                processor = LandingAIDocumentProcessor()
                result = processor.parse_document(Path(pdf_path))
                
                if result.get("status") == "success":
                    chunks = result.get("chunks", [])
                    text = "\n".join([chunk.get("text", "") for chunk in chunks])
                    extraction_method = "LandingAI"
                    logger.info(f"[YES] LandingAI extraction successful ({len(text)} chars)")
                    return text
            except Exception as e:
                logger.warning(f"LandingAI extraction failed: {e}. Falling back to pdfplumber.")
        
        # Try pdfplumber second
        try:
            logger.info(f"Attempting pdfplumber extraction for {pdf_path}")
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            
            if len(text.strip()) > 100:
                extraction_method = "pdfplumber"
                logger.info(f"[YES] pdfplumber extraction successful ({len(text)} chars)")
                return text
        
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
        
        # Fall back to OCR
        logger.info("Text extraction insufficient, attempting OCR...")
        text = self._ocr_pdf(pdf_path)
        extraction_method = "OCR"
        
        return text
    
    def extract_text_from_page(self, pdf_path: str, page_number: int) -> str:
        """Extract text from a specific page using LandingAI (primary), then pdfplumber/OCR as fallback"""
        text = ""
        
        # Try LandingAI first for best accuracy
        if LANDINGAI_AVAILABLE:
            try:
                logger.info(f"Attempting LandingAI extraction for page {page_number}")
                processor = LandingAIDocumentProcessor()
                result = processor.parse_document(Path(pdf_path))
                
                if result.get("status") == "success":
                    chunks = result.get("chunks", [])
                    # Filter for requested page
                    page_chunks = [c for c in chunks if c.get("page_number") == page_number + 1]
                    if page_chunks:
                        text = "\n".join([chunk.get("text", "") for chunk in page_chunks])
                        logger.info(f"[YES] LandingAI page extraction successful ({len(text)} chars)")
                        return text
            except Exception as e:
                logger.warning(f"LandingAI page extraction failed: {e}. Falling back to pdfplumber.")
        
        # Try pdfplumber for single page
        try:
            logger.info(f"Attempting pdfplumber extraction for page {page_number}")
            with pdfplumber.open(pdf_path) as pdf:
                if page_number < len(pdf.pages):
                    page = pdf.pages[page_number]
                    text = page.extract_text() or ""
                    
                    if len(text.strip()) > 50:
                        logger.info(f"[YES] pdfplumber page extraction successful ({len(text)} chars)")
                        return text
        
        except Exception as e:
            logger.warning(f"pdfplumber extraction for page {page_number} failed: {e}")
        
        # If insufficient text, use OCR on that page
        logger.info(f"Text extraction insufficient for page {page_number}, attempting OCR...")
        text = self._ocr_single_page(pdf_path, page_number)
        
        return text
    
    def pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """Convert PDF pages to PIL images for Donut processing"""
        images = []
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Higher resolution for better Donut recognition
                pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5))
                image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(image)
            logger.info(f"Converted {len(images)} PDF pages to images")
        except Exception as e:
            logger.error(f"PDF to image conversion failed: {e}")
        
        return images
    
    def _ocr_pdf(self, pdf_path: str) -> str:
        """Extract text using OCR (Tesseract)"""
        text = ""
        try:
            # Convert PDF to images and run OCR
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
                image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                page_text = pytesseract.image_to_string(image)
                text += page_text + "\n"
            
            logger.info("OCR extraction completed")
        
        except Exception as e:
            logger.error(f"OCR failed: {e}")
        
        return text
    
    def _ocr_single_page(self, pdf_path: str, page_number: int) -> str:
        """Extract text from single page using OCR (Tesseract)"""
        text = ""
        try:
            doc = fitz.open(pdf_path)
            if page_number < len(doc):
                page = doc[page_number]
                pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5))  # 2.5x zoom for better recognition
                image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text = pytesseract.image_to_string(image)
                logger.info(f"OCR extraction completed for page {page_number}")
        
        except Exception as e:
            logger.error(f"OCR failed for page {page_number}: {e}")
        
        return text
    
    def extract_fields(self, text: str, doc_type: DocumentType, image_path: Optional[str] = None) -> Dict[str, Any]:
        """Extract specific fields using Donut (preferred) or regex patterns (fallback)
        
        Returns LandingAI field names:
        - W-2: wages, federal_income_tax_withheld, social_security_wages, social_security_tax_withheld, medicare_wages, medicare_tax_withheld
        - 1099-NEC: nonemployee_compensation, federal_income_tax_withheld
        - 1099-INT: interest_income, federal_income_tax_withheld
        
        Strategy:
        1. Try Donut (best accuracy for tax forms)
        2. Fall back to regex patterns if Donut unavailable
        """
        extracted = {}
        
        # Try Donut first if we have an image path
        if image_path and self.use_donut:
            donut_results = self.extract_with_donut(image_path, doc_type)
            if donut_results:
                extracted.update(donut_results)
                logger.info(f"[YES] Using Donut extraction: {list(extracted.keys())}")
                return extracted
        
        # Fallback to regex-based extraction
        logger.info("Using regex-based field extraction (Donut not available)")
        
        if doc_type == DocumentType.W2:
            field_patterns = self.w2_fields
        elif doc_type == DocumentType.FORM_1099_MISC:
            field_patterns = self.form_1099_misc_fields
        elif doc_type == DocumentType.FORM_1099_NEC:
            field_patterns = self.form_1099_nec_fields
        elif doc_type == DocumentType.FORM_1099_INT:
            field_patterns = self.form_1099_int_fields
        else:
            logger.warning("Unknown document type, skipping field extraction")
            return extracted
        
        for field_name, pattern in field_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            
            if match:
                value = match.group(1).strip()
                
                # Convert to float if it's a currency field
                if any(currency_term in field_name.lower() for currency_term in ['wages', 'compensation', 'income', 'withheld']):
                    extracted[field_name] = self.extract_currency(value)
                else:
                    extracted[field_name] = value
                
                logger.info(f"Extracted {field_name}: {extracted[field_name]}")
            
            else:
                if any(currency_term in field_name.lower() for currency_term in ['wages', 'compensation', 'income', 'withheld']):
                    extracted[field_name] = 0.0
                else:
                    extracted[field_name] = None
                
                logger.warning(f"Field not found: {field_name}")
        
        return extracted
    
    def validate_extracted_data(self, data: Dict[str, Any], doc_type: DocumentType) -> List[str]:
        """Validate extracted data and return list of issues
        
        Uses LandingAI field names:
        - W-2: wages, federal_income_tax_withheld, employee_ssn
        - 1099-MISC: nonemployee_compensation (Box 7), federal_income_tax_withheld, recipient_tin
        - 1099-NEC: nonemployee_compensation, federal_income_tax_withheld, recipient_tin
        - 1099-INT: interest_income, federal_income_tax_withheld, recipient_tin
        """
        issues = []
        
        # Check for required fields
        if doc_type == DocumentType.W2:
            if not data.get("wages") or data.get("wages") == 0.0:
                issues.append("W-2: wages (wage and tax statement box 1) not found or is $0")
            if not data.get("employee_ssn"):
                issues.append("W-2: employee_ssn not found")
        
        elif doc_type == DocumentType.FORM_1099_MISC:
            if not data.get("nonemployee_compensation") or data.get("nonemployee_compensation") == 0.0:
                issues.append("1099-MISC: nonemployee_compensation (box 7) not found or is $0")
            if not data.get("recipient_tin"):
                issues.append("1099-MISC: recipient_tin not found")
        
        elif doc_type == DocumentType.FORM_1099_NEC:
            if not data.get("nonemployee_compensation") or data.get("nonemployee_compensation") == 0.0:
                issues.append("1099-NEC: nonemployee_compensation (box 1) not found or is $0")
            if not data.get("recipient_tin"):
                issues.append("1099-NEC: recipient_tin not found")
        
        elif doc_type == DocumentType.FORM_1099_INT:
            if not data.get("interest_income") or data.get("interest_income") == 0.0:
                issues.append("1099-INT: interest_income (box 1) not found or is $0")
            if not data.get("recipient_tin"):
                issues.append("1099-INT: recipient_tin not found")
        
        return issues
    
    def validate_w2_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate W-2 specific fields with confidence scoring
        
        Uses LandingAI field names:
        - wages: W-2 Box 1 (Wages, tips, other compensation)
        - federal_income_tax_withheld: W-2 Box 2 (Federal income tax withheld)
        - social_security_wages: W-2 Box 3 (Social Security wages)
        - social_security_tax_withheld: W-2 Box 4 (Social Security tax withheld)
        - medicare_wages: W-2 Box 5 (Medicare wages and tips)
        - medicare_tax_withheld: W-2 Box 6 (Medicare tax withheld)
        """
        validation = {
            "valid": True,
            "confidence": 100,
            "errors": [],
            "warnings": []
        }
        
        wages = data.get("wages", 0.0)
        fed_withheld = data.get("federal_income_tax_withheld", 0.0)
        ss_wages = data.get("social_security_wages", 0.0)
        ss_tax = data.get("social_security_tax_withheld", 0.0)
        medicare_wages = data.get("medicare_wages", 0.0)
        medicare_tax = data.get("medicare_tax_withheld", 0.0)
        
        # Critical checks
        if wages <= 0:
            validation["errors"].append("Wages (Box 1) must be > $0")
            validation["valid"] = False
        
        if fed_withheld > wages:
            validation["errors"].append(f"Federal withheld (${fed_withheld}) cannot exceed wages (${wages})")
            validation["valid"] = False
        
        # Consistency checks
        if ss_wages and abs(ss_wages - wages) > 100:
            validation["warnings"].append(f"SS Wages (${ss_wages}) differs from Wages (${wages}) by >${100}")
        
        if ss_tax and wages:
            expected_ss_tax = wages * 0.062
            if abs(ss_tax - expected_ss_tax) > 50:
                validation["warnings"].append(f"SS Tax (${ss_tax}) doesn't match expected (${expected_ss_tax:.2f})")
        
        if medicare_tax and wages:
            expected_medicare_tax = wages * 0.0145
            if abs(medicare_tax - expected_medicare_tax) > 10:
                validation["warnings"].append(f"Medicare Tax (${medicare_tax}) doesn't match expected (${expected_medicare_tax:.2f})")
        
        # Confidence adjustment
        if validation["warnings"]:
            validation["confidence"] = 85
        if validation["errors"]:
            validation["confidence"] = 40
        
        return validation
    
    def validate_1099nec_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate 1099-NEC specific fields with confidence scoring
        
        Uses LandingAI field names:
        - nonemployee_compensation: 1099-NEC Box 1 (Nonemployee Compensation)
        - federal_income_tax_withheld: 1099-NEC Box 4 (Federal income tax withheld)
        """
        validation = {
            "valid": True,
            "confidence": 100,
            "errors": [],
            "warnings": []
        }
        
        compensation = data.get("nonemployee_compensation", 0.0)
        fed_withheld = data.get("federal_income_tax_withheld", 0.0)
        
        if compensation <= 0:
            validation["errors"].append("Nonemployee Compensation (Box 1) must be > $0")
            validation["valid"] = False
        
        if fed_withheld > compensation:
            validation["errors"].append(f"Federal withheld (${fed_withheld}) cannot exceed compensation (${compensation})")
            validation["valid"] = False
        
        if validation["warnings"]:
            validation["confidence"] = 90
        if validation["errors"]:
            validation["confidence"] = 40
        
        return validation
    
    def validate_1099int_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate 1099-INT specific fields with confidence scoring
        
        Uses LandingAI field names:
        - interest_income: 1099-INT Box 1 (Interest Income)
        - federal_income_tax_withheld: 1099-INT Box 4 (Federal income tax withheld)
        """
        validation = {
            "valid": True,
            "confidence": 100,
            "errors": [],
            "warnings": []
        }
        
        interest = data.get("interest_income", 0.0)
        fed_withheld = data.get("federal_income_tax_withheld", 0.0)
        
        if interest <= 0:
            validation["errors"].append("Interest Income (Box 1) must be > $0")
            validation["valid"] = False
        
        if fed_withheld > interest:
            validation["errors"].append(f"Federal withheld (${fed_withheld}) cannot exceed interest (${interest})")
            validation["valid"] = False
        
        if validation["warnings"]:
            validation["confidence"] = 90
        if validation["errors"]:
            validation["confidence"] = 40
        
        return validation
    
    def parse(self, pdf_path: str) -> Dict[str, Any]:
        """Parse a tax document using LandingAI (primary) + Donut (secondary) + OCR (fallback)
        
        Returns extracted data using LandingAI field names:
        - W-2: wages, federal_income_tax_withheld, social_security_wages, social_security_tax_withheld, medicare_wages, medicare_tax_withheld
        - 1099-NEC: nonemployee_compensation, federal_income_tax_withheld
        - 1099-INT: interest_income, federal_income_tax_withheld
        
        Extraction Strategy:
        1. Convert PDF to images (for vision models)
        2. Detect document type
        3. Extract with LandingAI (primary) - 95-100% accuracy
        4. Extract with Donut (secondary) - direct visual understanding
        5. Fall back to OCR + regex if others unavailable
        6. Validate extracted data
        """
        logger.info(f"Starting to parse document: {pdf_path}")
        
        try:
            # Extract text for type detection
            text = self.extract_text_from_pdf(pdf_path)
            
            # Detect document type
            doc_type = self.detect_document_type(text)
            
            # Convert PDF to images for Donut processing
            image_path = None
            images = self.pdf_to_images(pdf_path)
            if images:
                # Use first page for extraction
                image_path = images[0]
                logger.info(f"Converted PDF to {len(images)} image(s)")
            
            # Extract fields (Donut primary, regex fallback)
            extracted_data = self.extract_fields(text, doc_type, image_path)
            
            # Validate data
            validation_issues = self.validate_extracted_data(extracted_data, doc_type)
            
            # Report extraction method used
            extraction_method = "Donut" if (image_path and self.use_donut and extracted_data) else "Regex+OCR"
            
            result = {
                "status": "success",
                "document_type": doc_type.value,
                "extracted_data": extracted_data,
                "validation_issues": validation_issues,
                "extraction_method": extraction_method,
                "text_preview": text[:500]  # First 500 chars for debugging
            }
            
            logger.info(f"[YES] Successfully parsed document using {extraction_method}")
            return result
        
        except Exception as e:
            logger.error(f"Error parsing document {pdf_path}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "document_type": "UNKNOWN"
            }
    
    def parse_multi(self, pdf_path: str) -> Dict[str, Any]:
        """Parse MULTI-FORM PDFs - Extract ALL forms in a PDF file
        
        Returns extracted data using LandingAI field names
        
        Supports:
        - Multiple W-2s from different employers
        - Multiple 1099-NECs
        - Multiple 1099-INTs
        - Mixed forms (W-2 + 1099 + 1099-INT in same PDF)
        - Scanned multipage PDFs
        - Concatenated tax documents
        
        Returns:
        {
            "status": "success",
            "total_pages": 5,
            "total_forms_extracted": 3,
            "forms": [
                {
                    "page_number": 1,
                    "document_type": "W-2",
                    "extraction_method": "LandingAI",
                    "extracted_data": {
                        "wages": 50000.0,
                        "federal_income_tax_withheld": 6000.0,
                        ...
                    },
                    "validation_issues": []
                },
                ...
            ]
        }
        """
        logger.info(f"🔄 Starting multi-form extraction from: {pdf_path}")
        
        results = []
        extraction_errors = []
        
        try:
            # Open PDF and get total pages
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            logger.info(f"PDF contains {total_pages} pages")
            
            # Process each page
            for page_number in range(total_pages):
                try:
                    logger.info(f"Processing page {page_number + 1}/{total_pages}...")
                    
                    page = doc[page_number]
                    
                    # Convert page to image (2.5x zoom for better recognition)
                    pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5))
                    pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
                    # Extract text from this page only
                    page_text = self.extract_text_from_page(pdf_path, page_number)
                    
                    # Detect document type for this page
                    doc_type = self.detect_document_type(page_text)
                    
                    # Skip UNKNOWN pages (don't clutter results)
                    if doc_type == DocumentType.UNKNOWN:
                        logger.warning(f"Page {page_number + 1}: Could not determine document type, skipping")
                        continue
                    
                    logger.info(f"Page {page_number + 1}: Detected {doc_type.value}")
                    
                    # Extract fields for this page
                    extracted_data = self.extract_fields(page_text, doc_type, pil_img)
                    
                    # Validate extracted data
                    validation_issues = self.validate_extracted_data(extracted_data, doc_type)
                    
                    # Determine extraction method used
                    extraction_method = "Donut" if (self.use_donut and any(extracted_data.values())) else "Regex+OCR"
                    
                    # Store result
                    form_result = {
                        "page_number": page_number + 1,
                        "document_type": doc_type.value,
                        "extraction_method": extraction_method,
                        "extracted_data": extracted_data,
                        "validation_issues": validation_issues,
                        "data_quality_score": self._calculate_data_quality(extracted_data, doc_type)
                    }
                    
                    results.append(form_result)
                    logger.info(f"[YES] Extracted {doc_type.value} from page {page_number + 1}")
                
                except Exception as page_error:
                    error_msg = f"Page {page_number + 1}: {str(page_error)}"
                    logger.error(error_msg)
                    extraction_errors.append(error_msg)
            
            doc.close()
            
            # Final report
            success_count = len(results)
            logger.info(f"[YES] Multi-form extraction complete: {success_count} forms extracted from {total_pages} pages")
            
            return {
                "status": "success",
                "total_pages": total_pages,
                "forms_extracted": success_count,
                "forms": results,
                "extraction_errors": extraction_errors if extraction_errors else None,
                "pdf_path": pdf_path
            }
        
        except Exception as e:
            logger.error(f"Multi-form extraction failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "total_pages": 0,
                "forms_extracted": 0,
                "forms": [],
                "extraction_errors": extraction_errors
            }
    
    def _calculate_data_quality(self, extracted_data: Dict[str, Any], doc_type: DocumentType) -> float:
        """Calculate data quality score (0-100) based on populated fields"""
        if not extracted_data:
            return 0.0
        
        total_fields = 0
        populated_fields = 0
        
        if doc_type == DocumentType.W2:
            total_fields = 7  # wages, tax_withheld, ss_wages, medicare_wages, ein, employer, ssn
        elif doc_type == DocumentType.FORM_1099_NEC:
            total_fields = 5  # compensation, tax_withheld, payer_name, payer_ein, recipient_tin
        elif doc_type == DocumentType.FORM_1099_INT:
            total_fields = 5  # interest_income, tax_withheld, payer_name, payer_tin, recipient_tin
        else:
            return 0.0
        
        for value in extracted_data.values():
            if value and value != 0.0 and value != "UNKNOWN":
                populated_fields += 1
        
        quality_score = (populated_fields / total_fields * 100) if total_fields > 0 else 0.0
        return round(quality_score, 2)
    
    def merge_multipage_forms(self, forms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge multi-page forms (e.g., W-2 split across pages 1-2)
        
        Detects forms with same identifiers and merges them:
        - Same EIN (employer identification number)
        - Same SSN (employee identification)
        - Same payer name
        
        Returns merged form list where multi-page forms are combined
        """
        if not forms:
            return []
        
        merged = []
        used_indices = set()
        
        for i, form1 in enumerate(forms):
            if i in used_indices:
                continue
            
            current_form = form1.copy()
            
            # Try to find matching forms to merge
            for j in range(i + 1, len(forms)):
                if j in used_indices:
                    continue
                
                form2 = forms[j]
                
                # Check if same document type
                if form1["document_type"] != form2["document_type"]:
                    continue
                
                # Check for matching identifiers
                data1 = form1.get("extracted_data", {})
                data2 = form2.get("extracted_data", {})
                
                # W-2 matching: same EIN and SSN
                if form1["document_type"] == "W-2":
                    if (data1.get("employer_ein") == data2.get("employer_ein") and
                        data1.get("employee_ssn") == data2.get("employee_ssn")):
                        
                        # Merge: prefer non-zero/non-None values from form2
                        merged_data = current_form["extracted_data"].copy()
                        for key, val in data2.items():
                            if val and val != 0.0 and not merged_data.get(key):
                                merged_data[key] = val
                        
                        current_form["extracted_data"] = merged_data
                        current_form["page_number"] = f"{form1['page_number']}-{form2['page_number']}"
                        used_indices.add(j)
                        logger.info(f"Merged W-2s from pages {form1['page_number']} and {form2['page_number']}")
                
                # 1099-NEC matching: same payer EIN and recipient TIN
                elif form1["document_type"] == "1099-NEC":
                    if (data1.get("payer_ein") == data2.get("payer_ein") and
                        data1.get("recipient_tin") == data2.get("recipient_tin")):
                        
                        merged_data = current_form["extracted_data"].copy()
                        for key, val in data2.items():
                            if val and val != 0.0 and not merged_data.get(key):
                                merged_data[key] = val
                        
                        current_form["extracted_data"] = merged_data
                        current_form["page_number"] = f"{form1['page_number']}-{form2['page_number']}"
                        used_indices.add(j)
                        logger.info(f"Merged 1099-NECs from pages {form1['page_number']} and {form2['page_number']}")
                
                # 1099-INT matching: same payer TIN and recipient TIN
                elif form1["document_type"] == "1099-INT":
                    if (data1.get("payer_tin") == data2.get("payer_tin") and
                        data1.get("recipient_tin") == data2.get("recipient_tin")):
                        
                        merged_data = current_form["extracted_data"].copy()
                        for key, val in data2.items():
                            if val and val != 0.0 and not merged_data.get(key):
                                merged_data[key] = val
                        
                        current_form["extracted_data"] = merged_data
                        current_form["page_number"] = f"{form1['page_number']}-{form2['page_number']}"
                        used_indices.add(j)
                        logger.info(f"Merged 1099-INTs from pages {form1['page_number']} and {form2['page_number']}")
            
            merged.append(current_form)
        
        logger.info(f"Form merging complete: {len(forms)} pages → {len(merged)} forms")
        return merged

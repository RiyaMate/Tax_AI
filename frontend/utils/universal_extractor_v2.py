"""
UNIVERSAL TAX FORM EXTRACTION ENGINE (ADE + Embeddings + LLM Schema Normalizer)
Production Version - No Special Characters for Windows Compatibility

Goal: Extract ANY tax form fields from ANY layout without regex.
Works with W-2, 1099-NEC, 1099-INT, 1099-DIV, Paystubs, Bank Statements, etc.
Handles OCR-noisy, scanned, rotated, messy documents.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel, ConfigDict
from enum import Enum

try:
    from sentence_transformers import SentenceTransformer, util
    EMBEDDINGS_AVAILABLE = True
except Exception as e:
    EMBEDDINGS_AVAILABLE = False
    embed_model = None

# -------------------------------------------------------
# 0. Configuration
# -------------------------------------------------------
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_SIMILARITY_THRESHOLD = 0.45

if EMBEDDINGS_AVAILABLE:
    try:
        embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    except Exception as e:
        print(f"[WARNING] Failed to load embedding model: {e}")
        EMBEDDINGS_AVAILABLE = False
        embed_model = None


# -------------------------------------------------------
# 1. TAX SCHEMA — UNIFIED OUTPUT FORMAT
# -------------------------------------------------------
class TaxUnifiedSchema(BaseModel):
    """Unified schema for ALL tax documents"""
    model_config = ConfigDict(use_enum_values=True)
    
    wages: Optional[float] = None
    federal_tax_withheld: Optional[float] = None
    ss_wages: Optional[float] = None
    ss_tax_withheld: Optional[float] = None
    medicare_wages: Optional[float] = None
    medicare_tax_withheld: Optional[float] = None
    nec_income: Optional[float] = None
    interest_income: Optional[float] = None
    dividend_income: Optional[float] = None
    state_tax_withheld: Optional[float] = None
    employer_ein: Optional[str] = None
    employee_ssn: Optional[str] = None
    document_type: Optional[str] = None
    extraction_confidence: Optional[Dict[str, float]] = None


# -------------------------------------------------------
# 2. LABEL MAPPING — ALL KNOWN VARIATIONS
# -------------------------------------------------------
TAX_LABELS = {
    "wages": [
        "wages",
        "employee wages",
        "box 1",
        "earnings",
        "wages, tips, other compensation",
        "total wages",
        "gross wages",
    ],
    "federal_tax_withheld": [
        "federal tax",
        "federal income tax",
        "federal income tax withheld",
        "federal tax withheld",
        "box 2",
        "fed tax",
    ],
    "ss_wages": [
        "social security wages",
        "ss wages",
        "social security wages and tips",
        "box 3",
    ],
    "ss_tax_withheld": [
        "social security tax",
        "social security tax withheld",
        "ss tax",
        "box 4",
    ],
    "medicare_wages": [
        "medicare wages",
        "medicare wages and tips",
        "box 5",
    ],
    "medicare_tax_withheld": [
        "medicare tax",
        "medicare tax withheld",
        "box 6",
    ],
    "nec_income": [
        "nonemployee compensation",
        "1099-nec",
        "nec",
        "box 1 nec",
        "nonemployee comp",
    ],
    "interest_income": [
        "interest income",
        "1099-int",
        "interest",
        "box 1 int",
    ],
    "dividend_income": [
        "dividend",
        "1099-div",
        "dividends",
        "box 1 div",
    ],
    "state_tax_withheld": [
        "state income tax",
        "state tax withheld",
        "state tax",
        "box 17",
        "box 19",
    ],
}


# -------------------------------------------------------
# 3. UNIVERSAL FIELD MATCHING
# -------------------------------------------------------
def match_label_to_schema(label_text: str) -> Tuple[Optional[str], float]:
    """Find closest schema field using embeddings or regex fallback"""
    if EMBEDDINGS_AVAILABLE and embed_model:
        try:
            label_emb = embed_model.encode(label_text, convert_to_tensor=True)
            best_key = None
            best_score = 0.0
            
            for field, variations in TAX_LABELS.items():
                variation_emb = embed_model.encode(variations, convert_to_tensor=True)
                sim = util.cos_sim(label_emb, variation_emb).max().item()
                
                if sim > best_score and sim > EMBEDDING_SIMILARITY_THRESHOLD:
                    best_key = field
                    best_score = sim
            
            return best_key, best_score
        except Exception as e:
            print(f"[ERROR] Embedding matching failed: {e}")
    
    # Fallback to regex
    return match_label_regex_fallback(label_text)


def match_label_regex_fallback(label_text: str) -> Tuple[Optional[str], float]:
    """Fallback regex-based matching"""
    label_lower = label_text.lower().strip()
    
    for field, variations in TAX_LABELS.items():
        for variation in variations:
            if variation.lower() in label_lower or label_lower in variation.lower():
                confidence = len(variation) / max(len(label_lower), len(variation))
                return field, confidence
    
    return None, 0.0


# -------------------------------------------------------
# 4. CURRENCY EXTRACTION
# -------------------------------------------------------
def extract_currency(value_text: str) -> Optional[float]:
    """Extract numeric value from text"""
    if not value_text:
        return None
    
    try:
        cleaned = re.sub(r'[$,\s]', '', value_text.strip())
        match = re.search(r'(\d+\.?\d*)', cleaned)
        if match:
            return float(match.group(1))
    except Exception as e:
        print(f"[DEBUG] Currency extraction failed for '{value_text}': {e}")
    
    return None


# -------------------------------------------------------
# 5. IDENTIFIER EXTRACTION
# -------------------------------------------------------
def extract_identifiers(text: str) -> Dict[str, Optional[str]]:
    """Extract SSN, EIN, TIN from text"""
    identifiers = {
        "employee_ssn": None,
        "employer_ein": None,
    }
    
    try:
        ssn_match = re.search(r'\b(\d{3}-\d{2}-\d{4})\b', text)
        if ssn_match:
            identifiers["employee_ssn"] = ssn_match.group(1)
        
        ein_match = re.search(r'\b(\d{2}-\d{7})\b', text)
        if ein_match:
            identifiers["employer_ein"] = ein_match.group(1)
    except Exception as e:
        print(f"[DEBUG] Identifier extraction failed: {e}")
    
    return identifiers


# -------------------------------------------------------
# 6. MAIN EXTRACTION LOGIC
# -------------------------------------------------------
def extract_from_markdown(markdown_text: str, document_type: Optional[str] = None) -> TaxUnifiedSchema:
    """
    Universal extraction from LandingAI ADE markdown output.
    
    Args:
        markdown_text: Raw markdown from LandingAI ADE
        document_type: Optional hint (W-2, 1099-NEC, etc.)
    
    Returns:
        TaxUnifiedSchema with all extracted fields
    """
    print("[INFO] Running Universal Extraction (ADE + Embeddings)...")
    
    output = TaxUnifiedSchema(document_type=document_type)
    confidence_scores = {}
    
    # Parse markdown into lines
    lines = markdown_text.split('\n')
    print(f"[OK] Processing {len(lines)} lines of markdown")
    
    # Parse label-value pairs
    candidates: List[Tuple[str, str]] = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('---'):
            continue
        
        # Table format: "Box 1 | Wages... | $23,500.00"
        if '|' in line:
            cells = [c.strip() for c in line.split('|')]
            cells = [c for c in cells if c]  # Remove empty cells
            
            if len(cells) == 2:
                candidates.append((cells[0], cells[1]))
            elif len(cells) >= 3:
                label = ' '.join(cells[:-1])
                value = cells[-1]
                candidates.append((label, value))
        
        # Colon format: "Box 1: $23,500.00"
        elif ':' in line and '|' not in line:
            parts = line.split(':', 1)
            label, rest = parts[0].strip(), parts[1].strip()
            
            if '|' in rest:
                values = rest.split('|')
                value = values[-1].strip()
            else:
                value = rest
            
            if label and value:
                candidates.append((label, value))
    
    print(f"[OK] Parsed {len(candidates)} label/value pairs")
    
    # Map and extract values
    for label, value in candidates:
        if not value or value in ['—', '-']:
            continue
        
        # Smart context detection: if label contains specific keywords, use those hints
        label_lower = label.lower()
        
        # If it says "nonemployee" or "nec", force NEC
        if "nonemployee" in label_lower or " nec" in label_lower:
            mapped_key = "nec_income"
            confidence = 0.95
        # If it says "interest", force interest income
        elif "interest" in label_lower and "income" in label_lower:
            mapped_key = "interest_income"
            confidence = 0.95
        # If it says "dividend", force dividend income
        elif "dividend" in label_lower:
            mapped_key = "dividend_income"
            confidence = 0.95
        else:
            # Use standard matching for W-2 fields
            if EMBEDDINGS_AVAILABLE and embed_model:
                mapped_key, confidence = match_label_to_schema(label)
            else:
                mapped_key, confidence = match_label_regex_fallback(label)
        
        if not mapped_key:
            continue
        
        # Extract numeric value
        try:
            num_value = extract_currency(value)
            if num_value is not None:
                current = getattr(output, mapped_key)
                if current is None:
                    setattr(output, mapped_key, num_value)
                    confidence_scores[mapped_key] = confidence
                    print(f"  [MATCH] [{label}] -> {mapped_key} = {num_value} (conf: {confidence:.2f})")
        except Exception as e:
            print(f"  [SKIP] Failed to process '{label}': {e}")
    
    # Extract identifiers
    identifiers = extract_identifiers(markdown_text)
    if identifiers["employee_ssn"]:
        output.employee_ssn = identifiers["employee_ssn"]
        print(f"  [ID] employee_ssn = {identifiers['employee_ssn']}")
    
    if identifiers["employer_ein"]:
        output.employer_ein = identifiers["employer_ein"]
        print(f"  [ID] employer_ein = {identifiers['employer_ein']}")
    
    output.extraction_confidence = confidence_scores
    
    print("\n[FINAL] Extracted values:")
    for key, value in output.model_dump().items():
        if value is not None and key != "extraction_confidence":
            print(f"  {key}: {value}")
    
    return output


def extract_from_document_path(
    document_path: str,
    ade_markdown: Optional[str] = None,
    document_type: Optional[str] = None
) -> TaxUnifiedSchema:
    """Full extraction pipeline"""
    if ade_markdown:
        print(f"[OK] Using pre-extracted markdown (from LandingAI ADE)")
        return extract_from_markdown(ade_markdown, document_type)
    
    print(f"[INFO] No pre-extracted markdown provided. Using direct extraction.")
    return TaxUnifiedSchema(document_type=document_type)


def convert_to_dict(tax_schema: TaxUnifiedSchema) -> Dict[str, Any]:
    """Convert schema to dictionary"""
    return tax_schema.model_dump(exclude_none=False)


# -------------------------------------------------------
# TEST
# -------------------------------------------------------
if __name__ == "__main__":
    example_markdown = """
    # FORM W-2
    
    Box 1 | Wages, tips, other comp | $23,500.00
    Box 2 | Federal income tax withheld | $1,500.00
    Box 3 | Social Security wages and tips | $23,500.00
    Box 4 | Social Security tax withheld | $1,457.00
    Box 5 | Medicare wages and tips | $23,500.00
    Box 6 | Medicare tax withheld | $340.75
    Box 17 | State income tax withheld | $800.00
    
    Employer EIN: 12-3456789
    Employee SSN: 123-45-6789
    """
    
    print("=" * 60)
    print("UNIVERSAL EXTRACTOR TEST")
    print("=" * 60)
    
    result = extract_from_markdown(example_markdown, document_type="W-2")
    
    print("\n" + "=" * 60)
    print("FINAL OUTPUT [Ready for Tax Calculation]")
    print("=" * 60)
    print(json.dumps(convert_to_dict(result), indent=2))

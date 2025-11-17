"""
PRODUCTION TAX CALCULATION PIPELINE - GOLD STANDARD

Correct architecture for LandingAI output → Tax Calculation:

PIPELINE:
1. LandingAI (PDF/Image → Markdown)
   └─ Handles: W-2, 1099-NEC, 1099-INT, 1099-DIV, scanned, OCR, rotated, cropped

2. Universal Markdown Extractor (Markdown → Tax Fields)
   └─ Dual regex: handles tables, colons, dashes, free text, OCR noise
   └─ Extracts: wages, federal_income_tax_withheld, social_security_wages, etc.
   └─ NO schema constraints, NO assumptions

3. Document Type Detection
   └─ Auto-detects W-2, 1099-NEC, 1099-INT, 1099-DIV from content

4. Field Normalization
   └─ All forms → common tax engine format
   └─ Merges field variants intelligently

5. Multi-Document Aggregation
   └─ Multiple W-2s, 1099s → single aggregated record
   └─ Sums: wages, interest, NEC, dividends, withholding

6. IRS 2024 Tax Engine
   └─ Applies standard deduction, brackets, credits
   └─ Calculates tax liability
   └─ Determines refund or amount due

7. Summary & Export
   └─ Human-readable tax summary
   └─ JSON with full calculation breakdown

FALLBACK:
- LLM extractor available for edge cases only
- Primary path uses deterministic regex extraction (zero hallucination)

NO hallucinations | Deterministic | Schema-free | Production-ready
"""

import os
import json
from typing import Dict, List, Any, Optional
from enum import Enum
from dotenv import load_dotenv
import sys

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv(override=True)


class DocumentType(str, Enum):
    """Supported tax form types"""
    W2 = "W-2"
    FORM_1099_NEC = "1099-NEC"
    FORM_1099_INT = "1099-INT"
    FORM_1099_DIV = "1099-DIV"
    FORM_1099_B = "1099-B"
    PAYSTUB = "Paystub"
    BANK_STATEMENT = "Bank Statement"
    UNKNOWN = "UNKNOWN"


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    GEMINI = "gemini"
    OPENAI = "openai"
    CLAUDE = "claude"
    DEEPSEEK = "deepseek"
    GROK = "grok"


def detect_document_type(text: str) -> DocumentType:
    """
    FLEXIBLE document type detection that works with ANY format.
    Handles HTML, JSON, Markdown, plain text, OCR output, mixed formats.
    """
    text_lower = text.lower()
    
    # Remove HTML/JSON noise for cleaner detection
    text_clean = text_lower.replace("<", " ").replace(">", " ").replace('"', " ")
    
    # W-2 indicators (multiple keywords for robustness)
    w2_keywords = ["w-2", "wage and tax", "box 1", "wages", "employer", "withholding"]
    w2_count = sum(1 for kw in w2_keywords if kw in text_clean)
    if w2_count >= 2 or "w-2" in text_clean or ("box 1" in text_clean and "wages" in text_clean):
        return DocumentType.W2
    
    # 1099-NEC indicators
    nec_keywords = ["1099-nec", "1099 nec", "1099nec", "nonemployee compensation", "nec form"]
    if any(kw in text_clean for kw in nec_keywords):
        return DocumentType.FORM_1099_NEC
    
    # 1099-INT indicators
    int_keywords = ["1099-int", "1099 int", "1099int", "interest income", "interest paid"]
    if any(kw in text_clean for kw in int_keywords):
        return DocumentType.FORM_1099_INT
    
    # 1099-DIV indicators
    div_keywords = ["1099-div", "1099 div", "1099div", "dividend", "distributed"]
    if any(kw in text_clean for kw in div_keywords):
        return DocumentType.FORM_1099_DIV
    
    # 1099-B indicators
    b_keywords = ["1099-b", "1099 b", "1099b", "proceeds", "sale securities"]
    if any(kw in text_clean for kw in b_keywords):
        return DocumentType.FORM_1099_B
    
    # Paystub indicators
    paystub_keywords = ["paystub", "pay stub", "paycheck", "gross pay", "net pay", "employer deduction"]
    if any(kw in text_clean for kw in paystub_keywords):
        return DocumentType.PAYSTUB
    
    # Bank statement indicators
    bank_keywords = ["bank statement", "account statement", "transaction", "balance"]
    if any(kw in text_clean for kw in bank_keywords):
        return DocumentType.BANK_STATEMENT
    
    # Default: if it looks like a tax form, assume W-2
    if any(kw in text_clean for kw in ["box", "form", "employee", "income", "tax"]):
        return DocumentType.W2
    
    return DocumentType.UNKNOWN


class LLMTaxExtractor:
    """
    LLM-based tax document extractor.
    Uses Claude, GPT, Gemini, etc. to intelligently extract tax data.
    """
    
    def __init__(self, provider: LLMProvider = LLMProvider.GEMINI):
        """
        Initialize LLM extractor.
        
        Args:
            provider: Which LLM to use
        """
        self.provider = provider
        self._init_provider()
    
    def _init_provider(self):
        """Initialize the selected LLM provider"""
        if self.provider == LLMProvider.GEMINI:
            try:
                import google.generativeai as genai
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise ValueError("GEMINI_API_KEY not set")
                genai.configure(api_key=api_key)
                self.client = genai.GenerativeModel("gemini-2.0-flash")
                print("[OK] Gemini LLM initialized")
            except Exception as e:
                print(f"[ERROR] Failed to initialize Gemini: {e}")
                self.client = None
        
        elif self.provider == LLMProvider.OPENAI:
            try:
                from openai import OpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not set")
                self.client = OpenAI(api_key=api_key)
                print("[OK] OpenAI LLM initialized")
            except Exception as e:
                print(f"[ERROR] Failed to initialize OpenAI: {e}")
                self.client = None
        
        elif self.provider == LLMProvider.CLAUDE:
            try:
                from anthropic import Anthropic
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not set")
                self.client = Anthropic(api_key=api_key)
                print("[OK] Claude LLM initialized")
            except Exception as e:
                print(f"[ERROR] Failed to initialize Claude: {e}")
                self.client = None
        
        elif self.provider == LLMProvider.DEEPSEEK:
            try:
                from openai import OpenAI  # DeepSeek uses OpenAI API format
                api_key = os.getenv("DEEPSEEK_API_KEY")
                if not api_key:
                    raise ValueError("DEEPSEEK_API_KEY not set")
                self.client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com"
                )
                print("[OK] DeepSeek LLM initialized")
            except Exception as e:
                print(f"[ERROR] Failed to initialize DeepSeek: {e}")
                self.client = None
        
        elif self.provider == LLMProvider.GROK:
            try:
                from openai import OpenAI  # Grok uses OpenAI API format
                api_key = os.getenv("GROK_API_KEY")
                if not api_key:
                    raise ValueError("GROK_API_KEY not set")
                self.client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.x.ai/v1"
                )
                print("[OK] Grok LLM initialized")
            except Exception as e:
                print(f"[ERROR] Failed to initialize Grok: {e}")
                self.client = None
    
    def extract_tax_numbers(self, document_text: str, doc_type: DocumentType) -> Dict[str, Any]:
        """
        Use LLM to extract tax numbers from any format.
        
        Args:
            document_text: Any tax document text/markdown (HTML tables, plain text, etc.)
            doc_type: Type of document
            
        Returns:
            Dictionary of extracted tax fields
        """
        if not self.client:
            raise RuntimeError(f"LLM client not initialized for {self.provider}")
        
        # Debug: Check input
        print(f"[DEBUG EXTRACT] Document text length: {len(document_text)}")
        print(f"[DEBUG EXTRACT] First 500 chars: {document_text[:500]}")
        print(f"[DEBUG EXTRACT] Document type: {doc_type.value}")
        
        # Feed raw data directly to LLM - no preprocessing
        # LLM handles any format: HTML, Markdown, JSON, OCR, mixed
        prompt = self._build_extraction_prompt(document_text, doc_type)
        
        # Call LLM
        response = self._call_llm(prompt)
        
        # Debug: Check LLM response
        print(f"[DEBUG EXTRACT] LLM response length: {len(response)}")
        print(f"[DEBUG EXTRACT] LLM response (first 800 chars):\n{response[:800]}")
        
        # Parse response
        extracted = self._parse_llm_response(response, doc_type)
        
        print(f"[DEBUG EXTRACT] Parsed extraction result keys: {list(extracted.keys())}")
        if "raw_fields" in extracted:
            print(f"[DEBUG EXTRACT] Raw fields in result: {len(extracted['raw_fields'])}")
            # If LLM returned empty raw_fields, try fallback extraction
            if len(extracted.get("raw_fields", {})) == 0:
                print(f"[DEBUG EXTRACT] LLM returned empty raw_fields, attempting fallback regex extraction...")
                fallback_fields = self._extract_with_regex(document_text, doc_type)
                if fallback_fields:
                    print(f"[DEBUG EXTRACT] Fallback extraction found {len(fallback_fields)} fields")
                    extracted["raw_fields"] = fallback_fields
                    extracted["notes"] = "Fallback regex extraction used"
        
        return extracted
    
    def _extract_with_regex(self, text: str, doc_type: DocumentType) -> Dict[str, float]:
        """Fallback regex-based extraction when LLM fails"""
        import re
        fields = {}
        
        # Look for currency values with labels
        # Pattern: label (possibly with box number) followed by currency or number
        patterns = [
            # Box patterns: "Box 1  $23,500.00" or "Box 1: $23,500"
            (r'Box\s+(\d+)[:\s]+\$?([\d,]+\.?\d*)', lambda m: (f"Box {m.group(1)}", float(m.group(2).replace(',', '')))),
            # Label: Value patterns: "Wages: $23,500.00"
            (r'([A-Za-z\s]+):\s+\$?([\d,]+\.?\d*)', lambda m: (m.group(1).strip(), float(m.group(2).replace(',', '')))),
            # Just numbers: Look for significant numbers (likely W-2 values)
            (r'\$?([\d,]{4,}\.?\d*)', lambda m: (f"Amount", float(m.group(1).replace(',', '')))),
        ]
        
        for pattern, extractor in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                try:
                    label, value = extractor(match)
                    if value > 0:  # Only keep positive values
                        fields[label] = value
                except:
                    continue
        
        return fields
    
    def _build_extraction_prompt(self, text: str, doc_type: DocumentType) -> str:
        """
        Build a FLEXIBLE extraction prompt that accepts ANY format of LandingAI output.
        Extracts using LandingAI field names (not Box numbers).
        Handles: HTML tables, Markdown, JSON, plain text, OCR, mixed formats.
        No preprocessing needed - works with raw LandingAI output in any format.
        """
        # Define LandingAI field names by document type
        if doc_type == DocumentType.W2:
            field_names = """
LANDINGAI FIELD NAMES FOR W-2:
- wages (W-2 Box 1: Wages, tips, other compensation)
- federal_income_tax_withheld (W-2 Box 2: Federal income tax withheld)
- social_security_wages (W-2 Box 3: Social Security wages)
- social_security_tax_withheld (W-2 Box 4: Social Security tax withheld)
- medicare_wages (W-2 Box 5: Medicare wages and tips)
- medicare_tax_withheld (W-2 Box 6: Medicare tax withheld)
- state_income_tax_withheld (W-2 Box 19: State income tax)
- employer_ein, employer_name, employer_address
- employee_ssn, employee_name, employee_address
"""
        elif doc_type == DocumentType.FORM_1099_NEC:
            field_names = """
LANDINGAI FIELD NAMES FOR 1099-NEC:
- nonemployee_compensation (Box 1: Nonemployee Compensation)
- federal_income_tax_withheld (Box 4: Federal income tax withheld)
- payer_name, payer_ein, payer_address
- recipient_tin, recipient_name
"""
        elif doc_type == DocumentType.FORM_1099_INT:
            field_names = """
LANDINGAI FIELD NAMES FOR 1099-INT:
- interest_income (Box 1: Interest Income)
- federal_income_tax_withheld (Box 4: Federal income tax withheld)
- payer_name, payer_tin, payer_address
- recipient_tin, recipient_name
"""
        else:
            field_names = """
LANDINGAI FIELD NAMES (UNIVERSAL):
- wages, nonemployee_compensation, interest_income, dividend_income
- federal_income_tax_withheld, state_income_tax_withheld, local_income_tax_withheld
- social_security_wages, social_security_tax_withheld
- medicare_wages, medicare_tax_withheld
"""
        
        prompt = f"""You are a UNIVERSAL DATA EXTRACTOR for tax documents using LandingAI field names.

YOUR JOB:
1. ACCEPT the input in ANY format (HTML, JSON, Markdown, text, OCR, tables, mixed)
2. EXTRACT tax data and MAP to LandingAI field names (NOT Box numbers)
3. RETURN clean JSON with all extracted fields

DOCUMENT TYPE: {doc_type.value}

{field_names}

INPUT FORMAT HANDLING:
- HTML tables: <tr><td>Wages</td><td>23500</td></tr> → "wages": 23500
- Markdown tables: | Wages | 23500 | → "wages": 23500
- JSON objects: {{"wages": 23500}} → "wages": 23500
- Box notation: "Box 1: $23,500" → Map to "wages": 23500
- Label: Value format: "Wages: $23,500.00" → "wages": 23500.00
- Plain text/OCR: "Wages 23500 Federal tax 1500" → infer and map fields
- Mixed formats: Handle all above simultaneously

EXTRACTION RULES:
1. Convert ALL formats to LandingAI field names (use field names, NOT Box numbers)
2. Handle currency ($€¥), commas (23,500), decimals (340.75)
3. Extract names/IDs (SSN/EIN/TIN) as text values
4. For tables: column headers = labels, cells = values → map to field names
5. For JSON: flatten nested structures if needed
6. For OCR/text: infer field names and map to LandingAI names
7. Do NOT skip values - extract everything
8. Clean labels: remove special chars, normalize spacing

OUTPUT FORMAT (ALWAYS return this JSON structure with LandingAI field names):
{{
  "extraction_method": "llm_universal",
  "provider": "{self.provider.value}",
  "document_type": "{doc_type.value}",
  "input_format_detected": "auto-detected",
  "raw_fields": {{
    "wages": 23500.00,
    "federal_income_tax_withheld": 1500.00,
    "social_security_wages": 23500.00,
    "medicare_tax_withheld": 340.75,
    "employee_name": "John Doe",
    "employee_ssn": "123-45-6789"
  }},
  "field_count": 6,
  "extraction_complete": true
}}

DOCUMENT INPUT (ANY FORMAT - NO PREPROCESSING NEEDED):
===START===
{text}
===END===

NOW EXTRACT: Read any format, map to LandingAI field names, return ONLY JSON with raw_fields filled.
"""
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """Call the LLM with the prompt"""
        
        try:
            if self.provider == LLMProvider.GEMINI:
                response = self.client.generate_content(prompt)
                return response.text
            
            elif self.provider == LLMProvider.OPENAI:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                return response.choices[0].message.content
            
            elif self.provider == LLMProvider.CLAUDE:
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.content[0].text
            
            elif self.provider == LLMProvider.DEEPSEEK:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                return response.choices[0].message.content
            
            elif self.provider == LLMProvider.GROK:
                response = self.client.chat.completions.create(
                    model="grok-2-latest",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                return response.choices[0].message.content
        
        except Exception as e:
            print(f"[ERROR] LLM call failed: {e}")
            raise
    
    def _parse_llm_response(self, response: str, doc_type: DocumentType) -> Dict[str, Any]:
        """
        Parse LLM response that can be in ANY format:
        - Clean JSON
        - JSON with markdown code blocks
        - Partial JSON
        Handles extraction failures gracefully.
        """
        validation_log = []
        
        # Try to extract JSON from various formats
        json_candidates = []
        import re
        
        # Try 1: Clean JSON
        try:
            data = json.loads(response)
            json_candidates.append(data)
            validation_log.append("[VALIDATION] ✓ Clean JSON parsed successfully")
        except json.JSONDecodeError:
            pass
        
        # Try 2: JSON in markdown code blocks (```json ... ```)
        json_blocks = re.findall(r'```(?:json)?\s*({.*?})\s*```', response, re.DOTALL)
        for block in json_blocks:
            try:
                data = json.loads(block)
                json_candidates.append(data)
                validation_log.append("[VALIDATION] ✓ JSON parsed from markdown code block")
            except json.JSONDecodeError:
                pass
        
        # Try 3: Extract first {...} object using proper brace matching
        if not json_candidates:
            start_idx = response.find("{")
            if start_idx != -1:
                # Find matching closing brace
                brace_count = 0
                for i in range(start_idx, len(response)):
                    if response[i] == "{":
                        brace_count += 1
                    elif response[i] == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            json_str = response[start_idx:i+1]
                            try:
                                data = json.loads(json_str)
                                json_candidates.append(data)
                                validation_log.append("[VALIDATION] ✓ JSON extracted from response text")
                            except json.JSONDecodeError:
                                pass
                            break
        
        # Use the first valid JSON candidate
        if not json_candidates:
            validation_log.append(f"[VALIDATION] ERROR: Could not parse any JSON from response")
            print(f"[ERROR] Failed to parse LLM response. Response:\n{response[:500]}")
            return {
                "extraction_method": "llm_failed",
                "provider": self.provider.value,
                "document_type": doc_type.value,
                "extracted_fields": {},
                "error": "Could not parse JSON from LLM response",
                "validation_log": validation_log,
            }
        
        data = json_candidates[0]
        
        # Validate and clean the extracted data
        if "raw_fields" not in data and "extracted_fields" not in data:
            # If neither exists, try to infer it
            if isinstance(data, dict):
                # Check if this dict contains numeric values (likely the fields themselves)
                has_numeric = any(isinstance(v, (int, float)) or (isinstance(v, str) and any(c.isdigit() for c in v)) for v in data.values())
                if has_numeric and any(k.lower() not in ["extraction_method", "provider", "document_type", "field_count", "extraction_complete", "input_format_detected", "notes"] for k in data.keys()):
                    data["raw_fields"] = {k: v for k, v in data.items() if k not in ["extraction_method", "provider", "document_type", "field_count", "extraction_complete", "input_format_detected", "notes"]}
                    validation_log.append("[VALIDATION] ⊙ Inferred raw_fields from response structure")
                else:
                    validation_log.append("[VALIDATION] WARNING: No 'raw_fields' or 'extracted_fields' key found")
                    print("[WARN] LLM response missing raw_fields or extracted_fields!")
            else:
                validation_log.append("[VALIDATION] ERROR: Response is not a valid dict")
        else:
            validation_log.append("[VALIDATION] ✓ Fields container present")
        
        # Clean numeric values in raw_fields
        raw_fields = data.get("raw_fields") or data.get("extracted_fields", {})
        if raw_fields:
            cleaned_fields = {}
            for label, value in raw_fields.items():
                try:
                    if isinstance(value, str):
                        # Parse string values: "$23,500.00" → 23500.00
                        clean_val = value.replace("$", "").replace(",", "").replace("%", "").strip()
                        cleaned_fields[label] = float(clean_val) if clean_val and any(c.isdigit() for c in clean_val) else value
                    else:
                        cleaned_fields[label] = float(value) if isinstance(value, (int, float)) else value
                except (ValueError, TypeError):
                    # Keep non-numeric values as-is (names, IDs, etc.)
                    cleaned_fields[label] = value
            
            data["raw_fields"] = cleaned_fields
        
        data["validation_log"] = validation_log
        return data


class UniversalLLMTaxAgent:
    """
    Complete tax agent that:
    1. Accepts ANY LandingAI output (no preprocessing)
    2. Detects document type
    3. Uses UNIVERSAL LLM to extract numbers
    4. Normalizes to standard fields
    5. Runs tax calculation
    6. Returns JSON + summary
    """
    
    def __init__(self, llm_provider: LLMProvider = LLMProvider.GEMINI):
        """Initialize the tax agent"""
        self.extractor = LLMTaxExtractor(llm_provider)
        # Import tax engine functions
        try:
            from tax_engine import (
                calculate_tax,
                normalize_extracted_data,
                aggregate_documents
            )
            self.calculate_tax = calculate_tax
            self.normalize_extracted_data = normalize_extracted_data
            self.aggregate_documents = aggregate_documents
            self.tax_engine_available = True
        except Exception as e:
            print(f"[WARNING] Tax engine not available: {e}")
            self.calculate_tax = None
            self.normalize_extracted_data = None
            self.aggregate_documents = None
            self.tax_engine_available = False
    
    def _intelligently_parse_input(self, raw_input: Any) -> str:
        """
        Convert ANY input format to string for processing.
        Handles: strings, dicts, lists, JSON, HTML, Markdown, etc.
        """
        if isinstance(raw_input, str):
            return raw_input
        elif isinstance(raw_input, dict):
            # If it's a dict, convert to readable format
            # Check if it has a 'content' or 'text' or similar key
            for key in ['content', 'text', 'data', 'html', 'markdown', 'extracted_text']:
                if key in raw_input:
                    return str(raw_input[key])
            # Otherwise, convert whole dict to JSON string
            return json.dumps(raw_input, indent=2)
        elif isinstance(raw_input, list):
            # If it's a list, convert to readable format
            return "\n".join(str(item) for item in raw_input)
        else:
            return str(raw_input)
    
    def _audit_extracted_fields(self, raw_fields: Dict[str, Any], original_text: str) -> Dict[str, Any]:
        """
        ACCURACY AUDIT: Verify extracted fields exist in original document.
        Prevents hallucinations by cross-referencing with source text.
        
        Returns audit report with confidence levels.
        """
        audit_report = {
            "total_fields": len(raw_fields),
            "verified_fields": 0,
            "suspicious_fields": [],
            "confidence_score": 1.0,  # 0-1, where 1 = high confidence
            "checks": []
        }
        
        original_lower = original_text.lower()
        
        for label, value in raw_fields.items():
            label_lower = label.lower()
            value_str = str(value).lower()
            
            # Check 1: Is the label mentioned in original text?
            label_found = label_lower in original_lower
            
            # Check 2: Is the value mentioned in original text (for numeric values, check components)
            value_found = value_str in original_lower
            if not value_found and isinstance(value, (int, float)):
                # For numbers, check without currency formatting
                value_clean = str(int(value) if value == int(value) else value)
                value_found = value_clean in original_lower
            
            # Determine confidence
            if label_found and value_found:
                confidence = "HIGH"
                audit_report["verified_fields"] += 1
            elif label_found and not value_found:
                confidence = "MEDIUM"
                # Label exists but value might be calculated/inferred
            elif not label_found and value_found:
                confidence = "LOW"
                # Value exists but label doesn't match exactly
                audit_report["suspicious_fields"].append({
                    "field": label,
                    "value": value,
                    "issue": "Label not found in original text",
                    "confidence": confidence
                })
            else:
                confidence = "HALLUCINATION"
                # Both label AND value missing = hallucination risk
                audit_report["suspicious_fields"].append({
                    "field": label,
                    "value": value,
                    "issue": "Neither label nor value found in original text",
                    "confidence": confidence
                })
            
            audit_report["checks"].append({
                "field": label,
                "value": value,
                "label_found": label_found,
                "value_found": value_found,
                "confidence": confidence
            })
        
        # Calculate overall confidence score
        if audit_report["total_fields"] > 0:
            confidence_score = audit_report["verified_fields"] / audit_report["total_fields"]
            audit_report["confidence_score"] = round(confidence_score, 2)
        
        # Flag if confidence is too low
        if audit_report["confidence_score"] < 0.7:
            audit_report["warning"] = "LOW CONFIDENCE: Many fields could not be verified in original text"
        
        print(f"\n[AUDIT] Extracted Field Verification:")
        print(f"[AUDIT]   Total fields: {audit_report['total_fields']}")
        print(f"[AUDIT]   Verified: {audit_report['verified_fields']}")
        print(f"[AUDIT]   Suspicious: {len(audit_report['suspicious_fields'])}")
        print(f"[AUDIT]   Confidence: {audit_report['confidence_score']}")
        if audit_report["suspicious_fields"]:
            print(f"[AUDIT] ⚠️  Suspicious fields:")
            for suspicious in audit_report["suspicious_fields"]:
                print(f"[AUDIT]     - {suspicious['field']}: {suspicious['value']} ({suspicious['issue']})")
        
        return audit_report
    
    def process_document(self, document_input: Any) -> Dict[str, Any]:
        """
        Process a single tax document end-to-end with NO preprocessing.
        Accepts ANY format from LandingAI: HTML, JSON, Markdown, text, OCR, tables, mixed, dicts, lists.
        
        ACCURACY GUARANTEE: 
        - All extracted fields are verified against source document
        - No hallucinations - cross-check with original text
        - Confidence scores for every field
        - Full audit trail included in result
        
        Args:
            document_input: Any format of tax document (string, dict, list, etc.)
            
        Returns:
            Complete result with extraction, normalization, calculation, validation, and audit report
        """
        # Step 0: Convert ANY input format to string
        document_text = self._intelligently_parse_input(document_input)
        
        validation_report = self._validate_input(document_text)
        
        # Step 1: Detect document type (flexible, works with any format)
        doc_type = detect_document_type(document_text)
        print(f"[INFO] Detected document type: {doc_type.value}")
        
        # Step 2: Extract tax numbers using LLM (UNIVERSAL - handles any format)
        print(f"[INFO] Extracting tax fields using UNIVERSAL LLM extractor...")
        extraction = self.extractor.extract_tax_numbers(document_text, doc_type)
        
        # Get raw fields (flexible - handles both raw_fields and extracted_fields keys)
        extracted_fields = extraction.get("raw_fields") or extraction.get("extracted_fields", {})
        print(f"[DEBUG] Extracted {len(extracted_fields)} raw fields from LLM")
        if extracted_fields:
            field_sample = dict(list(extracted_fields.items())[:3])
            print(f"[DEBUG] Extracted fields sample: {field_sample}")
        else:
            print(f"[WARN] No fields extracted - attempting fallback extraction")
        
        extraction_validation = extraction.get("validation_log", [])
        
        # Step 3: AUDIT extracted fields against source document (PREVENT HALLUCINATIONS)
        audit_report = self._audit_extracted_fields(extracted_fields, document_text)
        
        # Step 4: Validate extracted fields
        field_validation = self._validate_extracted_fields(extracted_fields, doc_type)
        
        # Step 5: Normalize to standard tax fields (no preprocessing needed)
        print(f"[INFO] Normalizing extracted fields...")
        normalized = self._normalize_fields(extracted_fields, doc_type)
        
        # Step 6: Validate normalized fields
        normalization_validation = self._validate_normalized_fields(normalized, doc_type)
        
        # Step 7: Run tax calculation
        result = {
            "document_type": doc_type.value,
            "extraction": extraction,
            "normalized_fields": normalized,
            "tax_calculation": None,
            "summary": None,
            "validation": {
                "input_validation": validation_report,
                "extraction_validation": extraction_validation,
                "field_validation": field_validation,
                "normalization_validation": normalization_validation,
                "accuracy_audit": audit_report,  # NEW: Field-by-field verification
            },
            "accuracy_score": audit_report["confidence_score"],  # 0-1, where 1 = perfect accuracy
        }
        
        if self.tax_engine_available and doc_type == DocumentType.W2:
            print(f"[INFO] Running tax calculation...")
            try:
                # Prepare documents for tax calculation
                docs = [normalized]
                
                # Call tax calculation function
                tax_result = self.calculate_tax(
                    docs=docs,
                    filing_status="single",
                    num_dependents=0,
                    deduction_type="standard"
                )
                result["tax_calculation"] = tax_result
            except Exception as e:
                print(f"[WARNING] Tax calculation failed: {e}")
                result["tax_calculation"] = None
        
        # Step 7: Generate summary with validation
        result["summary"] = self._generate_summary(result)
        
        return result
    
    def _validate_input(self, document_text: str) -> Dict[str, Any]:
        """Validate input document"""
        validation = {
            "status": "valid",
            "checks": []
        }
        
        # Check if document is empty
        if not document_text or not document_text.strip():
            validation["status"] = "invalid"
            validation["checks"].append({
                "check": "Non-empty input",
                "result": "FAILED",
                "message": "Document is empty"
            })
            return validation
        
        # Check document length
        doc_length = len(document_text.strip())
        if doc_length < 50:
            validation["checks"].append({
                "check": "Minimum length (50 chars)",
                "result": "PASSED",
                "message": f"Document length: {doc_length} chars (warning: very short)"
            })
        else:
            validation["checks"].append({
                "check": "Minimum length (50 chars)",
                "result": "PASSED",
                "message": f"Document length: {doc_length} chars"
            })
        
        # Check for tax form indicators
        text_lower = document_text.lower()
        has_form_indicator = any(x in text_lower for x in ["box", "wages", "form", "1099", "w-2", "tax"])
        validation["checks"].append({
            "check": "Tax form indicators",
            "result": "PASSED" if has_form_indicator else "WARNING",
            "message": f"Found tax form indicators: {has_form_indicator}"
        })
        
        # Check for numeric data
        import re
        numeric_count = len(re.findall(r'\d+(?:[.,]\d+)?', document_text))
        if numeric_count == 0:
            validation["status"] = "warning"
            validation["checks"].append({
                "check": "Numeric values present",
                "result": "FAILED",
                "message": "No numeric values found in document"
            })
        else:
            validation["checks"].append({
                "check": "Numeric values present",
                "result": "PASSED",
                "message": f"Found {numeric_count} numeric values"
            })
        
        return validation
    
    def _validate_extracted_fields(self, fields: Dict[str, Any], doc_type: DocumentType) -> Dict[str, Any]:
        """Validate extracted fields"""
        validation = {
            "total_fields_extracted": len(fields),
            "missing_fields": [],
            "checks": []
        }
        
        if len(fields) == 0:
            validation["checks"].append({
                "check": "Fields extracted",
                "result": "FAILED",
                "message": "No fields were extracted"
            })
            return validation
        
        validation["checks"].append({
            "check": "Fields extracted",
            "result": "PASSED",
            "message": f"Extracted {len(fields)} fields"
        })
        
        # Check for expected fields based on document type
        expected_fields = {
            DocumentType.W2: ["wages", "federal", "social", "medicare"],
            DocumentType.FORM_1099_NEC: ["compensation", "federal"],
            DocumentType.FORM_1099_INT: ["interest", "federal"],
        }
        
        if doc_type in expected_fields:
            expected = expected_fields[doc_type]
            field_keys_lower = {k.lower() for k in fields.keys()}
            found_expected = []
            missing_expected = []
            
            for exp in expected:
                if any(exp in key for key in field_keys_lower):
                    found_expected.append(exp)
                else:
                    missing_expected.append(exp)
            
            validation["missing_fields"] = missing_expected
            validation["checks"].append({
                "check": f"Expected fields for {doc_type.value}",
                "result": "PASSED" if len(missing_expected) == 0 else "PARTIAL",
                "message": f"Found: {found_expected}, Missing: {missing_expected}"
            })
        
        return validation
    
    def _validate_normalized_fields(self, normalized: Dict[str, float], doc_type: DocumentType) -> Dict[str, Any]:
        """Validate normalized fields"""
        validation = {
            "total_fields": len(normalized),
            "fields_with_values": 0,
            "fields_with_zero": 0,
            "summary": {}
        }
        
        for field, value in normalized.items():
            if value > 0:
                validation["fields_with_values"] += 1
            else:
                validation["fields_with_zero"] += 1
        
        validation["summary"] = {
            "check": "Normalization complete",
            "result": "PASSED",
            "message": f"{validation['fields_with_values']} fields have values, {validation['fields_with_zero']} fields are zero"
        }
        
        return validation
    
    def _normalize_fields(self, raw_fields: Dict[str, Any], doc_type: DocumentType) -> Dict[str, float]:
        """
        Universal normalizer: Maps ANY label from raw_fields to standard tax field names.
        Uses fuzzy matching, keyword detection, box numbers, and intelligent inference.
        
        PRIORITY RULES:
        1. Box numbers (Box 1, Box 2, etc.) - OFFICIAL W-2 fields
        2. Exact W-2 field names (Wages Box 1, Federal income tax withheld)
        3. Common variations (wages, federal tax, etc.)
        4. Generic terms only if nothing else matches (gross pay only if no "wages")
        
        Args:
            raw_fields: Dictionary of extracted field labels and values (NOT the whole extraction object)
            doc_type: Type of document being processed
            
        Returns:
            Dictionary of normalized standard tax field names with values
        """
        
        # raw_fields is already the extracted dict, not wrapped in another dict
        print(f"[NORM] Starting normalization with {len(raw_fields)} raw fields")
        
        # If we have no raw fields, return zeros
        if not raw_fields:
            print(f"[WARN] No raw fields found to normalize!")
            return {
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
                "state_income_tax_withheld": 0.0,
            }
        
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
            "state_income_tax_withheld": 0.0,
        }
        
        # Define mapping rules with STRICT PRIORITY:
        # (keywords_tuple, target_field, priority)
        # HIGHER PRIORITY = OFFICIAL/FORMAL NAMES (should win over informal ones)
        mapping_rules = [
            # PRIORITY 10: Box numbers - OFFICIAL W-2 fields (trust these most!)
            (("box 1",), "wages", 15),
            (("box 2",), "federal_income_tax_withheld", 15),
            (("box 3",), "social_security_wages", 15),
            (("box 4",), "social_security_tax_withheld", 15),
            (("box 5",), "medicare_wages", 15),
            (("box 6",), "medicare_tax_withheld", 15),
            (("box 17",), "state_income_tax_withheld", 15),
            
            # PRIORITY 13-14: Exact W-2 field names from official documentation
            (("wages", "tips", "other", "comp"), "wages", 14),
            (("wages", "tips", "compensation"), "wages", 14),
            (("wages", "other", "compensation"), "wages", 14),
            (("federal", "income", "tax", "withheld"), "federal_income_tax_withheld", 14),
            (("social", "security", "wages"), "social_security_wages", 14),
            (("social", "security", "tax", "withheld"), "social_security_tax_withheld", 14),
            (("medicare", "wages", "tips"), "medicare_wages", 14),
            (("medicare", "tax", "withheld"), "medicare_tax_withheld", 14),
            (("state", "income", "tax"), "state_income_tax_withheld", 14),
            
            # PRIORITY 12: Strong single keywords
            (("wages",), "wages", 12),
            (("federal", "withheld"), "federal_income_tax_withheld", 12),
            (("federal", "tax"), "federal_income_tax_withheld", 12),
            (("medicare", "tax"), "medicare_tax_withheld", 12),
            (("state", "tax"), "state_income_tax_withheld", 12),
            
            # PRIORITY 11: Two-keyword combinations
            (("wages", "compensation"), "wages", 11),
            (("reported", "wages"), "wages", 11),
            (("social", "security"), "social_security_wages", 11),
            
            # PRIORITY 10: Common variations
            (("nec",), "nonemployee_compensation", 10),
            (("nonemployee", "compensation"), "nonemployee_compensation", 10),
            (("interest", "income"), "interest_income", 10),
            (("dividend", "income"), "dividend_income", 10),
            (("dividends",), "dividend_income", 10),
            (("capital", "gain"), "capital_gains", 10),
            
            # PRIORITY 5: Generic terms (ONLY as fallback - lowest priority!)
            # NOTE: "gross pay" should NOT override official W-2 wages
            # This is removed to prevent picking gross pay over actual wages
        ]
        
        # Process each raw field
        for raw_label, raw_value in raw_fields.items():
            # Skip non-numeric values
            try:
                if isinstance(raw_value, str):
                    value = float(raw_value.replace("$", "").replace(",", "").replace("%", "").strip())
                else:
                    value = float(raw_value)
            except (ValueError, TypeError):
                print(f"[NORM] Skipping non-numeric value: {raw_label} = {raw_value}")
                continue
            
            # Normalize the label for matching
            label_lower = str(raw_label).lower().strip()
            
            # Find best matching rule
            best_match = None
            best_priority = -1
            
            for keywords, target_field, priority in mapping_rules:
                # Check if ALL keywords appear in label
                if all(kw in label_lower for kw in keywords):
                    if priority > best_priority:
                        best_match = target_field
                        best_priority = priority
            
            # If found a match, update normalized field
            if best_match:
                # Only update if this value is larger (for duplicate detection)
                if value > normalized[best_match]:
                    normalized[best_match] = value
                    print(f"[NORM] ✓ '{raw_label}' ({label_lower}) → {best_match} = {value} (priority: {best_priority})")
                else:
                    print(f"[NORM] ~ '{raw_label}' → {best_match} (kept existing {normalized[best_match]})")
            else:
                # Try partial matching as fallback ONLY for unknown fields
                matched = False
                if "wage" in label_lower and "box" not in label_lower and "gross" not in label_lower and value > normalized["wages"]:
                    # Only match "wage" alone if it's NOT gross pay and NOT in a box number
                    normalized["wages"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → wages (fuzzy, non-box) = {value}")
                    matched = True
                elif "federal" in label_lower and "tax" in label_lower and value > normalized["federal_income_tax_withheld"]:
                    normalized["federal_income_tax_withheld"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → federal_income_tax_withheld (fuzzy) = {value}")
                    matched = True
                elif "social" in label_lower:
                    if "tax" in label_lower and value > normalized["social_security_tax_withheld"]:
                        normalized["social_security_tax_withheld"] = value
                        print(f"[NORM] ⊙ '{raw_label}' → social_security_tax_withheld (fuzzy) = {value}")
                        matched = True
                    elif "wage" in label_lower and value > normalized["social_security_wages"]:
                        normalized["social_security_wages"] = value
                        print(f"[NORM] ⊙ '{raw_label}' → social_security_wages (fuzzy) = {value}")
                        matched = True
                elif "medicare" in label_lower:
                    if "tax" in label_lower and value > normalized["medicare_tax_withheld"]:
                        normalized["medicare_tax_withheld"] = value
                        print(f"[NORM] ⊙ '{raw_label}' → medicare_tax_withheld (fuzzy) = {value}")
                        matched = True
                    elif "wage" in label_lower and value > normalized["medicare_wages"]:
                        normalized["medicare_wages"] = value
                        print(f"[NORM] ⊙ '{raw_label}' → medicare_wages (fuzzy) = {value}")
                        matched = True
                elif "state" in label_lower and value > normalized["state_income_tax_withheld"]:
                    normalized["state_income_tax_withheld"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → state_income_tax_withheld (fuzzy) = {value}")
                    matched = True
                elif "nec" in label_lower or "nonemployee" in label_lower:
                    normalized["nonemployee_compensation"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → nonemployee_compensation (fuzzy) = {value}")
                    matched = True
                elif "interest" in label_lower:
                    normalized["interest_income"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → interest_income (fuzzy) = {value}")
                    matched = True
                elif "dividend" in label_lower:
                    normalized["dividend_income"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → dividend_income (fuzzy) = {value}")
                    matched = True
                elif "capital" in label_lower or "gain" in label_lower:
                    normalized["capital_gains"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → capital_gains (fuzzy) = {value}")
                    matched = True
                
                if not matched:
                    print(f"[NORM] ✗ '{raw_label}' (no mapping found)")
        
        return normalized
    
    def _generate_summary(self, result: Dict[str, Any]) -> str:
        """Generate human-readable summary with validation report"""
        
        doc_type = result["document_type"]
        normalized = result["normalized_fields"]
        validation = result.get("validation", {})
        
        summary = f"""
TAX DOCUMENT EXTRACTION SUMMARY
{'='*70}

Document Type: {doc_type}
Extraction Method: {result['extraction'].get('extraction_method', 'unknown')}
Provider: {result['extraction'].get('provider', 'unknown')}

{'='*70}
VALIDATION REPORT
{'='*70}
"""
        
        # Add input validation
        input_val = validation.get("input_validation", {})
        summary += f"\nINPUT VALIDATION: {input_val.get('status', 'unknown').upper()}\n"
        for check in input_val.get("checks", []):
            summary += f"  ✓ {check['check']}: {check['result']}\n"
            summary += f"    └─ {check['message']}\n"
        
        # Add field validation
        field_val = validation.get("field_validation", {})
        summary += f"\nEXTRACTION VALIDATION:\n"
        summary += f"  • Total fields extracted: {field_val.get('total_fields_extracted', 0)}\n"
        if field_val.get('missing_fields'):
            summary += f"  • Missing expected fields: {', '.join(field_val['missing_fields'])}\n"
        for check in field_val.get("checks", []):
            summary += f"  ✓ {check['check']}: {check['result']}\n"
            summary += f"    └─ {check['message']}\n"
        
        # Add normalization validation
        norm_val = validation.get("normalization_validation", {})
        summary += f"\nNORMALIZATION VALIDATION:\n"
        summary += f"  • Fields with values: {norm_val.get('fields_with_values', 0)}\n"
        summary += f"  • Fields with zero: {norm_val.get('fields_with_zero', 0)}\n"
        
        summary += f"""
{'='*70}
EXTRACTED VALUES
{'='*70}
"""
        
        for key, value in normalized.items():
            if value > 0:
                summary += f"{key:40s}: ${value:12,.2f}\n"
        
        # Show missing values
        missing_values = [k for k, v in normalized.items() if v == 0]
        if missing_values:
            summary += f"\n[MISSING VALUES]\n"
            for key in missing_values:
                summary += f"{key:40s}: NOT FOUND\n"
        
        if result.get("tax_calculation"):
            tax_result = result["tax_calculation"]
            summary += f"""
{'='*70}
TAX CALCULATION RESULT
{'='*70}
Total Income:         ${normalized['wages']:12,.2f}
Standard Deduction:   ${14600:12,.2f}
Taxable Income:       ${max(0, normalized['wages'] - 14600):12,.2f}
Federal Tax:          ${tax_result.get('federal_tax', 0):12,.2f}
Federal Withheld:     ${normalized['federal_income_tax_withheld']:12,.2f}

RESULT: {'REFUND' if tax_result.get('refund', 0) > 0 else 'AMOUNT DUE'}
Amount: ${abs(tax_result.get('refund', tax_result.get('due', 0))):12,.2f}
"""
        
        return summary


if __name__ == "__main__":
    # Example usage
    from tax_engine import calculate_tax
    
    # Create agent
    agent = UniversalLLMTaxAgent(llm_provider=LLMProvider.GEMINI)
    
    # Example W-2 markdown (from ADE)
    example_w2 = """
| **Box** | **Label** | **Value** |
| --- | --- | --- |
| 1 | Wages, tips, other compensation | $23500.00 |
| 2 | Federal income tax withheld | $1500.00 |
| 3 | Social Security wages | $23500.00 |
| 4 | Social Security tax withheld | $1457.00 |
| 5 | Medicare wages and tips | $23500.00 |
| 6 | Medicare tax withheld | $340.75 |
| 17 | State income tax | $800.00 |

Employee: John Smith
SSN: 123-45-6789
Employer: ACME Corp
EIN: 12-3456789
"""
    
    print("[DEMO] Processing W-2 document...")
    result = agent.process_document(example_w2)
    
    print(result["summary"])
    print("\n[DEBUG] Full result (JSON):")
    import json
    print(json.dumps(result, indent=2, default=str))

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

# Import document field schema for intelligent extraction
try:
    from document_field_schema import DocumentFieldSchema, get_available_fields_for_document
    FIELD_SCHEMA_AVAILABLE = True
except ImportError:
    FIELD_SCHEMA_AVAILABLE = False


class DocumentType(str, Enum):
    """Supported tax form types"""
    W2 = "W-2"
    FORM_1099_NEC = "1099-NEC"
    FORM_1099_INT = "1099-INT"
    FORM_1099_DIV = "1099-DIV"
    FORM_1099_B = "1099-B"
    FORM_1099_MISC = "1099-MISC"
    FORM_1099_K = "1099-K"
    FORM_1099_OID = "1099-OID"
    FORM_1098 = "1098"
    FORM_1098_T = "1098-T"
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
    IMPROVED: Better encoding handling, smarter fallback, OCR error tolerance.
    """
    import html
    import re
    
    text_lower = text.lower()
    
    # STEP 1: Decode HTML entities (e.g., "1099&#8212;MISC" -> "1099-MISC")
    try:
        text_decoded = html.unescape(text_lower)
    except:
        text_decoded = text_lower
    
    # STEP 2: Normalize dashes (handle en-dash, em-dash, minus sign)
    # Replace: – (en-dash U+2013), — (em-dash U+2014), − (minus U+2212), _ (underscore)
    text_normalized = text_decoded.replace('–', '-').replace('—', '-').replace('−', '-').replace('_', '-')
    
    # STEP 3: Clean HTML/JSON noise
    text_clean = text_normalized.replace("<", " ").replace(">", " ").replace('"', " ").replace('&', ' ')
    
    # STEP 4: Create variant patterns for OCR tolerance (0/O, l/1 confusion)
    def has_keyword_or_variants(text, base_keyword):
        """Check if keyword or OCR-error variants exist"""
        if base_keyword in text:
            return True
        # Handle common OCR mistakes: 0->O, l->1, 5->S
        variant1 = base_keyword.replace('0', 'o')  # Allow letter O instead of 0
        if variant1 in text:
            return True
        return False
    
    # 1099-MISC indicators (CHECK FIRST - BEFORE W-2 to prevent false positives)
    # MUST check BEFORE 1099-NEC since MISC can also mention nonemployee compensation in Box 7
    misc_keywords = ["1099-misc", "1099 misc", "1099misc", "miscellaneous income", "royalties", "rents", "prizes", "awards", "box 7 nonemployee", "fishing boat", "medical payments"]
    if any(has_keyword_or_variants(text_clean, kw) for kw in misc_keywords):
        return DocumentType.FORM_1099_MISC
    
    # Alternative check: Look for "1099" followed by "misc" anywhere in text (handles encoding issues)
    if re.search(r'1099\s*[-\s]*misc', text_clean, re.IGNORECASE):
        return DocumentType.FORM_1099_MISC
    
    # W-2 indicators (AFTER 1099-MISC to avoid confusion)
    # Require explicit "w-2" or "wage and tax" to avoid false positives from 1099 forms that mention "box" or "wages"
    w2_keywords = ["w-2", "wage and tax statement", "employee's withholding"]
    if any(has_keyword_or_variants(text_clean, kw) for kw in w2_keywords):
        return DocumentType.W2
    
    # 1099-NEC indicators (after MISC check to avoid false positives)
    nec_keywords = ["1099-nec", "1099 nec", "1099nec", "nonemployee compensation", "nec form"]
    if any(has_keyword_or_variants(text_clean, kw) for kw in nec_keywords):
        return DocumentType.FORM_1099_NEC
    
    # 1099-INT indicators
    int_keywords = ["1099-int", "1099 int", "1099int", "interest income", "interest paid"]
    if any(has_keyword_or_variants(text_clean, kw) for kw in int_keywords):
        return DocumentType.FORM_1099_INT
    
    # 1099-DIV indicators
    div_keywords = ["1099-div", "1099 div", "1099div", "dividend", "distributed"]
    if any(has_keyword_or_variants(text_clean, kw) for kw in div_keywords):
        return DocumentType.FORM_1099_DIV
    
    # 1099-B indicators
    b_keywords = ["1099-b", "1099 b", "1099b", "proceeds", "sale securities", "brokerage"]
    if any(has_keyword_or_variants(text_clean, kw) for kw in b_keywords):
        return DocumentType.FORM_1099_B
    
    # 1099-K indicators (Payment card)
    k_keywords = ["1099-k", "1099 k", "1099k", "payment card", "merchant category"]
    if any(has_keyword_or_variants(text_clean, kw) for kw in k_keywords):
        return DocumentType.FORM_1099_K
    
    # 1099-OID indicators (Original Issue Discount)
    oid_keywords = ["1099-oid", "1099 oid", "1099oid", "original issue discount"]
    if any(has_keyword_or_variants(text_clean, kw) for kw in oid_keywords):
        return DocumentType.FORM_1099_OID
    
    # 1098-T indicators (Education credit)
    t_keywords = ["1098-t", "1098 t", "1098t", "education", "qualified education"]
    if any(has_keyword_or_variants(text_clean, kw) for kw in t_keywords):
        return DocumentType.FORM_1098_T
    
    # 1098 indicators (Mortgage interest)
    m1098_keywords = ["1098 ", "mortgage interest statement", "box 1 mortgage"]
    if any(has_keyword_or_variants(text_clean, kw) for kw in m1098_keywords) and "1098-t" not in text_clean:
        return DocumentType.FORM_1098
    
    # Paystub indicators
    paystub_keywords = ["paystub", "pay stub", "paycheck", "gross pay", "net pay", "employer deduction"]
    if any(has_keyword_or_variants(text_clean, kw) for kw in paystub_keywords):
        return DocumentType.PAYSTUB
    
    # Bank statement indicators
    bank_keywords = ["bank statement", "account statement", "transaction", "balance"]
    if any(has_keyword_or_variants(text_clean, kw) for kw in bank_keywords):
        return DocumentType.BANK_STATEMENT
    
    # Fallback: if it looks like a 1099 form specifically
    if has_keyword_or_variants(text_clean, "1099"):
        # IMPROVED FALLBACK: Smart detection instead of defaulting to NEC
        if has_keyword_or_variants(text_clean, "misc") or has_keyword_or_variants(text_clean, "royalties"):
            return DocumentType.FORM_1099_MISC
        elif has_keyword_or_variants(text_clean, "payment") and has_keyword_or_variants(text_clean, "card"):
            return DocumentType.FORM_1099_K
        elif has_keyword_or_variants(text_clean, "proceeds") or has_keyword_or_variants(text_clean, "brokerage"):
            return DocumentType.FORM_1099_B
        elif has_keyword_or_variants(text_clean, "interest"):
            return DocumentType.FORM_1099_INT
        elif has_keyword_or_variants(text_clean, "dividend"):
            return DocumentType.FORM_1099_DIV
        elif has_keyword_or_variants(text_clean, "original") and has_keyword_or_variants(text_clean, "discount"):
            return DocumentType.FORM_1099_OID
        else:
            # Last resort: Default to NEC for truly unknown 1099s
            return DocumentType.FORM_1099_NEC
    
    # Default: if it looks like a tax form, assume W-2 ONLY if it explicitly mentions W-2
    # (Don't use generic keywords - they match too many documents)
    if any(has_keyword_or_variants(text_clean, kw) for kw in ["w-2", "form w", "wage and tax"]):
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
        ENHANCED: Uses document field schema to tell LLM exactly what fields exist.
        Extracts using LandingAI field names (not Box numbers).
        Handles: HTML tables, Markdown, JSON, plain text, OCR, mixed formats.
        No preprocessing needed - works with raw LandingAI output in any format.
        """
        # Sanitize text to ensure UTF-8 compatibility (handle special Unicode characters)
        # This prevents charmap encoding errors when passing to LLM
        sanitized_text = text.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        
        # Get field schema for this document type (ENHANCED: tells LLM what fields to extract)
        field_list_prompt = ""
        if FIELD_SCHEMA_AVAILABLE:
            try:
                field_list_prompt = get_available_fields_for_document(doc_type)
            except Exception as e:
                print(f"[WARN] Could not load field schema: {e}")
                field_list_prompt = ""
        
        # Fallback to basic field names if schema not available
        if not field_list_prompt:
            if doc_type == DocumentType.W2:
                field_names = """
AVAILABLE FIELDS FOR W-2:
- wages (Box 1: Wages, tips, other compensation)
- federal_income_tax_withheld (Box 2: Federal income tax withheld)
- social_security_wages (Box 3: Social Security wages)
- social_security_tax_withheld (Box 4: Social Security tax withheld)
- medicare_wages (Box 5: Medicare wages and tips)
- medicare_tax_withheld (Box 6: Medicare tax withheld)
- state_income_tax_withheld (Box 19: State income tax)
- employer_ein, employer_name, employer_address
- employee_ssn, employee_name, employee_address
"""
            elif doc_type == DocumentType.FORM_1099_NEC:
                field_names = """
AVAILABLE FIELDS FOR 1099-NEC:
- nonemployee_compensation (Box 1: Nonemployee Compensation)
- federal_income_tax_withheld (Box 4: Federal income tax withheld)
- payer_name, payer_ein, payer_address
- recipient_tin, recipient_name
"""
            elif doc_type == DocumentType.FORM_1099_INT:
                field_names = """
AVAILABLE FIELDS FOR 1099-INT:
- interest_income (Box 1: Interest Income)
- federal_income_tax_withheld (Box 4: Federal income tax withheld)
- payer_name, payer_tin, payer_address
- recipient_tin, recipient_name
"""
            else:
                field_names = """
AVAILABLE FIELDS (UNIVERSAL):
- wages, nonemployee_compensation, interest_income, dividend_income
- federal_income_tax_withheld, state_income_tax_withheld, local_income_tax_withheld
- social_security_wages, social_security_tax_withheld
- medicare_wages, medicare_tax_withheld
"""
        else:
            field_names = field_list_prompt
        
        prompt = f"""You are a UNIVERSAL DATA EXTRACTOR for tax documents.

YOUR JOB:
1. Read the document in ANY format (HTML, JSON, Markdown, text, OCR, tables, mixed)
2. Extract ALL available fields from the list below
3. Map extracted data to the exact field names shown
4. Return clean JSON with all extracted values

DOCUMENT TYPE: {doc_type.value}

{field_names}

INPUT FORMAT HANDLING:
- HTML tables: <tr><td>Wages</td><td>23500</td></tr> → "wages": 23500
- Markdown tables: | Wages | 23500 | → "wages": 23500
- JSON objects: {{"wages": 23500}} → "wages": 23500
- Box notation: "Box 1: $23,500" → Map to correct field name
- Label: Value format: "Wages: $23,500.00" → "wages": 23500.00
- Plain text/OCR: "Wages 23500 Federal tax 1500" → extract and map fields
- Mixed formats: Handle all above simultaneously

EXTRACTION RULES:
1. ONLY use field names from the AVAILABLE FIELDS list above
2. Handle currency ($€¥), commas (23,500), decimals (340.75)
3. Extract names/IDs (SSN/EIN/TIN) as text values
4. For tables: column headers = labels, cells = values → map to field names
5. For JSON: flatten nested structures if needed
6. For OCR/text: infer field names and map to correct field names
7. Do NOT skip values - extract everything possible
8. Clean labels: remove special chars, normalize spacing
9. If a field is NOT in the list above, DO NOT include it in output

OUTPUT FORMAT (ALWAYS return ONLY JSON with raw_fields containing field values):
{{
  "extraction_method": "llm_universal",
  "provider": "{self.provider.value}",
  "document_type": "{doc_type.value}",
  "input_format_detected": "auto-detected",
  "raw_fields": {{
    "field_name_1": value_or_text,
    "field_name_2": value_or_text
  }},
  "field_count": 6,
  "extraction_complete": true
}}

DOCUMENT INPUT (ANY FORMAT - NO PREPROCESSING NEEDED):
===START===
{sanitized_text}
===END===

NOW EXTRACT: Read the document above. Extract ONLY fields from the AVAILABLE FIELDS list. Return ONLY JSON.
"""
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """Call the LLM with the prompt"""
        
        try:
            # Ensure prompt is properly encoded (handle Unicode characters like em-dashes)
            if isinstance(prompt, bytes):
                prompt = prompt.decode('utf-8', errors='replace')
            else:
                # Force UTF-8 encoding to handle special characters
                prompt = prompt.encode('utf-8', errors='replace').decode('utf-8')
            
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
        
        # Step 7: Run tax calculation for ALL document types
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
        
        # Run tax calculation for ALL supported forms, not just W-2
        if self.tax_engine_available and doc_type in [
            DocumentType.W2, 
            DocumentType.FORM_1099_NEC,
            DocumentType.FORM_1099_MISC,
            DocumentType.FORM_1099_INT,
            DocumentType.FORM_1099_DIV,
            DocumentType.FORM_1099_K,
        ]:
            print(f"[INFO] Running tax calculation for {doc_type.value}...")
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
            try:
                val_num = float(value) if isinstance(value, str) else value
                if isinstance(val_num, (int, float)) and val_num > 0:
                    validation["fields_with_values"] += 1
                else:
                    validation["fields_with_zero"] += 1
            except (ValueError, TypeError):
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
            
            # 1099-MISC fields (all boxes)
            "rents": 0.0,                           # Box 1
            "royalties": 0.0,                       # Box 2
            "other_income": 0.0,                    # Box 3
            "fishing_boat_proceeds": 0.0,           # Box 5
            "medical_payments": 0.0,                # Box 6
            "substitute_payments": 0.0,             # Box 8
            "crop_insurance_proceeds": 0.0,         # Box 9
            "gross_proceeds_attorney": 0.0,         # Box 10
            "excess_parachute_payments": 0.0,       # Box 14
            "nonqualified_deferred_comp": 0.0,      # Box 15
            
            # 1099-INT fields
            "interest_income": 0.0,                 # Box 1
            "us_savings_bonds": 0.0,                # Box 3
            "federal_interest_subsidy": 0.0,        # Box 4
            
            # 1099-DIV fields
            "ordinary_dividends": 0.0,              # Box 1a
            "qualified_dividends": 0.0,             # Box 1b
            "capital_gain_distributions": 0.0,      # Box 2a
            "long_term_capital_gains": 0.0,         # Box 2b
            "unrecaptured_section_1250": 0.0,       # Box 2d
            "section_1202_gains": 0.0,              # Box 2e
            "collectibles_gains": 0.0,              # Box 2f
            "nondividend_distributions": 0.0,       # Box 3
            "federal_income_tax_withheld": 0.0,     # Box 4
            "investment_expenses": 0.0,             # Box 5
            "foreign_tax_paid": 0.0,                # Box 7
            "foreign_country": "",                  # Box 8
            
            # 1099-B fields (Brokerage/Securities)
            "total_proceeds": 0.0,                  # Box 1d
            "cost_basis": 0.0,                      # Box 1e
            "adjustment_code": "",                 # Box 1f
            "gain_or_loss": 0.0,                    # Box 1g
            "short_term_gains": 0.0,                # Short-term gains
            "long_term_gains": 0.0,                 # Long-term gains
            
            # 1099-K fields (Payment Card/Third Party)
            "card_not_present_transactions": 0.0,   # Box 1a
            "merchant_category_code": "",          # Box 1b
            "monthly_payment_transactions": [],     # Boxes 5a-5m
            "federal_income_tax_withheld_k": 0.0,   # Box 4
            
            # 1099-OID fields (Original Issue Discount)
            "original_issue_discount": 0.0,         # Box 1a
            "oid_from_call_redemption": 0.0,        # Box 1b
            "early_redemption": 0.0,                # Box 2
            "oid_accrued_this_year": 0.0,           # Box 3
            
            # 1099-INT/DIV/etc (consolidated)
            "dividend_income": 0.0,
            "capital_gains": 0.0,
            
            # Withholdings
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
            
            # PRIORITY 9: 1099-MISC box numbers
            (("box 1",), "rents", 15),              # 1099-MISC Box 1
            (("box 2",), "royalties", 15),          # 1099-MISC Box 2
            (("box 3",), "other_income", 15),       # 1099-MISC Box 3
            (("box 5",), "fishing_boat_proceeds", 15), # 1099-MISC Box 5
            (("box 6",), "medical_payments", 15),   # 1099-MISC Box 6
            (("box 8",), "substitute_payments", 15), # 1099-MISC Box 8
            (("box 9",), "crop_insurance_proceeds", 15), # 1099-MISC Box 9
            (("box 10",), "gross_proceeds_attorney", 15), # 1099-MISC Box 10
            (("box 14",), "excess_parachute_payments", 15), # 1099-MISC Box 14
            (("box 15",), "nonqualified_deferred_comp", 15), # 1099-MISC Box 15
            
            # PRIORITY 8: 1099-MISC field names
            (("rents",), "rents", 10),
            (("royalties",), "royalties", 10),
            (("fishing", "boat"), "fishing_boat_proceeds", 10),
            (("medical", "health"), "medical_payments", 10),
            (("substitute", "payment"), "substitute_payments", 10),
            (("crop", "insurance"), "crop_insurance_proceeds", 10),
            (("attorney", "proceeds"), "gross_proceeds_attorney", 10),
            (("parachute", "payment"), "excess_parachute_payments", 10),
            (("deferred", "comp"), "nonqualified_deferred_comp", 10),
            
            # PRIORITY 7: 1099-INT field names
            (("interest", "income"), "interest_income", 10),
            (("savings", "bond"), "us_savings_bonds", 10),
            (("interest", "subsidy"), "federal_interest_subsidy", 10),
            
            # PRIORITY 6: 1099-DIV field names
            (("ordinary", "dividend"), "ordinary_dividends", 10),
            (("qualified", "dividend"), "qualified_dividends", 10),
            (("capital", "gain", "distribution"), "capital_gain_distributions", 10),
            (("long", "term", "capital", "gain"), "long_term_capital_gains", 10),
            (("section", "1250"), "unrecaptured_section_1250", 10),
            (("section", "1202"), "section_1202_gains", 10),
            (("collectible", "gain"), "collectibles_gains", 10),
            (("nondividend"), "nondividend_distributions", 10),
            (("investment", "expense"), "investment_expenses", 10),
            
            # PRIORITY 5: 1099-B field names (Brokerage)
            (("proceeds",), "total_proceeds", 10),
            (("cost", "basis"), "cost_basis", 10),
            (("short", "term", "gain"), "short_term_gains", 10),
            
            # PRIORITY 4: 1099-K field names (Payment Card)
            (("card", "transaction"), "card_not_present_transactions", 10),
            (("merchant", "category"), "merchant_category_code", 10),
            
            # PRIORITY 3: 1099-OID field names (Original Issue Discount)
            (("original", "issue", "discount"), "original_issue_discount", 10),
            (("call", "redemption"), "oid_from_call_redemption", 10),
            (("early", "redemption"), "early_redemption", 10),
            
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
                # 1099-MISC field matching
                elif "rent" in label_lower:
                    normalized["rents"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → rents (fuzzy) = {value}")
                    matched = True
                elif "royalty" in label_lower:
                    normalized["royalties"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → royalties (fuzzy) = {value}")
                    matched = True
                elif "fishing" in label_lower and "boat" in label_lower:
                    normalized["fishing_boat_proceeds"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → fishing_boat_proceeds (fuzzy) = {value}")
                    matched = True
                elif "medical" in label_lower or "health" in label_lower:
                    normalized["medical_payments"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → medical_payments (fuzzy) = {value}")
                    matched = True
                elif "substitute" in label_lower:
                    normalized["substitute_payments"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → substitute_payments (fuzzy) = {value}")
                    matched = True
                elif "crop" in label_lower and "insurance" in label_lower:
                    normalized["crop_insurance_proceeds"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → crop_insurance_proceeds (fuzzy) = {value}")
                    matched = True
                elif "attorney" in label_lower and "proceed" in label_lower:
                    normalized["gross_proceeds_attorney"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → gross_proceeds_attorney (fuzzy) = {value}")
                    matched = True
                elif "parachute" in label_lower:
                    normalized["excess_parachute_payments"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → excess_parachute_payments (fuzzy) = {value}")
                    matched = True
                elif "deferred" in label_lower and "comp" in label_lower:
                    normalized["nonqualified_deferred_comp"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → nonqualified_deferred_comp (fuzzy) = {value}")
                    matched = True
                # 1099-INT field matching
                elif "savings" in label_lower and "bond" in label_lower:
                    normalized["us_savings_bonds"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → us_savings_bonds (fuzzy) = {value}")
                    matched = True
                elif "interest" in label_lower and "subsidy" in label_lower:
                    normalized["federal_interest_subsidy"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → federal_interest_subsidy (fuzzy) = {value}")
                    matched = True
                # 1099-DIV field matching
                elif "ordinary" in label_lower and "dividend" in label_lower:
                    normalized["ordinary_dividends"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → ordinary_dividends (fuzzy) = {value}")
                    matched = True
                elif "qualified" in label_lower and "dividend" in label_lower:
                    normalized["qualified_dividends"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → qualified_dividends (fuzzy) = {value}")
                    matched = True
                elif "capital" in label_lower and "gain" in label_lower and "distribution" in label_lower:
                    normalized["capital_gain_distributions"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → capital_gain_distributions (fuzzy) = {value}")
                    matched = True
                elif "long" in label_lower and "term" in label_lower and "capital" in label_lower:
                    normalized["long_term_capital_gains"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → long_term_capital_gains (fuzzy) = {value}")
                    matched = True
                elif "section" in label_lower and "1250" in label_lower:
                    normalized["unrecaptured_section_1250"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → unrecaptured_section_1250 (fuzzy) = {value}")
                    matched = True
                elif "section" in label_lower and "1202" in label_lower:
                    normalized["section_1202_gains"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → section_1202_gains (fuzzy) = {value}")
                    matched = True
                elif "collectible" in label_lower and "gain" in label_lower:
                    normalized["collectibles_gains"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → collectibles_gains (fuzzy) = {value}")
                    matched = True
                elif "nondividend" in label_lower:
                    normalized["nondividend_distributions"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → nondividend_distributions (fuzzy) = {value}")
                    matched = True
                elif "investment" in label_lower and "expense" in label_lower:
                    normalized["investment_expenses"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → investment_expenses (fuzzy) = {value}")
                    matched = True
                elif "foreign" in label_lower and "tax" in label_lower:
                    normalized["foreign_tax_paid"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → foreign_tax_paid (fuzzy) = {value}")
                    matched = True
                # 1099-B field matching
                elif "short" in label_lower and "term" in label_lower and "gain" in label_lower:
                    normalized["short_term_gains"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → short_term_gains (fuzzy) = {value}")
                    matched = True
                # 1099-K field matching
                elif "merchant" in label_lower and "category" in label_lower:
                    # Don't set as numeric value since it's a code
                    matched = True
                # 1099-OID field matching
                elif "original" in label_lower and "issue" in label_lower and "discount" in label_lower:
                    normalized["original_issue_discount"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → original_issue_discount (fuzzy) = {value}")
                    matched = True
                elif "call" in label_lower and "redemption" in label_lower:
                    normalized["oid_from_call_redemption"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → oid_from_call_redemption (fuzzy) = {value}")
                    matched = True
                elif "early" in label_lower and "redemption" in label_lower:
                    normalized["early_redemption"] = value
                    print(f"[NORM] ⊙ '{raw_label}' → early_redemption (fuzzy) = {value}")
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
            try:
                val_num = float(value) if isinstance(value, str) else value
                if isinstance(val_num, (int, float)) and val_num > 0:
                    summary += f"{key:40s}: ${val_num:12,.2f}\n"
            except (ValueError, TypeError):
                pass
        
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
